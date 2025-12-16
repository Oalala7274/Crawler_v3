# AI 提示词：生成 Separator Crawler v3.0 完整代码

## 项目背景

请为我生成一个完整的新闻爬虫系统，用于抓取锂电池隔膜行业的国际新闻。系统需要支持多个新闻网站，使用 Selenium Edge 浏览器，并集成 Google Translate API 进行翻译。

---

## 一、项目结构

请严格按照以下目录结构生成代码：

```
Separator_Crawler_v2/
├── main.py                    # 主入口
├── config/
│   ├── keyword_sets.json      # 搜索关键词配置
│   ├── scoring_keywords.json  # 打分关键词配置
│   ├── date_formats.json      # 网站日期格式映射
│   ├── parsers.json           # 网站解析规则配置
│   └── settings.json          # 全局设置（API密钥、筛选日期等）
├── pipeline/
│   ├── __init__.py
│   ├── a_prepare.py           # A模块：读取Excel，生成搜索任务
│   ├── b_browser.py           # B模块：打开网页，执行动作
│   ├── c_extract.py           # C模块：读取数据，分配UUID
│   ├── d_filter.py            # D模块：日期+打分筛选
│   ├── e_sort.py              # E模块：去重和排序
│   └── f_translate.py         # F模块：Google翻译
├── engine/
│   ├── __init__.py
│   ├── edge_driver.py         # Edge浏览器驱动管理
│   └── actions.py             # Selenium动作库
├── utils/
│   ├── __init__.py
│   ├── config_loader.py       # 配置加载器
│   ├── date_parser.py         # 日期解析器（支持网站格式映射+相对时间）
│   ├── logger.py              # 审计日志
│   └── models.py              # 数据模型定义
├── temp/                      # 临时文件目录（运行时生成）
├── output/                    # 最终输出目录
└── log/                       # 日志目录
```

---

## 二、数据流设计

```
Excel控制台 + JSON配置
        ↓
    [A模块] 准备任务 → temp/tasks.jsonl
        ↓
    [B模块] 打开网页执行动作 → 返回页面对象
        ↓
    [C模块] 提取数据 → temp/items_raw.jsonl（每条分配UUID）
        ↓
    [D模块] 筛选数据 → temp/items_filtered.jsonl
        ↓
    [E模块] 去重排序 → temp/items_sorted.jsonl
        ↓
    [F模块] 翻译输出 → output/YYYY-MM-DD_news.txt
```

---

## 三、配置文件详细格式

### 3.1 config/settings.json

```json
{
  "MINIMUM_DATE_TO_KEEP": "2025-12-6",
  "BYPASS_KEYWORD_SCORING": false,
  "PASS_SCORE_THRESHOLD": 80,
  "GOOGLE_TRANSLATE_API_KEY": "YOUR_API_KEY_HERE",
  "SOURCE_EXCEL_FILE": "国际隔膜信息源.xlsx",
  "BROWSER_TIMEOUT": 30,
  "MAX_RETRIES": 3
}
```

### 3.2 config/keyword_sets.json

```json
{
  "SEARCH_SEPARATOR_GENERAL": ["battery separator", "separator", "battery"],
  "SEARCH_SEPARATOR_DETAILED": [
    "wet-process separator",
    "dry-process separator",
    "coated separator",
    "ceramic coating",
    "solid-state separator",
    "polyolefin separator",
    "湿法隔膜",
    "干法隔膜",
    "涂覆隔膜",
    "陶瓷涂覆"
  ],
  "COMBINED_SEARCH": {
    "sources": ["SEARCH_SEPARATOR_GENERAL", "SEARCH_SEPARATOR_DETAILED"],
    "type": "union"
  },
  "KEYWORD_SETS_MAPPING": {
    "SEARCH_Q": "SEARCH_SEPARATOR_GENERAL",
    "SEARCH_2": "COMBINED_SEARCH",
    "NONE": []
  }
}
```

### 3.3 config/scoring_keywords.json

