"""
D模块：筛选数据
日期筛选 + 关键词打分筛选
"""
import os
import re
from datetime import date
from typing import List, Tuple
from urllib.parse import urlparse

from utils.models import NewsItem
from utils.date_parser import parse_date
from utils.logger import log_filter_result

# 临时文件目录
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')


def run(config: dict) -> int:
    """
    读取items_raw.jsonl，筛选后写入items_filtered.jsonl
    
    Args:
        config: 配置字典
        
    Returns:
        筛选后的条目数量
    """
    # 读取原始数据
    items_file = os.path.join(TEMP_DIR, 'items_raw.jsonl')
    if not os.path.exists(items_file):
        print("    ⚠ 没有原始数据文件")
        return 0
    
    items = []
    with open(items_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(NewsItem.from_json(line))
    
    original_count = len(items)
    print(f"    读取到 {original_count} 条原始数据")
    
    # 获取配置
    settings = config.get('settings', {})
    min_date_str = settings.get('MINIMUM_DATE_TO_KEEP', '')
    bypass_scoring = settings.get('BYPASS_KEYWORD_SCORING', False)
    pass_threshold = settings.get('PASS_SCORE_THRESHOLD', 80)
    
    # 解析最小日期
    min_date = None
    if min_date_str:
        try:
            parts = min_date_str.split('-')
            min_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            print(f"    ⚠ 无效的最小日期格式: {min_date_str}")
    
    # 获取打分关键词
    scoring_keywords = config.get('scoring_keywords', {})
    
    # 筛选数据
    filtered_items = []
    
    for item in items:
        # 1. 解析日期
        if item.date_raw and not item.date_parsed:
            # 从source_url提取域名
            domain = ""
            if item.source_url:
                parsed = urlparse(item.source_url)
                domain = parsed.netloc
            
            item.date_parsed = parse_date(item.date_raw, domain, config)
        
        # 2. 日期筛选
        if min_date and item.date_parsed:
            if item.date_parsed < min_date:
                continue  # 日期过旧，跳过
        
        # 3. 关键词打分
        if not bypass_scoring:
            score, hits = _calculate_score(item, scoring_keywords)
            item.score = score
            item.score_hits = hits
            
            if score < pass_threshold:
                continue  # 分数不够，跳过
        else:
            # 跳过打分，给一个默认分数
            item.score = 100
            item.score_hits = ["BYPASS"]
        
        filtered_items.append(item)
    
    # 写入筛选后的数据
    filtered_file = os.path.join(TEMP_DIR, 'items_filtered.jsonl')
    with open(filtered_file, 'w', encoding='utf-8') as f:
        for item in filtered_items:
            f.write(item.to_json() + '\n')
    
    filtered_count = len(filtered_items)
    log_filter_result(original_count, filtered_count, f"日期>={min_date}, 分数>={pass_threshold}")
    
    return filtered_count


def _calculate_score(item: NewsItem, scoring_keywords: dict) -> Tuple[int, List[str]]:
    """
    计算新闻条目的分数
    
    Args:
        item: 新闻条目
        scoring_keywords: 打分关键词配置
        
    Returns:
        (分数, 命中关键词列表)
    """
    # 组合文本
    text = f"{item.title} {item.teaser}".lower()
    
    total_score = 0
    hits = []
    
    for group_name, group_config in scoring_keywords.items():
        group_score = group_config.get('score', 0)
        keywords = group_config.get('keywords', [])
        
        group_hit = False
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 生成关键词变体
            variants = _generate_variants(keyword_lower)
            
            for variant in variants:
                # 使用正则匹配（支持词边界）
                pattern = r'\b' + re.escape(variant) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    if not group_hit:
                        total_score += group_score
                        group_hit = True
                    hits.append(keyword)
                    break
            
            if group_hit:
                break  # 每个组只计一次分
    
    return total_score, hits


def _generate_variants(keyword: str) -> List[str]:
    """
    生成关键词变体（复数形式、连字符变体等）
    
    Args:
        keyword: 原始关键词
        
    Returns:
        变体列表
    """
    variants = [keyword]
    
    # 仅处理英文关键词
    if not keyword.isascii():
        return variants
    
    # 连字符/空格变体
    if '-' in keyword:
        # separator-film -> separator film
        variants.append(keyword.replace('-', ' '))
        # separator-film -> separatorfilm
        variants.append(keyword.replace('-', ''))
    elif ' ' in keyword:
        # separator film -> separator-film
        variants.append(keyword.replace(' ', '-'))
    
    # 复数形式
    base = keyword.rstrip('s')  # 去掉可能的s
    
    # 如果原词不是以s结尾，添加复数
    if not keyword.endswith('s'):
        # y -> ies
        if keyword.endswith('y') and len(keyword) > 1 and keyword[-2] not in 'aeiou':
            variants.append(keyword[:-1] + 'ies')
        # 直接加s
        variants.append(keyword + 's')
        # 加es（以s, x, z, ch, sh结尾）
        if keyword.endswith(('s', 'x', 'z', 'ch', 'sh')):
            variants.append(keyword + 'es')
    
    return list(set(variants))


def load_filtered_items() -> List[NewsItem]:
    """
    从临时文件加载筛选后的数据
    
    Returns:
        NewsItem列表
    """
    filtered_file = os.path.join(TEMP_DIR, 'items_filtered.jsonl')
    items = []
    
    if os.path.exists(filtered_file):
        with open(filtered_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(NewsItem.from_json(line))
    
    return items

