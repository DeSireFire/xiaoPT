#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2025/1/20
# CreatTIME : 15:20
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'

import os

import requests
from qbittorrentapi import Client
from datetime import datetime, timedelta
from time import sleep
from mode.torrent_mode import *
from qbittorrentapi import Client
from qbittorrentapi.exceptions import APIError


class QBittorrent:

    def close(self):
        self.qb.auth_log_out()

    def __init__(self, qb_url: str, username: str, password: str):
        self.qb_url = qb_url
        self.username = username
        self.password = password
        self.qb = qbittorrentapi.Client(
            host=self.qb_url, username=self.username, password=self.password
        )
        self.qb.auth_log_in()

        # 受此项目管理的种子所带有的分类名
        self.category = "xiaoPT"
        self._create_category(self.category)

    @property
    def status(self) -> torrentStatus:
        result = self.qb.sync_maindata().server_state

        return torrentStatus(
            dl_total_size=result.alltime_dl,
            up_total_size=result.alltime_ul,
            free_space_size=result.free_space_on_disk,
            upspeed=result.up_info_speed,
            dlspeed=result.dl_info_speed
        )

    @property
    def torrents(self) -> List[torrentDB]:
        # return []
        result = []
        for i in self.qb.torrents_info(category=self.category).data:
            torrent_name = i.get('name')
            site, torrent_id, end_time = re.search(
                r'__meta\.(.*?)\.(\d+)\.endTime\.(.*)', torrent_name).groups()
            end_time = datetime.strptime(end_time, "%Y-%m-%d-%H:%M:%S")
            up_total_size = i.get('uploaded') if i.get('uploaded') else 0
            upspeed = i.get('upspeed') if i.get('upspeed') else 0
            dl_total_size = i.get('downloaded') if i.get('downloaded') else 0
            dlspeed = i.get('dlspeed') if i.get('dlspeed') else 0
            completed = i.get('completion_on') > 0
            torrent_hash = i.get('hash')
            size = i.get('size', 0)
            result.append(torrentDB(
                hash=torrent_hash,
                name=torrent_name,
                site=site,
                torrent_id=torrent_id,
                upspeed=upspeed,
                up_total_size=up_total_size,
                dl_total_size=dl_total_size,
                dlspeed=dlspeed,
                free_end_time=end_time,
                completed=completed,
                size=size
            ))
        return result

    def _create_category(self, category):
        """
        编辑分类的保存路径, 分类不存在时则会创建
        :param category:
        :param save_path:
        :return:
        """
        try:
            save_path = str(Path(self.qb.app_default_save_path()) / "_xiaoPT")
            self.qb.torrents_create_category(name=category, save_path=save_path)
        except qbittorrentapi.exceptions.Conflict409Error:
            # 已经存在
            pass
        # try:
        #     self.qb.torrents_edit_category(name=category, save_path=save_path)
        # except qbittorrentapi.exceptions.Conflict409Error:
        #     # 路径冲突或不可访问
        #     pass
        # return None

    def download_torrent_url(
            self,
            torrent_url: str,
            torrent_name: str,
    ) -> bool:
        torrent_download_res = requests.get(torrent_url, timeout=30, verify=False)
        res = self.qb.torrents_add(
            torrent_files=torrent_download_res.content,
            category=self.category,
            rename=torrent_name,
            use_auto_torrent_management=True,
        )
        return res == "Ok."

    def delete_torrent(self, torrent_hash: str):
        self.qb.torrents_delete(delete_files=True, torrent_hashes=[torrent_hash])

    def cancel_download(self, torrent_hash: str):
        """
        根据种子hash值，取消种子下载，但已下载的文件继续做种
        """
        files = self.get_torrent_files(torrent_hash)
        file_ids = [file['index'] for file in files]
        self.set_no_download_files(torrent_hash, file_ids)
        # self.qb.torrents_delete(delete_files=True, torrent_hashes=[torrent_hash])

    def get_torrent_files(self, hash: str) -> List[dict]:
        """
        检索单个种子的所有文件
        """
        files = self.qb.torrents_files(torrent_hash=hash) or []
        return files

    def set_no_download_files(self, hash: str, file_ids: List[int]) -> bool:
        """
        设置种子的某个文件不下载
        """
        self.qb.torrents_file_priority(hash, file_ids=file_ids, priority=0)
        return True

    def check_client_status(self):
        """
        检测登录态是否正常

        # 检查客户端状态
        qb.client_status = check_client_status()
        print(f"客户端状态正常: {client_status}")

        :return:
        """
        qb = self.qb

        try:
            # 尝试登录
            qb.auth_log_in()
            print("登录成功。")

            # 尝试获取应用版本
            app_version = qb.app_version()
            print(f"qbittorrent版本: {app_version}")

            # 尝试同步主数据
            qb.sync_maindata()
            print("主数据同步成功。")

            # 如果以上步骤都没有抛出异常，则认为客户端状态正常
            return True
        except APIError as e:
            # 如果捕获到异常，打印错误信息
            print(f"qbittorrent API异常: {e}")
            return False
        except Exception as e:
            # 捕获到其他异常
            print(f"发生异常: {e}")
            return False

    def get_completed_torrent(self, torrent_hash: str):
        """
        检测指定hash种子状态是否为完成.
        只支持单个hash查询
        有值则为真，无为假
        :param hash: str
        :return:
        """
        torrent = self.qb.torrents_info(status_filter='completed', torrent_hashes=torrent_hash)
        if not torrent:
            print(f"未找到哈希值为 {torrent_hash} 的种子。")
            return None
        else:
            return torrent[0]

    def retries_to_client(self):
        self.close()
        self.__init__(self.qb_url, self.username, self.password)


if __name__ == '__main__':
    pass
