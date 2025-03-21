#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2025/1/17
# CreatTIME : 10:40
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'

import os
import time
import copy
from pprint import pprint

import jsonpath
import requests
from datetime import datetime, timedelta
from crawler import BaseSiteSpider
from config.config import mteam, root_path


# api.m-team.cc/api/torrent/genDlToken
class mteamCrawler(BaseSiteSpider):
    NAME = "M-Team"
    HOST = "api.m-team.cc"
    SEARCH_API = "api/torrent/search"
    TORRENT_API = "api/torrent/genDlToken"
    PAGE_SIZE = 200
    BODYS = [
        # 电影最新
        {
            "categories": [],
            "mode": "movie",
            "visible": 1,
            "pageNumber": 1,
            "pageSize": PAGE_SIZE,
            "sortDirection": "DESC",
            "sortField": "CREATED_DATE",
        },
        # 成人最新
        {
            "categories": [],
            "mode": "adult",
            "visible": 1,
            "pageNumber": 1,
            "pageSize": PAGE_SIZE,
            "sortDirection": "DESC",
            "sortField": "CREATED_DATE",
        },
        # 电视最新
        {
            "categories": [],
            "mode": "tvshow",
            "visible": 1,
            "pageNumber": 1,
            "pageSize": PAGE_SIZE,
            "sortDirection": "DESC",
            "sortField": "CREATED_DATE",
        },
        # 综合最新
        {
            "categories": [],
            "mode": "normal",
            "visible": 1,
            "pageNumber": 1,
            "pageSize": PAGE_SIZE,
            "sortDirection": "DESC",
            "sortField": "CREATED_DATE",
        },
        # 排行榜 下载数最多
        {
            "categories": [],
            "mode": "rankings",
            "visible": 1,
            "pageNumber": 1,
            "pageSize": PAGE_SIZE,
            "sortDirection": "DESC",
            "sortField": "LEECHERS",
        },
        # 馒头官种 动漫列表 文件大小从小到大排序
        {
            'mode': 'normal',
            'categories': [
                '405',
                '434',
            ],
            'teams': [
                '44',
                '9',
                '43',
            ],
            'discount': 'FREE',
            'visible': 1,
            'sortDirection': 'ASC',
            'sortField': 'SIZE',
            'pageNumber': 1,
            'pageSize': 100,
        },
        # 馒头官种 文件大小从小到大排序
        {
            'mode': 'normal',
            'categories': [],
            'teams': [
                '44',
                '9',
                '43',
            ],
            'discount': 'FREE',
            'visible': 1,
            'sortDirection': 'ASC',
            'sortField': 'SIZE',
            'pageNumber': 1,
            'pageSize': 100,
        }
    ]
    base_headers = mteam.headers

    def torrent_rawlist_crawler(self):
        """
        获取目标网站的列表
        :return:
        """
        headers = copy.deepcopy(self.base_headers)
        headers['ts'] = f'{int(time.time())}'

        # json_data = {
        #     'mode': 'normal',
        #     'categories': [
        #         '405',
        #     ],
        #     'visible': 1,
        #     'pageNumber': 1,
        #     'pageSize': 100,
        # }
        json_data = self.BODYS[-1]

        response = self.fetch(
            method="POST",
            url=f"https://{self.HOST}/{self.SEARCH_API}",
            headers=headers, json=json_data
        )

        return response.json()

    def rawlist_cleaner(self, raw_list):
        """
        列表清洗器
        :return:
        """
        data = raw_list.get("data", {}).get("data", {})
        free_data = []
        for d in data:
            # toppingLevel = d["status"]["toppingLevel"]
            # size = d["size"] or 0
            # size_GB = int(size) / (1024**3)
            # if size_GB and 0 < size_GB < 10 and self._is_free_torrent(d):
            #     free_data.append(d)
            if self._rawlist_filter(d):
                free_data.append(d)
            else:
                # print(f"no free: {d['smallDescr']}")
                continue
        return free_data

    def _rawlist_filter(self, d):

        size = d["size"] or 0
        # 筛选大小， 单位 GB
        size_GB = int(size) / (1024 ** 3)
        size_MB = int(size) / (1024 ** 2)
        status = d.get("status")
        try:
            if any([
                size,  # 是否存在大小
                status,  # 是否存在大小
                # 0 < size_GB < 10,  # 大小小于10GB
                10 < size_MB < 2048,  # 大小小于2048M
                self._is_free_torrent(d),  # 是否为免费资源
                # self.is_seeders_greater_than_leechers(status["seeders"], status["leechers"], 1),  # 做种>下载3倍的不要
                # todo mallSingleFree为None的资源中有免费资源，判断方式待定
                # self.is_end_date_within_10_hours(status.get('mallSingleFree', {}).get('endDate')),  # 免费时长不到10小时跳过

            ]):
                return True
            else:
                return False
        except Exception as e:
            return False

    def is_seeders_greater_than_leechers(self, seeders, leechers, threshold=2):
        """
        判断seeders是否远大于leechers。

        :param seeders: 种子用户数量
        :param leechers: 下载用户数量
        :param threshold: 阈值，表示seeders数量需要超过leechers数量的倍数
        :return: 如果seeders远大于leechers，则返回True，否则返回False
        """
        if 0 < int(seeders) < 10:
            return True

        if int(leechers) == 0:  # 避免除以零的错误
            return True if 0 < int(seeders) < 3 else False
        # print(int(seeders) / int(leechers))
        return int(seeders) / int(leechers) <= int(threshold)

    def is_end_date_within_10_hours(self, end_date_str):
        """
        判断提供的结束日期是否距离现在不到10个小时。

        :param end_date_str: 结束日期的字符串表示，格式应为 "YYYY-MM-DD HH:MM:SS"
        :return: 如果结束日期距离现在不到10个小时，则返回False，否则返回True
        """
        if not end_date_str:
            return False
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
        current_date = datetime.now()
        time_difference = end_date - current_date
        return time_difference > timedelta(hours=10)

    def get_torrent_link(self, torrent_id: str) -> str:
        """
        获取种子下载链接
        """
        headers = copy.deepcopy(self.base_headers)
        headers['ts'] = f'{int(time.time())}'
        # headers['content-type'] = 'application/json'
        files = {
            'id': (None, f'{torrent_id}'),
        }
        url = f'https://{self.HOST}/{self.TORRENT_API}'
        response1 = requests.post(url=url, headers=headers, files=files)

        torrent_url = response1.json().get("data")
        # useHttps=true&type=copy&sign=
        torrent_url = torrent_url.replace("sign=", "useHttps=true&type=copy&sign=")
        return torrent_url

    def download_torrent_file(self, torrent_id: str) -> str:
        """
        获取种子下载链接并下载文件
        """
        headers = copy.deepcopy(self.base_headers)
        headers['ts'] = f'{int(time.time())}'
        # headers['content-type'] = 'application/json'
        files = {
            'id': (None, f'{torrent_id}'),
        }
        url = f'https://{self.HOST}/{self.TORRENT_API}'
        response1 = requests.post(url=url, headers=headers, files=files)

        torrent_url = response1.json().get("data")
        # useHttps=true&type=copy&sign=
        torrent_url = torrent_url.replace("sign=", "useHttps=true&type=copy&sign=")

        try:
            # 下载文件
            response2 = requests.get(torrent_url, stream=True)
            response2.raise_for_status()

            # 生成文件名
            file_name = f'{torrent_id}.torrent'

            # 保存文件
            with open(file_name, 'wb') as file:
                for chunk in response2.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)

            print(f"文件已成功下载并保存为 {file_name}")
            return file_name
        except requests.RequestException as e:
            print(f"下载文件时出现错误: {e}")
            return None

    def _is_free_torrent(self, item: dict) -> bool:
        """
        满足以下任意即为free,规则如下：
        1. discount = FREE or _2X_FREE
        2. mallSingleFree.status = ONGOING
        """
        discounts = jsonpath.jsonpath(item, "$.status.discount")

        mall_single_free_statuss = jsonpath.jsonpath(
            item, "$.status.mallSingleFree.status")

        if discounts and discounts[0] in ["FREE", "_2X_FREE"]:
            return True
        if mall_single_free_statuss and mall_single_free_statuss[0] == "ONGOING":
            return True
        return False

    def remove_duplicates_torrent_jobs(self, input_hashes, directory):
        """
        筛选出入参列表中，文本列表里所没有的hash。

        :param input_hashes: 包含多个hash值的列表。
        :param directory: 包含文本文件的目录路径。
        :return: 包含在入参列表中但不在文本文件中的hash列表。
        """
        # 读取目录下所有文本文件中的hash值
        file_hashes = set()
        file_path = os.path.join(root_path, "data", directory, 'hashes.txt')  # 假设所有的hash值都存储在一个文件中
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                for line in file:
                    # 假设每行是一个hash值，去除空格和换行符
                    hash_value = line.strip()
                    if hash_value:
                        file_hashes.add(hash_value)

        # 筛选出入参列表中不在文件列表里的hash
        missing_hashes = [hash_value for hash_value in input_hashes if hash_value not in file_hashes]

        # 将缺失的hash值添加到文本文件中
        with open(file_path, 'a') as file:
            for hash_value in missing_hashes:
                file.write(hash_value + '\n')

        return missing_hashes

    def search_torrent(self, keyword):
        """
        关键词搜索
        :param keyword:
        :return:
        """
        headers = copy.deepcopy(self.base_headers)
        headers['ts'] = f'{int(time.time())}'

        json_data = {
            'mode': 'normal',
            'categories': [],
            'visible': 1,
            'keyword': f'{keyword}',
            'pageNumber': 1,
            'pageSize': 100,
        }

        response = self.fetch(
            method="POST",
            url=f"https://{self.HOST}/{self.SEARCH_API}",
            headers=headers, json=json_data
        )

        return response.json()

    def simplify_data(self, data):
        """
        简化种子信息
        提取id，name,  smallDescr,  size(转为GB),是否为free.
        :param data:
        :return:
        """
        new_data = []
        for item in data['data']['data']:
            new_item = {
                'id': item['id'],
                'name': item['name'],
                'smallDescr': item['smallDescr'],
                'size_GB': round(int(item['size']) / (1024 * 1024 * 1024), 2),
                'is_free': item['status']['promotionRule']['discount'] == 'FREE',
                'free_endTime': item['status']['promotionRule']['endTime']
            }
            new_data.append(new_item)
        return new_data

    def filter_collection(self, data):
        """
        合集过滤
        :param data:
        :return:
        """
        # 或含
        keys = ["内封", "内嵌", "内", "嵌", "1-12"]
        # 必含
        keys2_1 = ["全", "中"]
        keys2_2 = ["1080"]
        # 排除
        keys3 = ["265"]
        res_list = []
        for d in data:
            if any([True if i in d.get("smallDescr") else False for i in keys]) \
                    and all([True if i in d.get('smallDescr') else False for i in keys2_1]) \
                    and all([True if i in d.get("name") else False for i in keys2_2]):
                # 未设置排除直接添加
                if not keys3:
                    res_list.append(d)
                    continue
                if keys3 and not any([True if i in d.get("smallDescr") else False for i in keys3]):
                    res_list.append(d)
                else:
                    # 存在需要排除的关键字则跳过
                    continue
            else:
                pass

        # 文件大小排除逻辑
        res_list = [i for i in res_list if 0 < i.get('size_GB', 0) <= 20]

        return res_list

    def crawler(self, ):
        """
        采集组件主程
        :return:
        """
        # 获取原始数据
        raw_list = self.torrent_rawlist_crawler() or {}
        if not raw_list:
            return
        # 筛选
        clear_list = self.rawlist_cleaner(raw_list)
        # pprint(clear_list)
        # 获取id
        rtids = [c["status"]["id"] for c in clear_list]
        # 去重，剔除已经添加过的种子
        tids = self.remove_duplicates_torrent_jobs(rtids, "")

        # 获取真实下载链接
        turls = []
        for i in tids:
            # pprint(clear_list[0])
            torrent_url = self.get_torrent_link(torrent_id=i)
            if torrent_url:
                turls.append(torrent_url)
        print(f"本次获取新增种子任务{len(turls)}个")
        return turls


