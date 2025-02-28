#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2025/1/22
# CreatTIME : 10:38
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'

import os
import shutil

from handlers import qb_client, jobs_clean_torrent
from datetime import datetime, timedelta


def get_torrents_with_no_upload_in_24_hours():
    """
    获取24小时内没有上传流量的种子列表。

    参数:
    qb_host: qbittorrent服务器的地址，默认为'localhost'
    qb_port: qbittorrent服务器的端口，默认为8080
    qb_username: qbittorrent服务器的用户名，默认为'admin'
    qb_password: qbittorrent服务器的密码，默认为'admin'

    返回:
    torrents_with_no_upload: 一个包含没有上传流量的种子的列表
    """
    # 获取qbittorrent客户端实例
    if qb_client.check_client_status():
        qb = qb_client.qb
    else:
        qb_client.retries_to_client()
        qb = qb_client.qb

    # 获取当前时间
    current_time = datetime.now()

    # 获取24小时前的时间
    time_24_hours_ago = current_time - timedelta(hours=24)

    # 获取所有种子的信息
    torrents = qb.torrents_info()

    # 查找24小时内没有上传流量的种子
    torrents_with_no_upload = []
    for torrent in torrents:
        # 上下传还有速度就pass
        if torrent.upspeed != 0 or torrent.dlspeed != 0:
            continue

        # 检查种子是否在下载或做种状态，并且上传速度为0，且最后活动时间早于24小时前
        if torrent.state not in ['paused'] and torrent.upspeed == 0:
            print(f"Torrent Name: {torrent['name']}, Hash: {torrent['hash']}, state: {torrent.state}")
            last_activity = datetime.fromtimestamp(torrent.last_activity)
            if last_activity < time_24_hours_ago:
                torrents_with_no_upload.append(torrent)

    # 退出登录
    qb.auth_log_out()

    return torrents_with_no_upload


def clean_torrent(delete_incomplete=True):
    """
    清理种子主程
    :return:
    """
    print("即将执行种子清理操作...")
    if not jobs_clean_torrent:
        print("当前已关闭种子清理任务，不执行清理操作...")
        return

    # 获取需要清理种子
    wait_clean_torrents = get_torrents_with_no_upload_in_24_hours() or []

    # 迁移需要保存的文件
    for wc_torrent in wait_clean_torrents:
        tmp = dict(wc_torrent)
        torrent_name = wc_torrent.get("name")
        torrent_hash = wc_torrent.get("hash")
        if tmp.get("size") == tmp.get("completed") \
                or tmp.get("total_size") == tmp.get("completed") or tmp.get("size") < 1024:
            if delete_incomplete:
                # 删除种子及其文件
                qb_client.delete_torrent(torrent_hash=torrent_hash)
                print(f"种子 {torrent_name} hash:{torrent_hash} 及其文件已被删除。")
            else:
                print(f"种子 {torrent_name} hash:{torrent_hash} 保持不变。")



if __name__ == '__main__':
    # 使用函数并打印结果
    # torrents_no_upload = get_torrents_with_no_upload_in_24_hours()
    # for torrent in torrents_no_upload:
        # print(f"Torrent Name: {torrent['name']}, Hash: {torrent['hash']}")

    clean_torrent()
