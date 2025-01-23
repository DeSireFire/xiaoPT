#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2025/1/22
# CreatTIME : 10:21
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'

from datetime import datetime
from pathlib import Path
import re
import traceback
from typing import List
import uuid
import qbittorrentapi
import requests
from pydantic import BaseModel

# 种子模组
"""
便于日后不同下载器，其种子模组对象打通
"""


class torrentDB(BaseModel):
    site: str
    name: str
    torrent_id: str
    completed: bool = False  # 是否下载完成
    free_end_time: datetime
    upspeed: int  # 上传速度 字节
    up_total_size: int
    dl_total_size: int
    dlspeed: int
    hash: str = ""
    size: int = 0


class torrentStatus(BaseModel):
    dl_total_size: int
    up_total_size: int
    upspeed: int
    dlspeed: int
    free_space_size: int
