#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2025/1/22
# CreatTIME : 10:33
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'

# 预载对象
import os

from config.config import *
from torrenter.qbittorrent import QBittorrent

from crawler.mteam import mteamCrawler


qb_client = QBittorrent(qb_url=qb.qb_url, username=qb.user, password=qb.pwd)
mtc = mteamCrawler(cookie={}, headers=mteam.headers)

