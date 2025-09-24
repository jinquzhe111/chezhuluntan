#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫工具函数
"""

import re
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """清理文本内容"""
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 移除特殊字符
    text = re.sub(r'[\r\n\t]', ' ', text)
    
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    return text.strip()


def format_timestamp(timestamp: Any) -> str:
    """格式化时间戳为标准时间格式"""
    try:
        if isinstance(timestamp, str):
            # 尝试解析字符串时间
            if '分钟前' in timestamp:
                minutes = int(re.search(r'(\d+)', timestamp).group(1))
                dt = datetime.now() - timedelta(minutes=minutes)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            elif '小时前' in timestamp:
                hours = int(re.search(r'(\d+)', timestamp).group(1))
                dt = datetime.now() - timedelta(hours=hours)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            elif '天前' in timestamp:
                days = int(re.search(r'(\d+)', timestamp).group(1))
                dt = datetime.now() - timedelta(days=days)
                return dt.strftime('%Y-%m-%d')
            elif re.match(r'\d{4}-\d{2}-\d{2}', timestamp):
                return timestamp
            else:
                return timestamp
                
        elif isinstance(timestamp, (int, float)):
            # Unix时间戳
            if timestamp > 1e10:  # 毫秒时间戳
                timestamp = timestamp / 1000
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
            
    except Exception as e:
        logger.warning(f"时间格式化失败: {timestamp}, 错误: {e}")
        
    return str(timestamp) if timestamp else ""


def extract_post_id_from_url(url: str) -> str:
    """从URL中提取帖子ID"""
    try:
        # 匹配各种可能的帖子ID格式
        patterns = [
            r'/post/(\d+)',
            r'/(\d+)/?$',
            r'id=(\d+)',
            r'gid=(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
                
    except Exception as e:
        logger.warning(f"提取帖子ID失败: {url}, 错误: {e}")
        
    return ""


def is_valid_url(url: str) -> bool:
    """检查URL是否有效"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def safe_json_loads(json_str: str) -> Optional[Dict]:
    """安全解析JSON字符串"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON解析失败: {e}")
        return None
    except Exception as e:
        logger.error(f"JSON解析异常: {e}")
        return None


def extract_numbers(text: str) -> List[int]:
    """从文本中提取所有数字"""
    try:
        return [int(x) for x in re.findall(r'\d+', text)]
    except:
        return []


def random_delay(min_seconds: float = 1, max_seconds: float = 3):
    """随机延时"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def save_json(data: Any, filename: str, ensure_ascii: bool = False, indent: int = 2):
    """保存数据为JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
        logger.info(f"数据已保存到 {filename}")
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败: {e}")
        return False


def load_json(filename: str) -> Optional[Any]:
    """加载JSON文件"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"文件不存在: {filename}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON文件格式错误: {filename}, 错误: {e}")
        return None
    except Exception as e:
        logger.error(f"加载JSON文件失败: {filename}, 错误: {e}")
        return None


def validate_post_data(post: Dict) -> bool:
    """验证帖子数据的完整性"""
    required_fields = ['title', 'author', 'publish_time', 'content', 'comments']
    
    for field in required_fields:
        if field not in post:
            logger.warning(f"帖子缺少必需字段: {field}")
            return False
    
    # 检查评论格式
    if not isinstance(post['comments'], list):
        logger.warning("评论字段不是列表格式")
        return False
    
    for comment in post['comments']:
        if not isinstance(comment, dict):
            logger.warning("评论不是字典格式")
            return False
        
        comment_fields = ['commenter', 'comment_time', 'comment_content']
        for field in comment_fields:
            if field not in comment:
                logger.warning(f"评论缺少必需字段: {field}")
                return False
    
    return True


def merge_duplicate_posts(posts: List[Dict]) -> List[Dict]:
    """合并重复的帖子"""
    seen_titles = set()
    unique_posts = []
    
    for post in posts:
        title = post.get('title', '').strip()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_posts.append(post)
        else:
            logger.debug(f"跳过重复帖子: {title}")
    
    logger.info(f"去重前: {len(posts)} 个帖子，去重后: {len(unique_posts)} 个帖子")
    return unique_posts


def generate_statistics(posts: List[Dict]) -> Dict:
    """生成统计信息"""
    if not posts:
        return {}
    
    total_posts = len(posts)
    total_comments = sum(len(post.get('comments', [])) for post in posts)
    
    # 统计有内容的帖子
    posts_with_content = sum(1 for post in posts if post.get('content', '').strip())
    
    # 统计有评论的帖子
    posts_with_comments = sum(1 for post in posts if post.get('comments', []))
    
    # 平均评论数
    avg_comments = total_comments / total_posts if total_posts > 0 else 0
    
    # 最多评论的帖子
    max_comments_post = max(posts, key=lambda x: len(x.get('comments', []))) if posts else None
    max_comments_count = len(max_comments_post.get('comments', [])) if max_comments_post else 0
    
    return {
        'total_posts': total_posts,
        'total_comments': total_comments,
        'posts_with_content': posts_with_content,
        'posts_with_comments': posts_with_comments,
        'average_comments_per_post': round(avg_comments, 2),
        'max_comments_count': max_comments_count,
        'max_comments_post_title': max_comments_post.get('title', '') if max_comments_post else '',
        'content_rate': round(posts_with_content / total_posts * 100, 2) if total_posts > 0 else 0,
        'comment_rate': round(posts_with_comments / total_posts * 100, 2) if total_posts > 0 else 0
    }


def create_backup_filename(base_name: str = "output", extension: str = "json") -> str:
    """创建带时间戳的备份文件名"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_backup_{timestamp}.{extension}"


def setup_logging(log_file: str = "scraper.log", level: int = logging.INFO):
    """设置日志配置"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 设置第三方库的日志级别
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
