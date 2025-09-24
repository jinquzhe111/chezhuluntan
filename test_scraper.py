#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫测试脚本 - 只抓取少量数据用于测试
"""

import logging
from scraper import DongchediScraper

# 设置日志级别为DEBUG以便调试
logging.basicConfig(level=logging.DEBUG)

def test_scraper():
    """测试爬虫功能"""
    scraper = DongchediScraper()
    
    # 修改配置以便快速测试
    scraper.max_pages = 2  # 只抓取2页
    scraper.min_delay = 1  # 减少延时
    scraper.max_delay = 2
    
    try:
        print("开始测试爬虫...")
        
        # 设置浏览器
        scraper.setup_driver()
        print("✓ 浏览器设置成功")
        
        # 加载首页
        if scraper.load_page(scraper.base_url):
            print("✓ 首页加载成功")
        else:
            print("✗ 首页加载失败")
            return
        
        # 提取帖子列表
        posts = scraper.extract_post_links_from_page()
        print(f"✓ 找到 {len(posts)} 个帖子")
        
        if posts:
            # 测试抓取第一个帖子的详情
            first_post = posts[0]
            print(f"测试抓取帖子: {first_post.get('title', '')[:50]}")
            
            post_data = scraper.scrape_post_details(first_post)
            print(f"✓ 帖子内容长度: {len(post_data.get('content', ''))}")
            print(f"✓ 评论数量: {len(post_data.get('comments', []))}")
            
            # 保存测试数据
            scraper.scraped_data = [post_data]
            scraper.save_data("test_output.json")
            print("✓ 测试数据已保存到 test_output.json")
        
        print("测试完成！")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    test_scraper()
