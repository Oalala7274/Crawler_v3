"""
配置加载器模块
负责加载和管理所有JSON配置文件
"""
import json
import os
from typing import Dict, List, Any, Optional

# 配置文件目录
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')


class ConfigLoader:
    """配置加载器类"""
    
    _cache: Dict[str, Any] = {}
    
    @classmethod
    def _load_json(cls, filename: str) -> dict:
        """加载单个JSON配置文件"""
        if filename in cls._cache:
            return cls._cache[filename]
        
        filepath = os.path.join(CONFIG_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cls._cache[filename] = data
                return data
        except FileNotFoundError:
            print(f"[错误] 配置文件不存在: {filepath}")
            return {}
        except json.JSONDecodeError as e:
            print(f"[错误] JSON格式错误 ({filename}): {e}")
            return {}
    
    @classmethod
    def load_all(cls) -> dict:
        """
        加载所有配置文件，返回统一配置字典
        
        Returns:
            包含所有配置的字典:
            - settings: 全局设置
            - keyword_sets: 搜索关键词配置
            - scoring_keywords: 打分关键词配置
            - date_formats: 日期格式配置
            - parsers: 网站解析规则配置
        """
        config = {
            'settings': cls._load_json('settings.json'),
            'keyword_sets': cls._load_json('keyword_sets.json'),
            'scoring_keywords': cls._load_json('scoring_keywords.json'),
            'date_formats': cls._load_json('date_formats.json'),
            'parsers': cls._load_json('parsers.json')
        }
        return config
    
    @classmethod
    def get_keyword_set(cls, name: str, config: Optional[dict] = None) -> List[str]:
        """
        获取指定名称的关键词集
        
        Args:
            name: 关键词集名称（如 SEARCH_Q, SEARCH_2, NONE）
            config: 可选的已加载配置字典
            
        Returns:
            关键词列表
        """
        if config is None:
            keyword_sets = cls._load_json('keyword_sets.json')
        else:
            keyword_sets = config.get('keyword_sets', {})
        
        # 处理特殊值 NONE
        if name == "NONE" or not name:
            return []
        
        # 获取映射
        mapping = keyword_sets.get('KEYWORD_SETS_MAPPING', {})
        actual_name = mapping.get(name, name)
        
        # 如果映射到空列表
        if actual_name == [] or actual_name == "NONE":
            return []
        
        # 检查是否是组合搜索
        if isinstance(actual_name, str) and actual_name in keyword_sets:
            keyword_data = keyword_sets[actual_name]
            
            # 如果是组合配置
            if isinstance(keyword_data, dict) and 'sources' in keyword_data:
                result = []
                for source_name in keyword_data['sources']:
                    source_keywords = keyword_sets.get(source_name, [])
                    if isinstance(source_keywords, list):
                        result.extend(source_keywords)
                # 去重但保持顺序
                seen = set()
                unique_result = []
                for kw in result:
                    if kw not in seen:
                        seen.add(kw)
                        unique_result.append(kw)
                return unique_result
            elif isinstance(keyword_data, list):
                return keyword_data
        
        # 直接返回关键词列表
        if actual_name in keyword_sets and isinstance(keyword_sets[actual_name], list):
            return keyword_sets[actual_name]
        
        return []
    
    @classmethod
    def get_parser(cls, name: str, config: Optional[dict] = None) -> dict:
        """
        获取指定名称的解析规则
        
        Args:
            name: 解析器名称
            config: 可选的已加载配置字典
            
        Returns:
            解析规则字典
        """
        if config is None:
            parsers = cls._load_json('parsers.json')
        else:
            parsers = config.get('parsers', {})
        
        parser = parsers.get(name, {})
        if not parser:
            print(f"[警告] 找不到解析器: {name}")
        return parser
    
    @classmethod
    def get_date_format(cls, site_domain: str, config: Optional[dict] = None) -> Optional[str]:
        """
        获取指定网站的日期格式
        
        Args:
            site_domain: 网站域名
            config: 可选的已加载配置字典
            
        Returns:
            日期格式字符串或None
        """
        if config is None:
            date_formats = cls._load_json('date_formats.json')
        else:
            date_formats = config.get('date_formats', {})
        
        site_formats = date_formats.get('site_formats', {})
        
        # 尝试匹配域名
        for domain, format_info in site_formats.items():
            if domain in site_domain:
                return format_info.get('format')
        
        return None
    
    @classmethod
    def get_default_date_formats(cls, config: Optional[dict] = None) -> List[str]:
        """
        获取默认日期格式列表
        
        Args:
            config: 可选的已加载配置字典
            
        Returns:
            日期格式列表
        """
        if config is None:
            date_formats = cls._load_json('date_formats.json')
        else:
            date_formats = config.get('date_formats', {})
        
        return date_formats.get('default_formats', [])
    
    @classmethod
    def clear_cache(cls):
        """清空配置缓存"""
        cls._cache.clear()

