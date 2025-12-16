"""
数据模型定义模块
定义 NewsItem 和 CrawlTask 数据结构
"""
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional, List
import uuid
import json


@dataclass
class NewsItem:
    """新闻条目数据模型"""
    uuid: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str = ""
    url: str = ""
    date_raw: str = ""                    # 原始日期字符串
    date_parsed: Optional[date] = None    # 解析后的日期
    teaser: str = ""
    score: int = 0
    score_hits: List[str] = field(default_factory=list)
    source_url: str = ""                  # 来源页面URL
    parser_name: str = ""                 # 使用的解析器名称

    def to_json(self) -> str:
        """序列化为JSON字符串"""
        data = asdict(self)
        if self.date_parsed:
            data['date_parsed'] = self.date_parsed.isoformat()
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'NewsItem':
        """从JSON字符串反序列化"""
        data = json.loads(json_str)
        if data.get('date_parsed'):
            data['date_parsed'] = date.fromisoformat(data['date_parsed'])
        return cls(**data)


@dataclass
class CrawlTask:
    """爬取任务数据模型"""
    task_id: str
    url: str
    parser_name: str
    action_name: str        # WAIT / INFINITE_SCROLL / CLICK_EXPAND
    filter_name: str
    engine: str = "edge"

    def to_json(self) -> str:
        """序列化为JSON字符串"""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'CrawlTask':
        """从JSON字符串反序列化"""
        return cls(**json.loads(json_str))

