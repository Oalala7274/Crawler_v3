"""
F模块：翻译
调用Google Translate API翻译标题和摘要
"""
import os
import re
import time
from datetime import date
from typing import List, Optional

from utils.models import NewsItem
from utils.logger import log_info

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')


def run(config: dict) -> str:
    """
    读取items_sorted.jsonl，翻译后输出到output目录
    
    Args:
        config: 配置字典
        
    Returns:
        输出文件路径
    """
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 读取排序后的数据
    sorted_file = os.path.join(TEMP_DIR, 'items_sorted.jsonl')
    if not os.path.exists(sorted_file):
        print("    ⚠ 没有排序后的数据文件")
        return ""
    
    items = []
    with open(sorted_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(NewsItem.from_json(line))
    
    print(f"    读取到 {len(items)} 条待翻译数据")
    
    # 获取API密钥
    api_key = config.get('settings', {}).get('GOOGLE_TRANSLATE_API_KEY', '')
    
    # 翻译
    translator = Translator(api_key)
    translated_items = translator.translate_items(items)
    
    # 生成输出文件
    today = date.today().isoformat()
    output_filename = f"{today}_news.txt"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# 锂电池隔膜行业新闻汇总\n")
        f.write(f"# 生成日期: {today}\n")
        f.write(f"# 共 {len(translated_items)} 条新闻\n")
        f.write("=" * 60 + "\n\n")
        
        for i, item in enumerate(translated_items, 1):
            f.write(_format_item(item, i))
    
    log_info(f"翻译完成，输出到: {output_path}")
    
    return output_path


def _format_item(item: NewsItem, index: int) -> str:
    """
    格式化单条新闻
    
    Args:
        item: NewsItem对象（已翻译）
        index: 序号
        
    Returns:
        格式化后的字符串
    """
    lines = []
    lines.append(f"[{index}]")
    
    # 标题
    title_cn = getattr(item, 'title_cn', '') or item.title
    lines.append(f"Title: {title_cn}")
    
    # 原始标题（如果翻译了）
    if hasattr(item, 'title_cn') and item.title_cn and item.title_cn != item.title:
        lines.append(f"Original Title: {item.title}")
    
    # 分数和命中关键词
    hits_str = ', '.join(item.score_hits) if item.score_hits else '-'
    lines.append(f"Score: {item.score} | {hits_str}")
    
    # URL
    lines.append(f"URL: {item.url}")
    
    # 日期
    date_str = item.date_parsed.isoformat() if item.date_parsed else "Unknown"
    if item.date_raw and item.date_raw != date_str:
        lines.append(f"Date: {date_str} (Raw: {item.date_raw})")
    else:
        lines.append(f"Date: {date_str}")
    
    # 摘要
    if item.teaser:
        teaser_cn = getattr(item, 'teaser_cn', '') or item.teaser
        lines.append(f"Teaser: {teaser_cn}")
    
    lines.append("-" * 40)
    lines.append("")
    
    return '\n'.join(lines)


class Translator:
    """翻译器类，支持Google Translate API"""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._translator = None
        
        # 尝试初始化翻译器
        if api_key and api_key != "YOUR_API_KEY_HERE":
            try:
                from google.cloud import translate_v2 as translate
                self._translator = translate.Client()
                print("    ✓ 使用 Google Cloud Translation API")
            except ImportError:
                print("    ⚠ google-cloud-translate 未安装，尝试使用 googletrans")
                self._init_googletrans()
            except Exception as e:
                print(f"    ⚠ Google Cloud API 初始化失败: {e}")
                self._init_googletrans()
        else:
            self._init_googletrans()
    
    def _init_googletrans(self):
        """初始化免费翻译库"""
        try:
            from googletrans import Translator as GoogleTranslator
            self._translator = GoogleTranslator()
            self._use_googletrans = True
            print("    ✓ 使用 googletrans 免费翻译")
        except ImportError:
            print("    ⚠ googletrans 未安装，将跳过翻译")
            self._translator = None
            self._use_googletrans = False
    
    def translate_items(self, items: List[NewsItem]) -> List[NewsItem]:
        """
        批量翻译新闻条目
        
        Args:
            items: NewsItem列表
            
        Returns:
            翻译后的NewsItem列表
        """
        if not self._translator:
            print("    ⚠ 翻译器未初始化，跳过翻译")
            return items
        
        total = len(items)
        translated_count = 0
        
        for i, item in enumerate(items):
            # 翻译标题
            if item.title and not _is_chinese(item.title):
                translated = self._translate_text(item.title)
                if translated:
                    item.title_cn = translated
                    translated_count += 1
            else:
                item.title_cn = item.title
            
            # 翻译摘要
            if item.teaser and not _is_chinese(item.teaser):
                translated = self._translate_text(item.teaser)
                if translated:
                    item.teaser_cn = translated
            else:
                item.teaser_cn = item.teaser
            
            # 进度显示
            if (i + 1) % 10 == 0 or (i + 1) == total:
                print(f"    翻译进度: {i + 1}/{total}")
            
            # 添加延迟避免API限流
            if hasattr(self, '_use_googletrans') and self._use_googletrans:
                time.sleep(0.5)
        
        print(f"    翻译完成: {translated_count}/{total} 条")
        return items
    
    def _translate_text(self, text: str) -> Optional[str]:
        """
        翻译单条文本
        
        Args:
            text: 原始文本
            
        Returns:
            翻译后的文本，失败返回None
        """
        if not text or not self._translator:
            return None
        
        try:
            if hasattr(self, '_use_googletrans') and self._use_googletrans:
                # 使用 googletrans
                result = self._translator.translate(text, dest='zh-cn')
                return result.text
            else:
                # 使用 Google Cloud API
                result = self._translator.translate(text, target_language='zh-CN')
                return result['translatedText']
        except Exception as e:
            # 翻译失败不影响整体流程
            return None


def _is_chinese(text: str) -> bool:
    """
    检测文本是否主要是中文
    
    Args:
        text: 文本字符串
        
    Returns:
        如果中文字符占比超过30%返回True
    """
    if not text:
        return False
    
    chinese_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(text.replace(' ', ''))
    
    if total_chars == 0:
        return False
    
    return chinese_count / total_chars > 0.3


def load_sorted_items() -> List[NewsItem]:
    """从临时文件加载排序后的数据"""
    sorted_file = os.path.join(TEMP_DIR, 'items_sorted.jsonl')
    items = []
    
    if os.path.exists(sorted_file):
        with open(sorted_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(NewsItem.from_json(line))
    
    return items