```json
{
  "TIER_1_SEPARATOR": {
    "score": 100,
    "keywords": [
      "battery separator",
      "lithium-ion separator",
      "li-ion separator",
      "separator film",
      "diaphragm",
      "polyolefin separator",
      "锂电池隔膜",
      "锂离子电池隔膜",
      "动力电池隔膜",
      "隔膜"
    ]
  },
  "TIER_2_TECH": {
    "score": 40,
    "keywords": [
      "wet process",
      "dry process",
      "coating",
      "coated separator",
      "ceramic coating",
      "PVDF coating",
      "solid-state",
      "microporous",
      "湿法",
      "干法",
      "涂覆",
      "涂层",
      "陶瓷涂覆",
      "固态电池"
    ]
  },
  "TIER_3_APPLICATION": {
    "score": 100,
    "keywords": [
      "lithium-ion battery",
      "li-ion",
      "EV battery",
      "energy storage",
      "electric vehicle",
      "EV",
      "NEV",
      "锂电池",
      "动力电池",
      "储能",
      "新能源汽车",
      "电动汽车"
    ]
  },
  "COMPANIES": {
    "score": 40,
    "keywords": [
      "Asahi Kasei",
      "Toray",
      "Celgard",
      "SK",
      "SKIET",
      "Entek",
      "SEMCORP",
      "恩捷股份",
      "星源材质",
      "CATL",
      "宁德时代",
      "BYD",
      "比亚迪"
    ]
  },
  "ACTIONS": {
    "score": 40,
    "keywords": [
      "start-up",
      "commissioning",
      "expansion",
      "capacity",
      "GWh",
      "breakthrough",
      "patent",
      "investment",
      "partnership",
      "投产",
      "扩产",
      "产能",
      "突破",
      "专利",
      "投资",
      "合作"
    ]
  }
}
```

### 3.4 config/date_formats.json

```json
{
  "site_formats": {
    "argusmedia.com": {
      "format": "%d/%m/%y",
      "example": "11/12/24"
    },
    "reuters.com": {
      "format": "%B %d, %Y",
      "example": "December 11, 2024"
    },
    "metal.com": {
      "format": "%Y-%m-%d",
      "example": "2024-12-11"
    }
  },
  "default_formats": [
    "%Y-%m-%d",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d %B %Y",
    "%d %b %Y",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%d/%m/%y"
  ]
}
```

### 3.5 config/parsers.json

