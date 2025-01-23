#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2025/1/17
# CreatTIME : 11:27
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'
import abc
from typing import Any, Generator, List, Optional
from curl_cffi import requests
from curl_cffi.requests import HttpMethod, CookieTypes


class BaseSiteSpider:

    def __init__(self, cookie: Optional[CookieTypes], headers: dict = {}):
        self.cookie = cookie
        # self.headers = headers
        self.headers = {
            "accept": "*/*",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        }
        self.headers.update(headers)

    def fetch(self, **kwargs) -> requests.Response:
        for i in range(3):
            try:
                response = requests.request(
                    **kwargs
                )
                return response
            except Exception as e:
                print(f"{e}")
        raise Exception("fetch failed")

    @abc.abstractmethod
    def free_torrents(self):
        pass

    @abc.abstractmethod
    def parse_torrent_link(self, torrent_id: str) -> str:
        pass
