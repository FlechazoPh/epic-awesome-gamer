# -*- coding: utf-8 -*-
# Time       : 2022/1/16 0:25
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from typing import Optional

from services.deploy import ClaimerScheduler
from services.settings import logger


@logger.catch()
def deploy(platform: Optional[str] = None):
    """在微小容器中部署 `claim` 定时调度任务"""
    ClaimerScheduler(silence=True).deploy_jobs(platform)


@logger.catch()
def run(silence: Optional[bool] = None):
    """运行 `claim` 单步子任务，认领周免游戏"""
    ClaimerScheduler(silence=silence).job_loop_claim()
