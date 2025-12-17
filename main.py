"""
Separator Crawler v3.0 主入口
锂电池隔膜行业国际新闻爬虫系统
"""
import os
import sys
import shutil
from datetime import datetime

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    # 设置标准输出编码为UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from pipeline import a_prepare, b_browser, c_extract, d_filter, e_sort, f_translate
from engine.edge_driver import create_driver, close_driver
from utils.config_loader import ConfigLoader
from utils.logger import setup_logger, log_info

# 目录配置
TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
LOG_DIR = os.path.join(PROJECT_ROOT, 'log')


def setup_directories():
    """创建临时目录和输出目录"""
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 清空临时目录中的旧数据文件
    for filename in ['items_raw.jsonl', 'items_filtered.jsonl', 'items_sorted.jsonl']:
        filepath = os.path.join(TEMP_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)


def cleanup_temp_files():
    """清理临时文件"""
    try:
        # 只删除数据文件，保留目录结构
        for filename in os.listdir(TEMP_DIR):
            if filename.endswith('.jsonl'):
                os.remove(os.path.join(TEMP_DIR, filename))
        print("\n✓ 临时文件已清理")
    except Exception as e:
        print(f"\n⚠ 清理临时文件失败: {e}")


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          Separator Crawler v3.0                          ║
║          锂电池隔膜行业新闻爬虫系统                          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
    print(banner)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目目录: {PROJECT_ROOT}")
    print("=" * 60)


def main():
    """主函数"""
    print_banner()
    
    driver = None
    
    try:
        # 初始化
        print("\n【初始化】")
        setup_directories()
        config = ConfigLoader.load_all()
        logger = setup_logger()
        
        # 显示配置信息
        settings = config.get('settings', {})
        print(f"  • 最小保留日期: {settings.get('MINIMUM_DATE_TO_KEEP', '未设置')}")
        print(f"  • 通过分数阈值: {settings.get('PASS_SCORE_THRESHOLD', 80)}")
        print(f"  • 跳过关键词评分: {settings.get('BYPASS_KEYWORD_SCORING', False)}")
        
        # ========== Step A: 准备任务 ==========
        print("\n" + "=" * 60)
        print("【Step A】准备搜索任务")
        print("=" * 60)
        
        tasks = a_prepare.run(config)
        
        if not tasks:
            print("\n❌ 没有生成任何任务，请检查Excel配置文件")
            return
        
        print(f"\n✓ 共生成 {len(tasks)} 个爬取任务")
        
        # ========== Step B+C: 执行任务并提取数据 ==========
        print("\n" + "=" * 60)
        print("【Step B+C】执行任务并提取数据")
        print("=" * 60)
        
        driver = create_driver()
        total_items = 0
        success_count = 0
        
        for i, task in enumerate(tasks, 1):
            print(f"\n[{i}/{len(tasks)}] 处理任务")
            print(f"  URL: {task.url[:70]}...")
            print(f"  解析器: {task.parser_name}")
            print(f"  动作: {task.action_name}")
            
            html = b_browser.run(task, driver, config)
            
            if html:
                items = c_extract.run(html, task, config)
                total_items += len(items)
                success_count += 1
                print(f"  ✓ 提取到 {len(items)} 条数据")
            else:
                print(f"  ✗ 任务跳过或失败")
        
        close_driver(driver)
        driver = None
        
        print(f"\n{'─' * 40}")
        print(f"任务执行统计:")
        print(f"  • 成功: {success_count}/{len(tasks)}")
        print(f"  • 原始数据: {total_items} 条")
        
        if total_items == 0:
            print("\n⚠ 未提取到任何数据，流程结束")
            return
        
        # ========== Step D: 筛选 ==========
        print("\n" + "=" * 60)
        print("【Step D】筛选数据")
        print("=" * 60)
        
        filtered_count = d_filter.run(config)
        print(f"\n✓ 筛选后保留 {filtered_count} 条")
        
        if filtered_count == 0:
            print("\n⚠ 筛选后没有数据，流程结束")
            return
        
        # ========== Step E: 排序 ==========
        print("\n" + "=" * 60)
        print("【Step E】去重排序")
        print("=" * 60)
        
        final_count = e_sort.run()
        print(f"\n✓ 去重后剩余 {final_count} 条")
        
        # ========== Step F: 翻译 ==========
        print("\n" + "=" * 60)
        print("【Step F】翻译输出")
        print("=" * 60)
        
        output_file = f_translate.run(config)
        
        if output_file:
            print(f"\n✓ 输出文件: {output_file}")
        
        # ========== 完成 ==========
        print("\n" + "=" * 60)
        print("【完成】爬虫流程全部完成!")
        print("=" * 60)
        
        print(f"\n📊 最终统计:")
        print(f"  • 执行任务: {len(tasks)} 个")
        print(f"  • 原始数据: {total_items} 条")
        print(f"  • 筛选后: {filtered_count} 条")
        print(f"  • 最终输出: {final_count} 条")
        
        log_info(f"爬虫完成: 任务{len(tasks)}, 原始{total_items}, 筛选{filtered_count}, 输出{final_count}")
        
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断 (Ctrl+C)")
        log_info("用户中断执行")
        
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        # 确保浏览器关闭
        if driver:
            try:
                close_driver(driver)
            except:
                pass
        
        # 清理临时文件（可选）
        # cleanup_temp_files()


def run_single_task(url: str, parser_name: str, action_name: str = "WAIT"):
    """
    运行单个任务（用于测试）
    
    Args:
        url: 目标URL
        parser_name: 解析器名称
        action_name: 动作名称
    """
    from utils.models import CrawlTask
    import uuid
    
    print(f"单任务测试: {url}")
    
    config = ConfigLoader.load_all()
    
    task = CrawlTask(
        task_id=uuid.uuid4().hex[:8],
        url=url,
        parser_name=parser_name,
        action_name=action_name,
        filter_name=""
    )
    
    driver = create_driver()
    
    try:
        html = b_browser.run(task, driver, config)
        if html:
            items = c_extract.run(html, task, config)
            print(f"提取到 {len(items)} 条数据")
            for item in items[:5]:
                print(f"  - {item.title[:50]}...")
        else:
            print("任务失败")
    finally:
        close_driver(driver)


if __name__ == "__main__":
    main()
    input("\n按 Enter 键退出...")