```json
{
  "ASAHI_KASEI_NEWS": {
    "item_container": { "type": "css", "selector": "ul.news-list-01 li" },
    "title": { "tag": "b", "attrs": {} },
    "date_source": { "tag": "span", "attrs": { "class": "day" } },
    "teaser": { "tag": "b", "attrs": {} },
    "url_logic": { "method": "find_in_container", "tag": "a", "attrs": {} }
  },
  "ARGUS_MEDIA_SEARCH": {
    "item_container": { "type": "css", "selector": "div.qa-news-item" },
    "title": { "type": "css", "selector": "h3.qa-item-title" },
    "url_logic": {
      "method": "url_from_element",
      "type": "css",
      "selector": "a.qa-news-item-content"
    },
    "date_source": { "type": "css", "selector": "p.qa-item-date" },
    "teaser": { "type": "css", "selector": "p.qa-item-summary" }
  },
  "REUTERS_SEARCH": {
    "item_container": { "tag": "li", "attrs": { "data-testid": "StoryCard" } },
    "title": { "tag": "span", "attrs": { "data-testid": "TitleHeading" } },
    "date_source": {
      "tag": "time",
      "attrs": { "data-testid": "DateLineText" }
    },
    "teaser": { "tag": "span", "attrs": { "data-testid": "TitleHeading" } },
    "url_logic": {
      "method": "find_in_container",
      "tag": "a",
      "attrs": { "data-testid": "TitleLink" }
    }
  },
  "google_news": {
    "item_container": { "type": "css", "selector": "div[jslog*='85008']" },
    "title": {
      "type": "css",
      "selector": "a[href^='./read/']:not([aria-hidden='true'])"
    },
    "url_logic": { "method": "url_from_title" },
    "date_source": {
      "method": "read_attribute",
      "attribute": "datetime",
      "type": "css",
      "selector": "time"
    },
    "teaser": null
  },
  "BING_NEWS_SEARCH": {
    "item_container": {
      "tag": "div",
      "attrs": { "class__contains": "news-card" }
    },
    "title": { "tag": "a", "attrs": { "class": "title" } },
    "url_logic": { "method": "url_from_title" },
    "date_source": { "type": "css", "selector": "div.source span[aria-label]" },
    "teaser": { "tag": "div", "attrs": { "class": "snippet" } }
  },
  "METAL_COM_SEARCH": {
    "item_container": {
      "tag": "div",
      "attrs": { "class__contains": "newsItem___" }
    },
    "title": { "tag": "div", "attrs": { "class__contains": "title___" } },
    "url_logic": {
      "method": "url_from_element",
      "tag": "a",
      "attrs": { "href": true }
    },
    "date_source": { "tag": "div", "attrs": { "class__contains": "date___" } },
    "teaser": { "tag": "div", "attrs": { "class__contains": "description___" } }
  },
  "BATTERIES_NEWS_SEARCH": {
    "item_container": {
      "tag": "article",
      "attrs": { "class__contains": "gridlove-post" }
    },
    "title": { "tag": "h2", "attrs": { "class__contains": "entry-title" } },
    "url_logic": { "method": "url_from_title" },
    "date_source": { "tag": "span", "attrs": { "class": "updated" } },
    "teaser": null
  },
  "entek_news": {
    "item_container": {
      "tag": "article",
      "attrs": { "class__contains": "et_pb_post" }
    },
    "title": { "tag": "h2", "attrs": { "class": "entry-title" } },
    "url_logic": { "method": "url_from_title" },
    "date_source": { "tag": "span", "attrs": { "class": "published" } },
    "teaser": { "type": "css", "selector": "div.post-data p" }
  },
  "sk_news": {
    "item_container": { "tag": "div", "attrs": { "class": "grid__col" } },
    "title": { "tag": "p", "attrs": { "class": "h3" } },
    "url_logic": {
      "method": "find_in_container",
      "tag": "a",
      "attrs": { "class__contains": "card--news" }
    },
    "date_source": { "tag": "div", "attrs": { "class": "card__footer" } },
    "teaser": null
  }
}
```

---

## 四、核心数据模型 (utils/models.py)

```python
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
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'CrawlTask':
        return cls(**json.loads(json_str))
```

---

## 五、各模块详细规格

### 5.1 A 模块：准备任务 (pipeline/a_prepare.py)

**功能**：读取 Excel 控制台，生成 JSONL 格式的任务列表

**输入**：

- Excel 文件（国际隔膜信息源.xlsx）
- 关键词配置（keyword_sets.json）

**Excel 列格式**：
| Base_URL | Is_Enabled | Parser_Name | Action_Name | Search_Name | Filter_Name | Engine |
|----------|------------|-------------|-------------|-------------|-------------|--------|

**处理逻辑**：

1. 读取 Excel，跳过 Is_Enabled != TRUE 的行
2. 如果 Search_Name != "NONE"，URL 中的"Separator"占位符需要替换为关键词列表中的每个关键词
3. 为每个任务生成唯一的 task_id
4. 输出到 temp/tasks.jsonl

**关键函数**：

```python
def run(config: dict) -> List[CrawlTask]:
    """
    读取Excel并生成任务列表
    返回: CrawlTask列表
    同时写入 temp/tasks.jsonl
    """
```

### 5.2 B 模块：执行动作 (pipeline/b_browser.py)

**功能**：打开网页，执行 Selenium 动作

**动作类型**：

- `WAIT`: 简单等待 3 秒
- `INFINITE_SCROLL`: 滚动加载更多内容（滚动 5 次，每次 1000px，间隔 0.7 秒）
- `CLICK_EXPAND`: 点击展开按钮

**暂停机制**：

- 检测到验证码/反爬时，打印提示并等待用户输入
- 用户输入 `C` 继续刷新重试
- 用户输入 `P` 跳过当前任务

**关键函数**：

```python
def run(task: CrawlTask, driver) -> Optional[str]:
    """
    执行任务：打开网页，执行动作
    返回: 页面HTML字符串，或None（跳过）
    """
```

### 5.3 C 模块：提取数据 (pipeline/c_extract.py)

