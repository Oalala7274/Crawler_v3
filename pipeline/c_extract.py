"""
C模块：提取数据
解析HTML，提取新闻条目，分配UUID
"""
import os
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from utils.models import NewsItem, CrawlTask
from utils.config_loader import ConfigLoader
from utils.logger import log_extraction

# 临时文件目录
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')


def run(html: str, task: CrawlTask, config: dict) -> List[NewsItem]:
    """
    从HTML提取新闻条目
    
    Args:
        html: 页面HTML字符串
        task: 爬取任务
        config: 配置字典
        
    Returns:
        NewsItem列表
        
    同时追加写入 temp/items_raw.jsonl
    """
    # 确保临时目录存在
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # 获取解析规则
    parser = ConfigLoader.get_parser(task.parser_name, config)
    if not parser:
        print(f"    ⚠ 找不到解析器: {task.parser_name}")
        return []
    
    # 解析HTML
    soup = BeautifulSoup(html, 'lxml')
    
    # 提取新闻条目
    items = _extract_items(soup, parser, task)
    
    # 写入临时文件
    if items:
        items_file = os.path.join(TEMP_DIR, 'items_raw.jsonl')
        with open(items_file, 'a', encoding='utf-8') as f:
            for item in items:
                f.write(item.to_json() + '\n')
    
    log_extraction(task.parser_name, len(items))
    
    return items


def _extract_items(soup: BeautifulSoup, parser: dict, task: CrawlTask) -> List[NewsItem]:
    """
    根据解析规则提取新闻条目
    
    Args:
        soup: BeautifulSoup对象
        parser: 解析规则
        task: 爬取任务
        
    Returns:
        NewsItem列表
    """
    items = []
    
    # 获取容器选择器
    container_rule = parser.get('item_container', {})
    containers = _find_elements(soup, container_rule)
    
    if not containers:
        print(f"    ⚠ 未找到任何容器元素")
        return items
    
    for container in containers:
        try:
            item = _extract_single_item(container, parser, task)
            if item and item.title:  # 至少要有标题
                items.append(item)
        except Exception as e:
            # 单条提取失败不影响其他条目
            continue
    
    return items


def _extract_single_item(container, parser: dict, task: CrawlTask) -> Optional[NewsItem]:
    """
    从单个容器中提取新闻条目
    
    Args:
        container: BeautifulSoup元素
        parser: 解析规则
        task: 爬取任务
        
    Returns:
        NewsItem或None
    """
    item = NewsItem(source_url=task.url, parser_name=task.parser_name)
    
    # 提取标题
    title_rule = parser.get('title')
    if title_rule:
        title_elem = _find_element(container, title_rule)
        if title_elem:
            item.title = _get_text(title_elem)
    
    # 提取URL
    url_rule = parser.get('url_logic', {})
    item.url = _extract_url(container, url_rule, task.url, title_elem if 'title_elem' in dir() else None)
    
    # 提取日期
    date_rule = parser.get('date_source')
    if date_rule:
        if date_rule.get('method') == 'read_attribute':
            # 从属性读取日期
            date_elem = _find_element(container, date_rule)
            if date_elem:
                attr = date_rule.get('attribute', 'datetime')
                item.date_raw = date_elem.get(attr, '') or _get_text(date_elem)
        else:
            date_elem = _find_element(container, date_rule)
            if date_elem:
                item.date_raw = _get_text(date_elem)
    
    # 提取摘要
    teaser_rule = parser.get('teaser')
    if teaser_rule:
        teaser_elem = _find_element(container, teaser_rule)
        if teaser_elem:
            item.teaser = _get_text(teaser_elem)
    
    return item


def _find_elements(soup, rule: dict) -> list:
    """
    根据规则查找所有匹配的元素
    
    Args:
        soup: BeautifulSoup对象
        rule: 选择器规则
        
    Returns:
        元素列表
    """
    if not rule:
        return []
    
    # CSS选择器
    if rule.get('type') == 'css':
        selector = rule.get('selector', '')
        if selector:
            return soup.select(selector)
    
    # tag + attrs
    tag = rule.get('tag')
    attrs = rule.get('attrs', {})
    
    if tag:
        # 处理 class__contains
        processed_attrs = _process_attrs(attrs)
        if processed_attrs.get('_contains'):
            contains_rules = processed_attrs.pop('_contains')
            elements = soup.find_all(tag, processed_attrs)
            # 过滤包含指定类名的元素
            filtered = []
            for elem in elements:
                elem_classes = elem.get('class', [])
                if isinstance(elem_classes, str):
                    elem_classes = [elem_classes]
                match = True
                for attr_name, substring in contains_rules.items():
                    if attr_name == 'class':
                        if not any(substring in c for c in elem_classes):
                            match = False
                            break
                    else:
                        attr_value = elem.get(attr_name, '')
                        if substring not in str(attr_value):
                            match = False
                            break
                if match:
                    filtered.append(elem)
            return filtered
        else:
            return soup.find_all(tag, processed_attrs)
    
    return []


