"""
E模块：排序
去重 + 排序
"""
import os
from typing import List
from datetime import date

from utils.models import NewsItem
from utils.logger import log_info

# 临时文件目录
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')


def run() -> int:
    """
    读取items_filtered.jsonl，去重排序后写入items_sorted.jsonl
    
    Returns:
        最终条目数量
    """
    # 读取筛选后的数据
    filtered_file = os.path.join(TEMP_DIR, 'items_filtered.jsonl')
    if not os.path.exists(filtered_file):
        print("    ⚠ 没有筛选后的数据文件")
        return 0
    
    items = []
    with open(filtered_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(NewsItem.from_json(line))
    
    original_count = len(items)
    print(f"    读取到 {original_count} 条筛选后数据")
    
    # 去重
    unique_items = _deduplicate(items)
    dedup_count = len(unique_items)
    print(f"    去重后剩余 {dedup_count} 条")
    
    # 排序
    sorted_items = _sort_items(unique_items)
    
    # 写入排序后的数据
    sorted_file = os.path.join(TEMP_DIR, 'items_sorted.jsonl')
    with open(sorted_file, 'w', encoding='utf-8') as f:
        for item in sorted_items:
            f.write(item.to_json() + '\n')
    
    log_info(f"排序完成: {original_count} → {dedup_count}")
    
    return len(sorted_items)


def _deduplicate(items: List[NewsItem]) -> List[NewsItem]:
    """
    按标题去重，保留分数最高的条目
    
    Args:
        items: NewsItem列表
        
    Returns:
        去重后的列表
    """
    # 按标题分组
    title_groups = {}
    
    for item in items:
        # 标准化标题（去除空格、转小写）
        normalized_title = _normalize_title(item.title)
        
        if not normalized_title:
            continue
        
        if normalized_title in title_groups:
            # 保留分数更高的
            if item.score > title_groups[normalized_title].score:
                title_groups[normalized_title] = item
            # 分数相同时，保留日期更新的
            elif item.score == title_groups[normalized_title].score:
                existing_date = title_groups[normalized_title].date_parsed
                if item.date_parsed and existing_date:
                    if item.date_parsed > existing_date:
                        title_groups[normalized_title] = item
        else:
            title_groups[normalized_title] = item
    
    return list(title_groups.values())


def _normalize_title(title: str) -> str:
    """
    标准化标题用于去重比较
    
    Args:
        title: 原始标题
        
    Returns:
        标准化后的标题
    """
    if not title:
        return ""
    
    # 转小写
    normalized = title.lower()
    # 去除标点符号
    import re
    normalized = re.sub(r'[^\w\s]', '', normalized)
    # 去除多余空格
    normalized = ' '.join(normalized.split())
    
    return normalized


def _sort_items(items: List[NewsItem]) -> List[NewsItem]:
    """
    排序新闻条目
    
    排序规则：
    1. 有效日期的条目优先（日期从新到旧）
    2. 同日期按分数降序
    3. 无效日期的条目放最后（按分数降序）
    
    Args:
        items: NewsItem列表
        
    Returns:
        排序后的列表
    """
    # 分离有日期和无日期的条目
    with_date = []
    without_date = []
    
    for item in items:
        if item.date_parsed:
            with_date.append(item)
        else:
            without_date.append(item)
    
    # 有日期的：按日期降序，同日期按分数降序
    with_date.sort(key=lambda x: (x.date_parsed, x.score), reverse=True)
    
    # 无日期的：按分数降序
    without_date.sort(key=lambda x: x.score, reverse=True)
    
    # 合并：有日期的在前
    return with_date + without_date


def load_sorted_items() -> List[NewsItem]:
    """
    从临时文件加载排序后的数据
    
    Returns:
        NewsItem列表
    """
    sorted_file = os.path.join(TEMP_DIR, 'items_sorted.jsonl')
    items = []
    
    if os.path.exists(sorted_file):
        with open(sorted_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(NewsItem.from_json(line))
    
    return items