**功能**：解析 HTML，提取新闻条目，分配 UUID

**解析逻辑**：

1. 根据 parser_name 获取解析规则
2. 使用 BeautifulSoup 解析 HTML
3. 支持多种选择器：CSS 选择器、tag+attrs、class\_\_contains 模糊匹配
4. URL 提取逻辑：url_from_title / url_from_element / find_in_container
5. 每条数据分配 8 位 UUID
6. 流式写入 temp/items_raw.jsonl

**关键函数**：

```python
def run(html: str, task: CrawlTask, config: dict) -> List[NewsItem]:
    """
    从HTML提取新闻条目
    返回: NewsItem列表
    同时追加写入 temp/items_raw.jsonl
    """
```

### 5.4 D 模块：筛选数据 (pipeline/d_filter.py)

**功能**：日期筛选 + 关键词打分筛选

**日期解析**：

1. 首先尝试网站特定格式（从 date_formats.json）
2. 然后尝试默认格式列表
3. 最后尝试相对时间（"3 天前"、"2 hours ago"等）
4. 支持中英文相对时间

**打分逻辑**：

1. 将 title + teaser 组合为文本
2. 遍历打分规则组，每命中一个关键词加对应分数
3. 英文关键词支持：连字符/空格变体、复数形式（y→ies, +s, +es）
4. 分数 >= PASS_SCORE_THRESHOLD 才保留

**关键函数**：

```python
def run(config: dict) -> int:
    """
    读取items_raw.jsonl，筛选后写入items_filtered.jsonl
    返回: 筛选后的条目数量
    """
```

### 5.5 E 模块：排序 (pipeline/e_sort.py)

**功能**：去重 + 排序

**去重逻辑**：

- 按标题去重
- 保留分数最高的条目

**排序逻辑**：

1. 有效日期的条目优先（日期从新到旧）
2. 同日期按分数降序
3. 无效日期的条目放最后（按分数降序）

**关键函数**：

```python
def run() -> int:
    """
    读取items_filtered.jsonl，去重排序后写入items_sorted.jsonl
    返回: 最终条目数量
    """
```

### 5.6 F 模块：翻译 (pipeline/f_translate.py)

**功能**：调用 Google Translate API 翻译标题和摘要

**翻译逻辑**：

1. 检测文本是否包含中文，中文不翻译
2. 英文翻译为中文
3. 批量翻译以减少 API 调用次数

**输出格式**：

```
Title: [翻译后标题]
Original Title: [原始标题]
Score: [分数] | [命中关键词]
URL: [链接]
Date: [YYYY-MM-DD格式日期] (Raw: [原始日期])
Teaser: [翻译后摘要]
--------------------
```

**关键函数**：

```python
def run(config: dict) -> str:
    """
    读取items_sorted.jsonl，翻译后输出到output目录
    返回: 输出文件路径
    """
```

---

## 六、浏览器引擎 (engine/)

### 6.1 edge_driver.py

```python
def create_driver() -> webdriver.Edge:
    """创建Edge浏览器实例，配置无头模式可选"""

def close_driver(driver):
    """安全关闭浏览器"""
```

### 6.2 actions.py

```python
def perform_wait(driver, delay=3.0):
    """简单等待"""

def perform_scroll_by(driver, pixels=1000, times=5, delay=0.7):
    """滚动加载"""

def perform_click_all(driver, selector, delay=0.5):
    """批量点击展开"""

def perform_refresh(driver):
    """刷新页面"""
```

---

## 七、工具函数 (utils/)

### 7.1 config_loader.py

```python
class ConfigLoader:
    @staticmethod
    def load_all() -> dict:
        """加载所有配置文件，返回统一配置字典"""

    @staticmethod
    def get_keyword_set(name: str) -> List[str]:
        """获取指定名称的关键词集"""

    @staticmethod
    def get_parser(name: str) -> dict:
        """获取指定名称的解析规则"""
```

### 7.2 date_parser.py

```python
def parse_date(date_str: str, site_domain: str = None) -> Optional[date]:
    """
    解析日期字符串
    1. 尝试网站特定格式
    2. 尝试默认格式列表
    3. 尝试相对时间
    """

def parse_relative_time(date_str: str) -> Optional[date]:
    """解析相对时间（中英文支持）"""
```

