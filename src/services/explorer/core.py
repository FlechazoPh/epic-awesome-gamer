# -*- coding: utf-8 -*-
# Time       : 2022/1/17 15:20
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import os.path
import time
from typing import List, ContextManager, Union, Dict

from selenium.common.exceptions import WebDriverException
from selenium.webdriver import Chrome
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from services.settings import DIR_EXPLORER, logger
from services.utils import ToolBox
from .exceptions import DiscoveryTimeoutException


class AwesomeFreeGirl:
    """游戏商店探索者 获取免费游戏数据以及促销信息"""

    # 平台对象参数
    URL_STORE_HOME = "https://store.epicgames.com/zh-CN/"
    URL_FREE_GAMES = "https://store.epicgames.com/zh-CN/free-games"
    URL_STORE_PREFIX = "https://store.epicgames.com/zh-CN/browse?"
    URL_STORE_FREE = (
        f"{URL_STORE_PREFIX}sortBy=releaseDate&sortDir=DESC&priceTier=tierFree&count=40"
    )
    URL_PROMOTIONS = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=zh-CN"
    URL_PRODUCT_PAGE = "https://store.epicgames.com/zh-CN/p/"

    def __init__(self, silence: bool = None):
        self.silence = True if silence is None else silence

        # 驱动参数
        self.action_name = "AwesomeFreeGirl"

        # 运行缓存
        self.runtime_workspace = None
        self.path_free_games = "ctx_games.csv"
        self.game_objs = {}  # {index0:{name:value url:value}, }

        # 初始化工作空间
        self._init_workspace()

    def _init_workspace(self) -> None:
        """初始化工作目录 缓存游戏商店数据"""
        self.runtime_workspace = "." if not os.path.exists(DIR_EXPLORER) else DIR_EXPLORER
        self.path_free_games = os.path.join(self.runtime_workspace, self.path_free_games)

    def _discovery_free_games(
        self, ctx: Union[ContextManager, Chrome], ctx_cookies: List[dict]
    ) -> None:
        """发现玩家所属地区可视的常驻免费游戏数据"""

        # 重载玩家令牌
        if ctx_cookies:
            ctx.get(self.URL_STORE_FREE)
            for cookie_dict in ctx_cookies:
                ctx.add_cookie(cookie_dict)

        _mode = "（深度搜索）" if ctx_cookies else "（广度搜索）"
        logger.debug(
            ToolBox.runtime_report(
                motive="DISCOVERY",
                action_name=self.action_name,
                message=f"📡 正在为玩家搜集免费游戏{_mode}...",
            )
        )

        # 获取免费游戏链接
        _start = time.time()
        _url_store_free = self.URL_STORE_FREE
        while True:
            ctx.get(_url_store_free)
            time.sleep(1)
            WebDriverWait(ctx, 10, ignored_exceptions=WebDriverException).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//section[@data-testid='section-wrapper']")
                )
            )

            # 滑到底部
            action = ActionChains(ctx)
            action.send_keys(Keys.END)
            action.perform()

            # 判断异常跳转
            if "tierFree" not in ctx.current_url:
                break
            if time.time() - _start > 80:
                raise DiscoveryTimeoutException("获取免费游戏链接超时")

            # 断言最后一页
            WebDriverWait(ctx, 5, ignored_exceptions=WebDriverException).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[@data-component='PaginationItem']")
                )
            )
            page_switcher = ctx.find_elements(
                By.XPATH, "//a[@data-component='PaginationItem']"
            )[-1]

            # 提取价值信息
            game_objs = ctx.find_elements(By.XPATH, "//a[@class='css-1jx3eyg']")
            for game_obj in game_objs:
                name = game_obj.get_attribute("aria-label")
                url = game_obj.get_attribute("href")
                self.game_objs.update(
                    {self.game_objs.__len__(): {"name": name.strip(), "url": url.strip()}}
                )

            # 页面跳转判断
            page_end = page_switcher.get_attribute("href")
            if page_end in ctx.current_url:
                break

            # 更新跳转链接
            _url_store_free = page_end

        logger.success(
            ToolBox.runtime_report(
                motive="DISCOVERY",
                action_name=self.action_name,
                message="免费游戏搜集完毕",
                qsize=len(self.game_objs),
            )
        )

    def stress_expressions(self, ctx: Union[ContextManager, Chrome]) -> Dict[str, str]:
        """
        应力表达式的主要实现

        :param ctx: 浏览器驱动上下文
        :return: 不需要 quit()
        """
        logger.debug(
            ToolBox.runtime_report(
                motive="DISCOVERY",
                action_name=self.action_name,
                message="📡 使用应力表达式搜索周免游戏...",
            )
        )

        # 访问链接 游戏名称
        pending_games = {}

        for _ in range(2):
            try:
                ctx.get(self.URL_STORE_HOME)
                time.sleep(3)

                # 定位周免游戏的绝对位置
                WebDriverWait(ctx, 45, ignored_exceptions=WebDriverException).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//a[contains(string(),'当前免费')]")
                    )
                )

                # 周免游戏基本信息
                stress_operator = ctx.find_elements(
                    By.XPATH, "//a[contains(string(),'当前免费')]"
                )
                img_seq = ctx.find_elements(
                    By.XPATH, "//a[contains(string(),'当前免费')]//img"
                )

                # 重组周免游戏信息
                for index, _ in enumerate(stress_operator):
                    href = stress_operator[index].get_attribute("href")
                    alias = img_seq[index].get_attribute("alt")
                    pending_games[href] = alias

                break
            except (WebDriverException, AttributeError):
                continue

        return pending_games