def _find_element(container, rule: dict):
    """
    根据规则查找单个元素
    
    Args:
        container: 父元素
        rule: 选择器规则
        
    Returns:
        元素或None
    """
    if not rule:
        return None
    
    # CSS选择器
    if rule.get('type') == 'css':
        selector = rule.get('selector', '')
        if selector:
            return container.select_one(selector)
    
    # tag + attrs
    tag = rule.get('tag')
    attrs = rule.get('attrs', {})
    
    if tag:
        processed_attrs = _process_attrs(attrs)
        contains_rules = processed_attrs.pop('_contains', {})
        
        elements = container.find_all(tag, processed_attrs)
        
        if contains_rules:
            for elem in elements:
                match = True
                elem_classes = elem.get('class', [])
                if isinstance(elem_classes, str):
                    elem_classes = [elem_classes]
                    
                for attr_name, substring in contains_rules.items():
                    if attr_name == 'class':
                        if not any(substring in c for c in elem_classes):
                            match = False
                            break
                    else:
                        attr_value = elem.get(attr_name, '')
                        if substring not in str(attr_value):
                            match = False
                            break
                if match:
                    return elem
            return None
        else:
            return elements[0] if elements else None
    
    return None


def _process_attrs(attrs: dict) -> dict:
    """
    处理属性选择器，支持 __contains 语法
    
    Args:
        attrs: 原始属性字典
        
    Returns:
        处理后的属性字典
    """
    processed = {}
    contains = {}
    
    for key, value in attrs.items():
        if '__contains' in key:
            # 提取原始属性名
            attr_name = key.replace('__contains', '')
            contains[attr_name] = value
        elif value is True:
            # href: true 表示只要存在该属性
            processed[key] = True
        else:
            processed[key] = value
    
    if contains:
        processed['_contains'] = contains
    
    return processed


def _extract_url(container, url_rule: dict, base_url: str, title_elem=None) -> str:
    """
    根据URL提取规则获取链接
    
    Args:
        container: 父元素
        url_rule: URL提取规则
        base_url: 基础URL（用于相对路径转换）
        title_elem: 标题元素（用于url_from_title方法）
        
    Returns:
        完整URL字符串
    """
    method = url_rule.get('method', 'find_in_container')
    href = ""
    
    if method == 'url_from_title':
        # 从标题元素获取URL
        if title_elem:
            href = title_elem.get('href', '')
            if not href:
                # 查找父级或子级的a标签
                parent_a = title_elem.find_parent('a')
                if parent_a:
                    href = parent_a.get('href', '')
                else:
                    child_a = title_elem.find('a')
                    if child_a:
                        href = child_a.get('href', '')
                        
    elif method == 'url_from_element':
        # 从指定元素获取URL
        elem = _find_element(container, url_rule)
        if elem:
            href = elem.get('href', '')
            
    elif method == 'find_in_container':
        # 在容器中查找a标签
        tag = url_rule.get('tag', 'a')
        attrs = url_rule.get('attrs', {})
        
        if attrs:
            processed_attrs = _process_attrs(attrs)
            contains_rules = processed_attrs.pop('_contains', {})
            
            a_tags = container.find_all(tag, processed_attrs)
            
            if contains_rules:
                for a in a_tags:
                    match = True
                    a_classes = a.get('class', [])
                    if isinstance(a_classes, str):
                        a_classes = [a_classes]
                    for attr_name, substring in contains_rules.items():
                        if attr_name == 'class':
                            if not any(substring in c for c in a_classes):
                                match = False
                                break
                        else:
                            attr_value = a.get(attr_name, '')
                            if substring not in str(attr_value):
                                match = False
                                break
                    if match:
                        href = a.get('href', '')
                        break
            elif a_tags:
                href = a_tags[0].get('href', '')
        else:
            a_tag = container.find(tag)
            if a_tag:
                href = a_tag.get('href', '')
    
    # 转换相对路径为绝对路径
    if href:
        # 处理特殊前缀
        if href.startswith('./'):
            href = href[2:]
        
        href = urljoin(base_url, href)
    
    return href


def _get_text(elem) -> str:
    """
    获取元素文本，清理空白字符
    
    Args:
        elem: BeautifulSoup元素
        
    Returns:
        清理后的文本
    """
    if elem is None:
        return ""
    
    text = elem.get_text(strip=True)
    # 清理多余空白
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def clear_raw_items():
    """清空原始数据文件"""
    items_file = os.path.join(TEMP_DIR, 'items_raw.jsonl')
    if os.path.exists(items_file):
        os.remove(items_file)


def load_raw_items() -> List[NewsItem]:
    """
    从临时文件加载原始数据
    
    Returns:
        NewsItem列表
    """
    items_file = os.path.join(TEMP_DIR, 'items_raw.jsonl')
    items = []
    
    if os.path.exists(items_file):
        with open(items_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(NewsItem.from_json(line))
    
    return items

