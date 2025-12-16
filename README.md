# Separator Crawler v3.0

锂电池隔膜行业国际新闻爬虫系统

## 功能特点

- 🌐 支持多个新闻网站爬取
- 🔍 灵活的关键词搜索配置
- 📊 智能打分筛选机制
- 🌍 Google Translate API 翻译支持
- 🖥️ 基于 Selenium Edge 的浏览器自动化
- ⏸️ 人工介入暂停机制（验证码处理）

## 目录结构

```
Separator_Crawler_v3/
├── main.py                    # 主入口
├── config/
│   ├── keyword_sets.json      # 搜索关键词配置
│   ├── scoring_keywords.json  # 打分关键词配置
│   ├── date_formats.json      # 网站日期格式映射
│   ├── parsers.json           # 网站解析规则配置
│   └── settings.json          # 全局设置
├── pipeline/
│   ├── a_prepare.py           # A模块：读取Excel，生成搜索任务
│   ├── b_browser.py           # B模块：打开网页，执行动作
│   ├── c_extract.py           # C模块：读取数据，分配UUID
│   ├── d_filter.py            # D模块：日期+打分筛选
│   ├── e_sort.py              # E模块：去重和排序
│   └── f_translate.py         # F模块：Google翻译
├── engine/
│   ├── edge_driver.py         # Edge浏览器驱动管理
│   └── actions.py             # Selenium动作库
├── utils/
│   ├── config_loader.py       # 配置加载器
│   ├── date_parser.py         # 日期解析器
│   ├── logger.py              # 审计日志
│   └── models.py              # 数据模型定义
├── temp/                      # 临时文件目录
├── output/                    # 最终输出目录
└── log/                       # 日志目录
```

## 安装

1. 确保已安装 Python 3.11+

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 确保已安装 Microsoft Edge 浏览器（WebDriver 会自动下载）

## 配置

### 1. Excel 控制台

创建 `国际隔膜信息源.xlsx` 文件，包含以下列：

| Base_URL | Is_Enabled | Parser_Name | Action_Name | Search_Name | Filter_Name | Engine |
|----------|------------|-------------|-------------|-------------|-------------|--------|

- **Base_URL**: 目标URL，可包含 `Separator` 占位符
- **Is_Enabled**: TRUE/FALSE，是否启用
- **Parser_Name**: 解析器名称（对应 parsers.json）
- **Action_Name**: 动作类型（WAIT/INFINITE_SCROLL/CLICK_EXPAND）
- **Search_Name**: 关键词集名称（对应 keyword_sets.json）
- **Filter_Name**: 筛选器名称（保留字段）
- **Engine**: 浏览器类型（默认 edge）

### 2. 全局设置 (config/settings.json)

```json
{
  "MINIMUM_DATE_TO_KEEP": "2025-12-6",
  "BYPASS_KEYWORD_SCORING": false,
  "PASS_SCORE_THRESHOLD": 80,
  "GOOGLE_TRANSLATE_API_KEY": "YOUR_API_KEY_HERE"
}
```

### 3. 翻译配置

**方案1**: 使用 Google Cloud Translation API
- 设置 `GOOGLE_TRANSLATE_API_KEY`
- 安装 `google-cloud-translate`

**方案2**: 使用免费翻译库（推荐）
- 保持 API Key 为空
- 默认使用 `googletrans`

## 使用

```bash
python main.py
```

## 数据流

```
Excel控制台 + JSON配置
        ↓
    [A模块] 准备任务 → temp/tasks.jsonl
        ↓
    [B模块] 打开网页执行动作 → 返回页面对象
        ↓
    [C模块] 提取数据 → temp/items_raw.jsonl
        ↓
    [D模块] 筛选数据 → temp/items_filtered.jsonl
        ↓
    [E模块] 去重排序 → temp/items_sorted.jsonl
        ↓
    [F模块] 翻译输出 → output/YYYY-MM-DD_news.txt
```

## 人工介入

当检测到验证码或反爬时，程序会暂停并提示：
- 输入 `C` 继续执行（刷新页面重试）
- 输入 `P` 跳过当前任务

## 输出格式

```
Title: [翻译后标题]
Original Title: [原始标题]
Score: [分数] | [命中关键词]
URL: [链接]
Date: [YYYY-MM-DD格式日期] (Raw: [原始日期])
Teaser: [翻译后摘要]
--------------------
```

## 许可证

MIT License