if __name__ == '__main__':
    obj = mteamCrawler(cookie={}, headers=[])
    turls = obj.crawler()
    # print(root_path)

    # t = obj.is_seeders_greater_than_leechers(164, 38, 2)
    # print(t)


    # 批量下载BT
    # riman_list = [
    #     # 新作
    #     # "《轮回七次的反派大小姐，在前敌国享受随心所欲的新婚生活》",
    #     "《事与愿违的不死冒险者》",
    #     "《最弱的驯养师开启的捡垃圾的旅途》",
    #     "《秒杀外挂太强了，异世界的家伙们根本就不是对手》",
    #     "《恶役千金LV99～我是隐藏BOSS但不是魔王～》",
    #     "《最强肉盾的迷宫攻略》",
    #     "《魔女与野兽》",
    #     "《北海道辣妹贼拉可爱》",
    #     "《魔都精兵的奴隶》",
    #     "《婚戒物语》",
    #     "《我独自升级》",
    #     "《公主大人，接下来是“拷问”时间》",
    #     "《战国妖狐 救世姐弟篇》",
    #     "《憧憬成为魔法少女》",
    #     "《金属口红》",
    #     "《胆大党》",
    #     "《少女乐队的呐喊》",
    #     "《失忆投捕》",
    #     "《恶魔的破坏》",
    #     "《义妹生活》",
    #     "《擅长逃跑的殿下》",
    #     "《杀手寓言》",
    #     "《地：关于地球的运动》",
    #     "《村井之恋》",
    #     "《青之箱》",
    #     "《悲喜渔生》",
    #     # 续作
    #     # "《我心里危险的东西 第二季》",
    #     # "《王者天下 第五季》",
    #     # "《超自然武装当哒当》",
    #     # "《葬送的芙莉莲》",
    #     # "《鬼灭之刃 柱训练篇》",
    #     # "《我推的孩子 第二季》",
    #     # "《好想告诉你》",
    #     # "《败犬女主太多了》",
    #     # "《夏目友人帐 第七季》",
    #     # "《物语系列 外传季&怪物季》",
    #     # "《乱马1/2》",
    #     # "《Vivy - fluorite eye's song -》",
    #     # "《无职转生》",
    #     # "《Re:Zero》第三季",
    #     # "《黑执事》",
    #     # "《青之驱魔师》",
    #     # "《Frieren: beyond journey’s end》",
    #     # "《我的英雄学院》第7季",
    #     # "《忍者神龟》"
    # ]
    #     riman_list = [
    # "休假的坏人先生",
    # "爱犬讯号 (DOG SIGNAL)",
    # "为了在异世界也能抚摸毛茸茸而努力",
    # "北海道辣妹贼拉可爱",
    # "愚蠢天使与恶魔共舞",
    # "反派千金等级 99 我是隐藏头目但不是魔王",
    # "外科医生爱丽丝 (女王的手术刀)",
    # "异修罗",
    # "战国妖狐",
    # "梦想成为魔法少女 (憧憬成为魔法少女)",
    # "如果 30 岁还是处男似乎就能成为魔法师",
    # "金属口红 (METALLIC ROUGE)",
    # "迷宫饭",
    # "魔都精兵的奴隶",
    # "勇气爆发 BANG BRAVERN",
    # "名汤「异世界温泉」开拓记",
    # "秒杀外挂太强了异世界的家伙们根本就不是对手",
    # "月刊妄想科学",
    # "魔女与野兽",
    # "宝可梦地平线",
    # "葬送的芙莉莲",
    # "佐佐木与文鸟小哔",
    # "超普通县千叶传说",
    # "事与愿违的不死冒险者 (非自愿的不死冒险者)",
    # "最弱魔物使开始了捡垃圾之旅",
    # "治愈魔法的错误使用方法",
    # "百千家的妖怪王子",
    # "小酒馆 Basue",
    # "不死不运 (不死不幸) 碰之道",
    # "特搜组大吾救国的橘色部队",
    # "卡片战斗先导者 DivineZ",
    # "我独自升级",
    # "婚戒物语",
    # "指尖相触恋恋不舍",
    # "绽裂？！(天方本气谭 / BUCCHIGIRI?!)",
    # "狩龙人拉格纳",
    # "药屋少女的呢喃",
    # "最强肉盾的迷宫攻略",
    # "Wonderful 光之美少女",
    # "逃走中 GREAT MISSION",
    # "明治击剑 - 1874-",
    # "挣扎吧亚当君",
    # "大欺诈师 razbliuto",
    # "怪物一百三情飞龙侍极"
    # ]
    # riman_list = ["终末列车前往何方?"]
    #
    # NoneRes = []
    # for kw in riman_list:
    #     Rj = obj.search_torrent(kw.strip("《》"))
    #     Sj = obj.simplify_data(Rj)
    #     wait_downloads = obj.filter_collection(Sj)
    #     if not wait_downloads:
    #         NoneRes.append(kw)
    #         print(f"'{kw}', 无可用资源...")
    #     else:
    #         tid = wait_downloads[0].get("id") or None
    #         if tid:
    #             obj.download_torrent_file(tid)
    #
    # print(f"没有筛选到可用资源的关键词："
    #       f"{NoneRes}")