#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2025/1/20
# CreatTIME : 14:29
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'
import time
from pydantic import BaseModel, Field


class mteam(BaseModel):
    headers: dict
    cookies: str


class qb(BaseModel):
    qb_url: str
    user: str
    pwd: str