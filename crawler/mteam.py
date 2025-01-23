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

from crawler import BaseSiteSpider
from config.config import mteam, root_path


class mteamCrawler(BaseSiteSpider):
    NAME = "M-Team"
    HOST = "api.m-team.cc"
    API = "api/torrent/search"
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
    ]
    base_headers = mteam.headers

    def torrent_rawlist_crawler(self):
        """
        获取目标网站的列表
        :return:
        """
        headers = copy.deepcopy(self.base_headers)
        headers['ts'] = f'{int(time.time())}'

        json_data = {
            'mode': 'normal',
            'categories': [
                '405',
            ],
            'visible': 1,
            'pageNumber': 1,
            'pageSize': 100,
        }

        response = self.fetch(
            method="POST",
            url=f"https://{self.HOST}/{self.API}",
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
            # mallSingleFree = d["status"]["mallSingleFree"]
            # if mallSingleFree:
            #     free_data.append(d)
            toppingLevel = d["status"]["toppingLevel"]
            size = d["size"] or 0
            size_GB = int(size) / (1024**3)
            if size_GB and 0 < size_GB < 10 and self._is_free_torrent(d):
                free_data.append(d)
            else:
                print(f"no free: {d['smallDescr']}")
                continue




        return free_data

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
        url = f'https://api.m-team.cc/{self.TORRENT_API}'
        response1 = requests.post(url=url, headers=headers, files=files)

        torrent_url = response1.json().get("data")
        # useHttps=true&type=copy&sign=
        torrent_url = torrent_url.replace("sign=", "useHttps=true&type=copy&sign=")
        return torrent_url

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

    def crawler(self, ):
        """
        采集组件主程
        :return:
        """
        # 获取原始数据
        raw_list = self.torrent_rawlist_crawler() or {}
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