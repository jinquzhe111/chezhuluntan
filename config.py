#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫配置文件
"""

# 目标网站配置
BASE_URL = "https://www.dongchedi.com/community/4363/wenda"
DOMAIN = "www.dongchedi.com"

# 浏览器配置
BROWSER_CONFIG = {
    'headless': True,  # 是否无头模式（服务器环境必须为True）
    'window_size': (1920, 1080),
    'page_load_timeout': 30,
    'element_wait_timeout': 10,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 延时配置（秒）
DELAY_CONFIG = {
    'min_delay': 2,
    'max_delay': 5,
    'page_delay_min': 3,
    'page_delay_max': 6,
    'post_delay_min': 1,
    'post_delay_max': 3
}

# 重试配置
RETRY_CONFIG = {
    'max_retries': 3,
    'retry_delay': 5
}

# 输出配置
OUTPUT_CONFIG = {
    'output_file': 'output.json',
    'backup_interval': 10,  # 每抓取多少个帖子备份一次
    'log_file': 'scraper.log'
}

# 限制配置
LIMITS = {
    'max_pages': 100,  # 最大抓取页数
    'max_posts_per_page': 50,  # 每页最大帖子数
    'max_comments_per_post': 1000  # 每个帖子最大评论数
}

# CSS选择器配置
SELECTORS = {
    'post_list': [
        "[class*='cheyou-list'] > div",
        ".cheyou_list > div", 
        "[data-testid*='post']",
        ".post-item",
        "article",
        "[class*='post-card']",
        "[class*='question-item']"
    ],
    'post_title': [
        "h3", "h2", "h1", 
        "[class*='title']", 
        "[class*='content']",
        "a[href*='/post/']",
        ".question-title"
    ],
    'post_author': [
        "[class*='author']", 
        "[class*='user']", 
        "[class*='name']",
        ".profile-info .name"
    ],
    'post_time': [
        "[class*='time']", 
        "[class*='date']", 
        "time",
        "[data-time]"
    ],
    'post_content': [
        "[class*='content']",
        "[class*='detail']", 
        "[class*='body']",
        ".post-content",
        ".question-content",
        "article",
        "[data-testid*='content']"
    ],
    'comments': [
        "[class*='comment']",
        "[class*='reply']", 
        ".comment-item",
        ".reply-item",
        "[data-testid*='comment']"
    ],
    'comment_author': [
        "[class*='author']",
        "[class*='user']", 
        "[class*='name']",
        ".commenter-name"
    ],
    'comment_time': [
        "[class*='time']",
        "[class*='date']", 
        "time",
        "[data-time]"
    ],
    'comment_content': [
        "[class*='content']",
        "[class*='text']", 
        "[class*='body']",
        ".comment-text"
    ],
    'next_page': [
        "[class*='next']",
        "[class*='pagination'] a[class*='next']",
        ".pagination-next",
        "a[aria-label*='下一页']",
        "a[title*='下一页']",
        ".pagination a:last-child"
    ],
    'load_more': [
        "[class*='load-more']",
        "[class*='more-comment']", 
        "button[class*='more']",
        ".load-more-btn",
        "[data-testid*='load-more']"
    ]
}
