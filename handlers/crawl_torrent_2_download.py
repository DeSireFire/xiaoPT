#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2025/1/22
# CreatTIME : 10:39
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'
# 获取新的种子任务
from handlers import mtc, qb_client

def add_torrent_jobs():
    """
    获取新一批种子任务
    :return:
    """

    # 馒头
    turls = mtc.crawler()
    if not turls:
        return
    callback_res = qb_client.qb.torrents_add(
        urls="\r\n".join(turls),
        category="xiaoPT",
        use_auto_torrent_management=True,
    )
    print(f"种子任务添加：{callback_res}")



if __name__ == '__main__':
    add_torrent_jobs()