"""
日期解析器模块
支持多种日期格式和相对时间解析
"""
import re
from datetime import date, datetime, timedelta
from typing import Optional
from .config_loader import ConfigLoader


def parse_date(date_str: str, site_domain: str = None, config: dict = None) -> Optional[date]:
    """
    解析日期字符串
    
    解析顺序：
    1. 尝试网站特定格式
    2. 尝试默认格式列表
    3. 尝试相对时间
    
    Args:
        date_str: 原始日期字符串
        site_domain: 网站域名（用于获取网站特定格式）
        config: 可选的已加载配置字典
        
    Returns:
        解析成功返回date对象，失败返回None
    """
    if not date_str or not date_str.strip():
        return None
    
    date_str = date_str.strip()
    
    # 1. 尝试网站特定格式
    if site_domain:
        site_format = ConfigLoader.get_date_format(site_domain, config)
        if site_format:
            parsed = _try_parse_format(date_str, site_format)
            if parsed:
                return parsed
    
    # 2. 尝试默认格式列表
    default_formats = ConfigLoader.get_default_date_formats(config)
    for fmt in default_formats:
        parsed = _try_parse_format(date_str, fmt)
        if parsed:
            return parsed
    
    # 3. 尝试相对时间
    parsed = parse_relative_time(date_str)
    if parsed:
        return parsed
    
    # 4. 尝试从datetime属性解析 (ISO 8601)
    parsed = _try_parse_iso(date_str)
    if parsed:
        return parsed
    
    return None


def _try_parse_format(date_str: str, fmt: str) -> Optional[date]:
    """尝试使用指定格式解析日期"""
    try:
        return datetime.strptime(date_str, fmt).date()
    except ValueError:
        return None


def _try_parse_iso(date_str: str) -> Optional[date]:
    """尝试解析ISO 8601格式的日期时间"""
    # 处理类似 "2024-12-11T10:30:00Z" 或 "2024-12-11T10:30:00+08:00"
    iso_patterns = [
        r'(\d{4}-\d{2}-\d{2})T',  # ISO格式开头
        r'(\d{4}-\d{2}-\d{2})',    # 纯日期
    ]
    
    for pattern in iso_patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d').date()
            except ValueError:
                continue
    
    return None


def parse_relative_time(date_str: str) -> Optional[date]:
    """
    解析相对时间（中英文支持）
    
    支持的格式：
    - 英文: "3 days ago", "2 hours ago", "1 week ago", "a minute ago"
    - 中文: "3天前", "2小时前", "1周前", "刚刚"
    
    Args:
        date_str: 相对时间字符串
        
    Returns:
        解析成功返回date对象，失败返回None
    """
    today = date.today()
    date_str_lower = date_str.lower().strip()
    
    # 处理"刚刚"、"just now"、"now"
    if date_str_lower in ['刚刚', 'just now', 'now', '刚才']:
        return today
    
    # 处理"今天"、"today"
    if date_str_lower in ['今天', 'today']:
        return today
    
    # 处理"昨天"、"yesterday"
    if date_str_lower in ['昨天', 'yesterday']:
        return today - timedelta(days=1)
    
    # 英文相对时间模式
    en_patterns = [
        # "3 days ago", "a day ago"
        (r'(\d+)\s*days?\s*ago', lambda m: timedelta(days=int(m.group(1)))),
        (r'a\s*day\s*ago', lambda m: timedelta(days=1)),
        # "3 hours ago", "an hour ago"
        (r'(\d+)\s*hours?\s*ago', lambda m: timedelta(hours=int(m.group(1)))),
        (r'an?\s*hour\s*ago', lambda m: timedelta(hours=1)),
        # "3 minutes ago", "a minute ago"
        (r'(\d+)\s*minutes?\s*ago', lambda m: timedelta(minutes=int(m.group(1)))),
        (r'a\s*minute\s*ago', lambda m: timedelta(minutes=1)),
        # "3 weeks ago", "a week ago"
        (r'(\d+)\s*weeks?\s*ago', lambda m: timedelta(weeks=int(m.group(1)))),
        (r'a\s*week\s*ago', lambda m: timedelta(weeks=1)),
        # "3 months ago", "a month ago"
        (r'(\d+)\s*months?\s*ago', lambda m: timedelta(days=int(m.group(1)) * 30)),
        (r'a\s*month\s*ago', lambda m: timedelta(days=30)),
        # "3 seconds ago"
        (r'(\d+)\s*seconds?\s*ago', lambda m: timedelta(seconds=int(m.group(1)))),
    ]
    
    for pattern, delta_func in en_patterns:
        match = re.search(pattern, date_str_lower)
        if match:
            delta = delta_func(match)
            result_datetime = datetime.now() - delta
            return result_datetime.date()
    
    # 中文相对时间模式
    cn_patterns = [
        # "3天前"
        (r'(\d+)\s*天前', lambda m: timedelta(days=int(m.group(1)))),
        # "3小时前"
        (r'(\d+)\s*小时前', lambda m: timedelta(hours=int(m.group(1)))),
        # "3分钟前"
        (r'(\d+)\s*分钟前', lambda m: timedelta(minutes=int(m.group(1)))),
        # "3周前"
        (r'(\d+)\s*周前', lambda m: timedelta(weeks=int(m.group(1)))),
        # "3个月前"
        (r'(\d+)\s*个?月前', lambda m: timedelta(days=int(m.group(1)) * 30)),
        # "3秒前"
        (r'(\d+)\s*秒前', lambda m: timedelta(seconds=int(m.group(1)))),
    ]
    
    for pattern, delta_func in cn_patterns:
        match = re.search(pattern, date_str)
        if match:
            delta = delta_func(match)
            result_datetime = datetime.now() - delta
            return result_datetime.date()
    
    return None


def extract_date_from_url(url: str) -> Optional[date]:
    """
    尝试从URL中提取日期
    
    支持的格式：
    - /2024/12/11/
    - /2024-12-11/
    - /20241211/
    
    Args:
        url: URL字符串
        
    Returns:
        解析成功返回date对象，失败返回None
    """
    patterns = [
        r'/(\d{4})/(\d{2})/(\d{2})/',
        r'/(\d{4})-(\d{2})-(\d{2})/',
        r'/(\d{4})(\d{2})(\d{2})/',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            try:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                return date(year, month, day)
            except ValueError:
                continue
    
    return None

