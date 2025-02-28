#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2025/1/23
# CreatTIME : 11:08
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'

from datetime import datetime, timedelta
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import tasks as tasks


def main():
    executors = {"default": ThreadPoolExecutor(max_workers=6)}
    job_defaults = {"coalesce": True, "max_instances": 1}
    scheduler = BlockingScheduler(
        executors=executors, job_defaults=job_defaults)
    # 新增种子任务
    scheduler.add_job(tasks.add_torrent_jobs, "interval", minutes=15, next_run_time=datetime.now() + timedelta(seconds=10))
    # 清理种子任务（不需要就注释）
    scheduler.add_job(tasks.clean_torrent, "interval", hours=1, next_run_time=datetime.now() + timedelta(seconds=10))
    print(f"开始运行，稍后你可以在日志文件中查看日志，观察运行情况...")
    scheduler.start()


if __name__ == "__main__":
    main()