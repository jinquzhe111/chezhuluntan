#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
懂车帝Model Y车友圈问答区爬虫脚本
目标网址：https://www.dongchedi.com/community/4363/wenda
"""

import json
import time
import random
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    StaleElementReferenceException
)
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# 导入配置和工具函数
try:
    from config import *
    from utils import *
except ImportError:
    # 如果没有配置文件，使用默认配置
    BASE_URL = "https://www.dongchedi.com/community/4363/wenda"
    BROWSER_CONFIG = {'headless': False, 'window_size': (1920, 1080)}
    DELAY_CONFIG = {'min_delay': 2, 'max_delay': 5}
    OUTPUT_CONFIG = {'output_file': 'output.json', 'backup_interval': 10}
    LIMITS = {'max_pages': 100}

# 设置日志
setup_logging() if 'setup_logging' in globals() else logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DongchediScraper:
    """懂车帝Model Y车友圈问答区爬虫"""

    def __init__(self):
        self.base_url = BASE_URL
        self.driver = None
        self.wait = None
        self.scraped_data = []

        # 从配置文件加载参数
        self.page_load_timeout = BROWSER_CONFIG.get('page_load_timeout', 30)
        self.element_wait_timeout = BROWSER_CONFIG.get('element_wait_timeout', 10)
        self.min_delay = DELAY_CONFIG.get('min_delay', 2)
        self.max_delay = DELAY_CONFIG.get('max_delay', 5)
        self.max_retries = RETRY_CONFIG.get('max_retries', 3) if 'RETRY_CONFIG' in globals() else 3
        self.max_pages = LIMITS.get('max_pages', 100)
        self.backup_interval = OUTPUT_CONFIG.get('backup_interval', 10)

    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        try:
            chrome_options = Options()

            # 基本配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')

            # 窗口大小
            window_size = BROWSER_CONFIG.get('window_size', (1920, 1080))
            chrome_options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')

            # 反检测配置
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 用户代理
            user_agent = BROWSER_CONFIG.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument(f'--user-agent={user_agent}')

            # 无头模式
            if BROWSER_CONFIG.get('headless', False):
                chrome_options.add_argument('--headless')

            # 使用webdriver-manager自动管理ChromeDriver
            try:
                service = webdriver.chrome.service.Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except:
                # 如果webdriver-manager失败，尝试使用系统PATH中的ChromeDriver
                self.driver = webdriver.Chrome(options=chrome_options)

            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self.wait = WebDriverWait(self.driver, self.element_wait_timeout)
            self.driver.set_page_load_timeout(self.page_load_timeout)

            logger.info("Chrome浏览器驱动设置完成")

        except Exception as e:
            logger.error(f"设置浏览器驱动失败: {e}")
            raise

    def random_delay(self, min_seconds: float = None, max_seconds: float = None):
        """随机延时，避免被检测"""
        min_sec = min_seconds or self.min_delay
        max_sec = max_seconds or self.max_delay
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"延时 {delay:.2f} 秒")
        time.sleep(delay)

    def safe_get_text(self, element) -> str:
        """安全获取元素文本"""
        try:
            return element.text.strip() if element else ""
        except StaleElementReferenceException:
            return ""
        except Exception as e:
            logger.warning(f"获取元素文本失败: {e}")
            return ""

    def safe_get_attribute(self, element, attribute: str) -> str:
        """安全获取元素属性"""
        try:
            return element.get_attribute(attribute) if element else ""
        except StaleElementReferenceException:
            return ""
        except Exception as e:
            logger.warning(f"获取元素属性失败: {e}")
            return ""

    def load_page(self, url: str, retries: int = 0) -> bool:
        """加载页面，带重试机制"""
        try:
            logger.info(f"正在加载页面: {url}")
            self.driver.get(url)

            # 等待页面加载完成
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            self.random_delay(3, 6)  # 等待动态内容加载

            return True

        except TimeoutException:
            logger.warning(f"页面加载超时: {url}")
            if retries < self.max_retries:
                logger.info(f"重试加载页面 ({retries + 1}/{self.max_retries})")
                self.random_delay(5, 10)
                return self.load_page(url, retries + 1)
            return False

        except Exception as e:
            logger.error(f"加载页面失败: {url}, 错误: {e}")
            if retries < self.max_retries:
                logger.info(f"重试加载页面 ({retries + 1}/{self.max_retries})")
                self.random_delay(5, 10)
                return self.load_page(url, retries + 1)
            return False

    def extract_post_links_from_page(self) -> List[Dict]:
        """从当前页面提取帖子链接和基本信息"""
        posts = []

        try:
            # 等待帖子列表加载
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='cheyou-list'], .cheyou_list, [data-testid*='post'], .post-item")))

            # 尝试多种可能的选择器
            post_selectors = [
                "[class*='cheyou-list'] > div",
                ".cheyou_list > div",
                "[data-testid*='post']",
                ".post-item",
                "article",
                "[class*='post-card']",
                "[class*='question-item']"
            ]

            post_elements = []
            for selector in post_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        post_elements = elements
                        logger.info(f"使用选择器找到 {len(elements)} 个帖子: {selector}")
                        break
                except:
                    continue

            if not post_elements:
                # 如果没有找到帖子，尝试从页面源码中解析JSON数据
                posts = self.extract_posts_from_json()
                return posts

            for element in post_elements:
                try:
                    post_info = self.extract_post_info_from_element(element)
                    if post_info:
                        posts.append(post_info)

                except Exception as e:
                    logger.warning(f"提取帖子信息失败: {e}")
                    continue

        except TimeoutException:
            logger.warning("等待帖子列表加载超时，尝试从JSON数据中提取")
            posts = self.extract_posts_from_json()

        except Exception as e:
            logger.error(f"提取帖子链接失败: {e}")

        logger.info(f"从当前页面提取到 {len(posts)} 个帖子")
        return posts

    def extract_posts_from_json(self) -> List[Dict]:
        """从页面的JSON数据中提取帖子信息"""
        posts = []

        try:
            # 获取页面源码
            page_source = self.driver.page_source

            # 查找JSON数据
            json_pattern = r'{"props":.*?"buildId"'
            match = re.search(json_pattern, page_source)

            if match:
                json_str = match.group(0)[:-10] + '}'  # 移除最后的"buildId"部分
                try:
                    data = json.loads(json_str)

                    # 从JSON中提取帖子列表
                    cheyou_list = data.get('props', {}).get('pageProps', {}).get('cheyouList', {}).get('cheyou_list', [])

                    for item in cheyou_list:
                        post_info = {
                            'title': item.get('title', '') or item.get('content', '')[:50] + '...' if item.get('content') else '',
                            'link': f"https://www.dongchedi.com/community/post/{item.get('gid_str', '')}",
                            'author': item.get('profile_info', {}).get('name', ''),
                            'publish_time': self.format_timestamp(item.get('display_time', 0)),
                            'content_preview': item.get('content', '')[:100] + '...' if item.get('content') else '',
                            'comment_count': item.get('comment_count', 0),
                            'gid': item.get('gid_str', '')
                        }

                        if post_info['gid']:  # 只有有效的帖子ID才添加
                            posts.append(post_info)

                except json.JSONDecodeError as e:
                    logger.error(f"解析JSON数据失败: {e}")

        except Exception as e:
            logger.error(f"从JSON提取帖子失败: {e}")

        return posts

    def extract_post_info_from_element(self, element) -> Optional[Dict]:
        """从帖子元素中提取基本信息"""
        try:
            # 尝试多种方式获取标题和链接
            title_selectors = [
                "h3", "h2", "h1",
                "[class*='title']",
                "[class*='content']",
                "a[href*='/post/']",
                ".question-title"
            ]

            title = ""
            link = ""

            for selector in title_selectors:
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, selector)
                    if title_element:
                        title = self.safe_get_text(title_element)
                        link_element = title_element if title_element.tag_name == 'a' else title_element.find_element(By.TAG_NAME, 'a')
                        if link_element:
                            href = self.safe_get_attribute(link_element, 'href')
                            if href:
                                link = urljoin(self.base_url, href)
                                break
                except:
                    continue

            if not title or not link:
                return None

            # 提取作者信息
            author = ""
            author_selectors = [
                "[class*='author']",
                "[class*='user']",
                "[class*='name']",
                ".profile-info .name"
            ]

            for selector in author_selectors:
                try:
                    author_element = element.find_element(By.CSS_SELECTOR, selector)
                    if author_element:
                        author = self.safe_get_text(author_element)
                        break
                except:
                    continue

            # 提取时间信息
            publish_time = ""
            time_selectors = [
                "[class*='time']",
                "[class*='date']",
                "time",
                "[data-time]"
            ]

            for selector in time_selectors:
                try:
                    time_element = element.find_element(By.CSS_SELECTOR, selector)
                    if time_element:
                        publish_time = self.safe_get_text(time_element)
                        break
                except:
                    continue

            return {
                'title': title,
                'link': link,
                'author': author,
                'publish_time': publish_time,
                'content_preview': title[:100] + '...' if len(title) > 100 else title
            }

        except Exception as e:
            logger.warning(f"提取帖子元素信息失败: {e}")
            return None

    def format_timestamp(self, timestamp: int) -> str:
        """格式化时间戳"""
        try:
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        return ""

    def scrape_post_details(self, post_info: Dict) -> Dict:
        """抓取单个帖子的详细内容和评论"""
        logger.info(f"正在抓取帖子详情: {post_info.get('title', '')[:50]}")

        post_data = {
            'title': post_info.get('title', ''),
            'author': post_info.get('author', ''),
            'publish_time': post_info.get('publish_time', ''),
            'content': '',
            'comments': []
        }

        try:
            # 加载帖子详情页
            if not self.load_page(post_info['link']):
                logger.error(f"无法加载帖子页面: {post_info['link']}")
                return post_data

            # 提取帖子内容
            content = self.extract_post_content()
            post_data['content'] = content

            # 提取评论
            comments = self.extract_comments()
            post_data['comments'] = comments

            logger.info(f"成功抓取帖子，评论数: {len(comments)}")

        except Exception as e:
            logger.error(f"抓取帖子详情失败: {e}")

        return post_data

    def extract_post_content(self) -> str:
        """提取帖子正文内容"""
        content = ""

        try:
            # 等待内容加载
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            self.random_delay(2, 4)

            # 尝试多种内容选择器
            content_selectors = [
                "[class*='content']",
                "[class*='detail']",
                "[class*='body']",
                ".post-content",
                ".question-content",
                "article",
                "[data-testid*='content']"
            ]

            for selector in content_selectors:
                try:
                    content_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in content_elements:
                        text = self.safe_get_text(element)
                        if text and len(text) > len(content):
                            content = text
                except:
                    continue

            # 如果没有找到内容，尝试从页面JSON中提取
            if not content:
                content = self.extract_content_from_json()

        except Exception as e:
            logger.warning(f"提取帖子内容失败: {e}")

        return content.strip()

    def extract_content_from_json(self) -> str:
        """从页面JSON数据中提取内容"""
        try:
            page_source = self.driver.page_source
            json_pattern = r'{"props":.*?"buildId"'
            match = re.search(json_pattern, page_source)

            if match:
                json_str = match.group(0)[:-10] + '}'
                data = json.loads(json_str)

                # 查找内容字段
                content_paths = [
                    ['props', 'pageProps', 'content'],
                    ['props', 'pageProps', 'postDetail', 'content'],
                    ['props', 'pageProps', 'data', 'content']
                ]

                for path in content_paths:
                    try:
                        current = data
                        for key in path:
                            current = current[key]
                        if current:
                            return str(current)
                    except:
                        continue

        except Exception as e:
            logger.warning(f"从JSON提取内容失败: {e}")

        return ""

    def extract_comments(self) -> List[Dict]:
        """提取帖子的所有评论"""
        comments = []

        try:
            # 等待评论区加载
            self.random_delay(2, 4)

            # 尝试加载更多评论
            self.load_more_comments()

            # 提取评论
            comment_selectors = [
                "[class*='comment']",
                "[class*='reply']",
                ".comment-item",
                ".reply-item",
                "[data-testid*='comment']"
            ]

            comment_elements = []
            for selector in comment_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        comment_elements = elements
                        logger.info(f"找到 {len(elements)} 个评论元素")
                        break
                except:
                    continue

            for element in comment_elements:
                try:
                    comment_info = self.extract_comment_info(element)
                    if comment_info:
                        comments.append(comment_info)
                except Exception as e:
                    logger.warning(f"提取评论失败: {e}")
                    continue

            # 如果没有找到评论，尝试从JSON中提取
            if not comments:
                comments = self.extract_comments_from_json()

        except Exception as e:
            logger.warning(f"提取评论失败: {e}")

        return comments

    def load_more_comments(self):
        """尝试加载更多评论"""
        try:
            # 查找"加载更多"或"查看更多评论"按钮
            load_more_selectors = [
                "[class*='load-more']",
                "[class*='more-comment']",
                "button[class*='more']",
                ".load-more-btn",
                "[data-testid*='load-more']"
            ]

            for selector in load_more_selectors:
                try:
                    load_more_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if load_more_btn and load_more_btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", load_more_btn)
                        self.random_delay(2, 4)
                        logger.info("点击了加载更多评论按钮")
                        break
                except:
                    continue

            # 尝试滚动到页面底部加载更多内容
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.random_delay(2, 3)

        except Exception as e:
            logger.debug(f"加载更多评论失败: {e}")

    def extract_comment_info(self, element) -> Optional[Dict]:
        """从评论元素中提取信息"""
        try:
            # 提取评论者
            commenter = ""
            commenter_selectors = [
                "[class*='author']",
                "[class*='user']",
                "[class*='name']",
                ".commenter-name"
            ]

            for selector in commenter_selectors:
                try:
                    commenter_element = element.find_element(By.CSS_SELECTOR, selector)
                    if commenter_element:
                        commenter = self.safe_get_text(commenter_element)
                        break
                except:
                    continue

            # 提取评论时间
            comment_time = ""
            time_selectors = [
                "[class*='time']",
                "[class*='date']",
                "time",
                "[data-time]"
            ]

            for selector in time_selectors:
                try:
                    time_element = element.find_element(By.CSS_SELECTOR, selector)
                    if time_element:
                        comment_time = self.safe_get_text(time_element)
                        break
                except:
                    continue

            # 提取评论内容
            comment_content = ""
            content_selectors = [
                "[class*='content']",
                "[class*='text']",
                "[class*='body']",
                ".comment-text"
            ]

            for selector in content_selectors:
                try:
                    content_element = element.find_element(By.CSS_SELECTOR, selector)
                    if content_element:
                        comment_content = self.safe_get_text(content_element)
                        break
                except:
                    continue

            # 如果没有找到内容，使用整个元素的文本
            if not comment_content:
                comment_content = self.safe_get_text(element)

            if comment_content and len(comment_content.strip()) > 0:
                return {
                    'commenter': commenter,
                    'comment_time': comment_time,
                    'comment_content': comment_content.strip()
                }

        except Exception as e:
            logger.warning(f"提取评论信息失败: {e}")

        return None

    def extract_comments_from_json(self) -> List[Dict]:
        """从页面JSON数据中提取评论"""
        comments = []

        try:
            page_source = self.driver.page_source
            json_pattern = r'{"props":.*?"buildId"'
            match = re.search(json_pattern, page_source)

            if match:
                json_str = match.group(0)[:-10] + '}'
                data = json.loads(json_str)

                # 查找评论数据
                comment_paths = [
                    ['props', 'pageProps', 'comments'],
                    ['props', 'pageProps', 'commentList'],
                    ['props', 'pageProps', 'data', 'comments']
                ]

                for path in comment_paths:
                    try:
                        current = data
                        for key in path:
                            current = current[key]

                        if isinstance(current, list):
                            for comment_data in current:
                                comment_info = {
                                    'commenter': comment_data.get('user_name', ''),
                                    'comment_time': self.format_timestamp(comment_data.get('create_time', 0)),
                                    'comment_content': comment_data.get('content', '')
                                }
                                if comment_info['comment_content']:
                                    comments.append(comment_info)
                            break
                    except:
                        continue

        except Exception as e:
            logger.warning(f"从JSON提取评论失败: {e}")

        return comments

    def navigate_to_next_page(self) -> bool:
        """导航到下一页"""
        try:
            # 查找下一页按钮
            next_page_selectors = [
                "[class*='next']",
                "[class*='pagination'] a[class*='next']",
                ".pagination-next",
                "a[aria-label*='下一页']",
                "a[title*='下一页']",
                ".pagination a:last-child"
            ]

            for selector in next_page_selectors:
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_btn and next_btn.is_enabled() and next_btn.is_displayed():
                        # 检查按钮是否可点击（不是禁用状态）
                        classes = next_btn.get_attribute('class') or ''
                        if 'disabled' not in classes.lower():
                            self.driver.execute_script("arguments[0].click();", next_btn)
                            self.random_delay(3, 6)
                            logger.info("成功点击下一页按钮")
                            return True
                except:
                    continue

            # 如果没有找到下一页按钮，尝试通过URL参数翻页
            current_url = self.driver.current_url
            if 'page=' in current_url:
                # 提取当前页码并增加1
                import re
                page_match = re.search(r'page=(\d+)', current_url)
                if page_match:
                    current_page = int(page_match.group(1))
                    next_page = current_page + 1
                    next_url = re.sub(r'page=\d+', f'page={next_page}', current_url)

                    if self.load_page(next_url):
                        logger.info(f"通过URL导航到第 {next_page} 页")
                        return True
            else:
                # 如果URL中没有page参数，尝试添加
                separator = '&' if '?' in current_url else '?'
                next_url = f"{current_url}{separator}page=2"
                if self.load_page(next_url):
                    logger.info("通过URL导航到第2页")
                    return True

            logger.info("没有找到下一页，可能已到最后一页")
            return False

        except Exception as e:
            logger.error(f"导航到下一页失败: {e}")
            return False

    def scrape_all_pages(self):
        """抓取所有页面的帖子"""
        logger.info("开始抓取所有页面的帖子")

        if not self.load_page(self.base_url):
            logger.error("无法加载起始页面")
            return

        page_num = 1
        max_pages = 100  # 设置最大页数限制，避免无限循环

        while page_num <= max_pages:
            logger.info(f"正在抓取第 {page_num} 页")

            # 提取当前页面的帖子链接
            posts = self.extract_post_links_from_page()

            if not posts:
                logger.warning(f"第 {page_num} 页没有找到帖子")
                break

            # 抓取每个帖子的详细内容
            for i, post_info in enumerate(posts, 1):
                logger.info(f"第 {page_num} 页，第 {i}/{len(posts)} 个帖子")

                try:
                    post_data = self.scrape_post_details(post_info)
                    if post_data['content'] or post_data['comments']:  # 只保存有内容的帖子
                        self.scraped_data.append(post_data)
                        logger.info(f"成功保存帖子: {post_data['title'][:50]}")

                    # 每抓取几个帖子就保存一次数据，防止数据丢失
                    if len(self.scraped_data) % 10 == 0:
                        self.save_data(f"output_backup_{len(self.scraped_data)}.json")

                except Exception as e:
                    logger.error(f"抓取帖子失败: {e}")
                    continue

                # 随机延时，避免请求过快
                self.random_delay(1, 3)

            # 尝试导航到下一页
            if not self.navigate_to_next_page():
                logger.info("已抓取完所有页面")
                break

            page_num += 1

            # 每页之间的延时
            self.random_delay(2, 5)

        logger.info(f"抓取完成，共获取 {len(self.scraped_data)} 个帖子")

    def save_data(self, filename: str = "output.json"):
        """保存抓取的数据到JSON文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到 {filename}，共 {len(self.scraped_data)} 个帖子")
        except Exception as e:
            logger.error(f"保存数据失败: {e}")

    def cleanup(self):
        """清理资源"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except:
                pass

    def run(self):
        """运行爬虫"""
        try:
            logger.info("启动懂车帝Model Y车友圈问答区爬虫")

            # 设置浏览器
            self.setup_driver()

            # 抓取所有页面
            self.scrape_all_pages()

            # 保存最终数据
            self.save_data()

            # 生成统计报告
            self.generate_report()

        except KeyboardInterrupt:
            logger.info("用户中断了爬虫运行")
        except Exception as e:
            logger.error(f"爬虫运行出错: {e}")
        finally:
            self.cleanup()

    def generate_report(self):
        """生成抓取报告"""
        total_posts = len(self.scraped_data)
        total_comments = sum(len(post['comments']) for post in self.scraped_data)

        report = {
            '抓取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '总帖子数': total_posts,
            '总评论数': total_comments,
            '平均每帖评论数': round(total_comments / total_posts, 2) if total_posts > 0 else 0
        }

        logger.info("=" * 50)
        logger.info("抓取报告")
        logger.info("=" * 50)
        for key, value in report.items():
            logger.info(f"{key}: {value}")
        logger.info("=" * 50)

        # 保存报告
        with open('scrape_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    scraper = DongchediScraper()
    scraper.run()


if __name__ == "__main__":
    main()