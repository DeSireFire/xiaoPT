#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author    : RaXianch
# CreatDATE : 2025/1/23
# CreatTIME : 11:08
# Blog      : https://blog.raxianch.moe/
# Github    : https://github.com/DeSireFire
__author__ = 'RaXianch'

import signal
import logging
from datetime import datetime, timedelta
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import tasks as tasks

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)


def main():
    executors = {"default": ThreadPoolExecutor(max_workers=6)}
    job_defaults = {"coalesce": True, "max_instances": 1}
    scheduler = BlockingScheduler(
        executors=executors, job_defaults=job_defaults)

    # 首次运行
    tasks.add_torrent_jobs(list(range(1, 10)))

    try:
        # 新增种子任务，每15分钟执行一次
        scheduler.add_job(tasks.add_torrent_jobs, "interval", minutes=5, kwargs={"pages": list(range(1, 3))})
        # 新增种子任务
        # scheduler.add_job(tasks.add_torrent_jobs, "interval", minutes=15,
        #                   next_run_time=datetime.now() + timedelta(seconds=10))
        # 清理种子任务（不需要就注释）
        # scheduler.add_job(tasks.clean_torrent, "interval", hours=1, next_run_time=datetime.now() + timedelta(seconds=10))

        logging.info("开始运行，稍后你可以在日志文件中查看日志，观察运行情况...")

        # 定义信号处理函数
        def shutdown(signum, frame):
            logging.info('Received signal to terminate. Shutting down gracefully...')
            scheduler.shutdown()

        # 注册信号处理函数
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        scheduler.start()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        scheduler.shutdown()
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
    # tasks.add_torrent_jobs(list(range(1, 10)))