### 7.3 logger.py

```python
def setup_logger() -> logging.Logger:
    """创建带时间戳的日志文件"""

def log_error(code: str, message: str):
    """记录错误到控制台和日志"""

def pause_for_manual_fix(driver, reason: str, error_code: str = "E000") -> str:
    """暂停等待人工介入，返回 'continue' 或 'skip'"""
```

---

## 八、主入口 (main.py)

```python
import os
from pipeline import a_prepare, b_browser, c_extract, d_filter, e_sort, f_translate
from engine.edge_driver import create_driver, close_driver
from utils.config_loader import ConfigLoader
from utils.logger import setup_logger

def setup_directories():
    """创建临时目录和输出目录"""

def cleanup_temp_files():
    """清理临时文件"""

def main():
    print("=" * 50)
    print("Separator Crawler v2.0 启动")
    print("=" * 50)

    try:
        # 初始化
        setup_directories()
        config = ConfigLoader.load_all()
        logger = setup_logger()

        # A: 准备任务
        print("\n--- Step A: 准备搜索任务 ---")
        tasks = a_prepare.run(config)
        print(f"共生成 {len(tasks)} 个爬取任务")

        # B+C: 执行任务并提取数据
        print("\n--- Step B+C: 执行任务并提取数据 ---")
        driver = create_driver()
        total_items = 0

        for i, task in enumerate(tasks, 1):
            print(f"\n[{i}/{len(tasks)}] 处理: {task.url[:60]}...")
            html = b_browser.run(task, driver)
            if html:
                items = c_extract.run(html, task, config)
                total_items += len(items)
                print(f"    提取到 {len(items)} 条数据")

        close_driver(driver)
        print(f"\n共提取 {total_items} 条原始数据")

        # D: 筛选
        print("\n--- Step D: 筛选数据 ---")
        filtered_count = d_filter.run(config)
        print(f"筛选后保留 {filtered_count} 条")

        # E: 排序
        print("\n--- Step E: 去重排序 ---")
        final_count = e_sort.run()
        print(f"去重后剩余 {final_count} 条")

        # F: 翻译
        print("\n--- Step F: 翻译输出 ---")
        output_file = f_translate.run(config)
        print(f"已输出到: {output_file}")

        print("\n" + "=" * 50)
        print("爬虫流程全部完成!")
        print("=" * 50)

    except KeyboardInterrupt:
        print("\n用户中断 (Ctrl+C)")
    except Exception as e:
        print(f"\n错误: {e}")
        raise
    finally:
        cleanup_temp_files()

if __name__ == "__main__":
    main()
    input("\n按 Enter 键退出...")
```

---

## 九、依赖要求

请生成 requirements.txt：

```
selenium>=4.0.0
openpyxl>=3.0.0
beautifulsoup4>=4.9.0
lxml>=4.6.0
google-cloud-translate>=3.0.0
# 或者使用 googletrans==4.0.0-rc1 作为免费替代
```

---

## 十、代码风格要求

1. Python 3.11+ 兼容
2. 使用 dataclass 定义数据模型
3. 使用类型注解 (Type Hints)
4. 模块级函数使用 docstring 说明
5. 错误处理：捕获异常，打印友好错误信息
6. 日志：关键操作输出到控制台，详细日志写入文件
7. 中文注释和输出信息

---

## 十一、注意事项

1. **JSONL 格式**：每行一个 JSON 对象，便于流式处理
2. **UUID**：使用 uuid.uuid4().hex[:8] 生成 8 位标识符
3. **日期解析**：优先使用网站特定格式，失败后回退到通用格式
4. **打分正则**：英文关键词自动生成变体（复数、连字符）
5. **暂停机制**：遇到反爬时暂停，等待用户输入 C（继续）或 P（跳过）
6. **临时文件**：运行结束后清理 temp 目录
7. **Google 翻译**：批量翻译减少 API 调用，添加延迟避免限流

---

请根据以上规格，生成完整的、可运行的 Python 代码。每个文件单独输出，包含完整的 import 语句和函数实现。
