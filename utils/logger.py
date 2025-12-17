"""
日志模块
提供日志记录和人工介入暂停功能
"""
import logging
import os
from datetime import datetime
from typing import Optional

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')

# 全局logger实例
_logger: Optional[logging.Logger] = None


def setup_logger() -> logging.Logger:
    """
    创建带时间戳的日志文件
    
    Returns:
        配置好的Logger实例
    """
    global _logger
    
    # 确保日志目录存在
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger('separator_crawler')
    logger.setLevel(logging.DEBUG)
    
    # 清除已有的handlers
    logger.handlers.clear()
    
    # 创建文件handler
    log_filename = datetime.now().strftime('%Y%m%d_%H%M%S') + '_crawler.log'
    log_filepath = os.path.join(LOG_DIR, log_filename)
    
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 创建控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建格式器
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter('%(message)s')
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # 添加handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    _logger = logger
    
    logger.info(f"日志文件: {log_filepath}")
    
    return logger


def get_logger() -> logging.Logger:
    """获取logger实例"""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


def log_info(message: str):
    """记录信息日志"""
    logger = get_logger()
    logger.info(message)


def log_debug(message: str):
    """记录调试日志"""
    logger = get_logger()
    logger.debug(message)


def log_warning(message: str):
    """记录警告日志"""
    logger = get_logger()
    logger.warning(message)


def log_error(code: str, message: str):
    """
    记录错误到控制台和日志
    
    Args:
        code: 错误代码（如 E001, E002）
        message: 错误信息
    """
    logger = get_logger()
    formatted_message = f"[{code}] {message}"
    logger.error(formatted_message)
    print(f"\n❌ 错误 {formatted_message}")


def pause_for_manual_fix(driver, reason: str, error_code: str = "E000") -> str:
    """
    暂停等待人工介入
    
    当检测到验证码或反爬时调用此函数，等待用户处理
    
    Args:
        driver: Selenium WebDriver实例
        reason: 暂停原因
        error_code: 错误代码
        
    Returns:
        'continue' - 用户输入C，继续执行（刷新页面重试）
        'continue_no_refresh' - 用户输入R，继续执行（不刷新，直接继续）
        'skip' - 用户输入P，跳过当前任务
    """
    logger = get_logger()
    
    print("\n" + "=" * 60)
    print(f"⚠️  检测到问题: {reason}")
    print(f"错误代码: {error_code}")
    print("=" * 60)
    print("\n请在浏览器中手动处理（如验证码、登录等）")
    print("\n处理完成后，请输入:")
    print("  C - 继续执行（刷新页面重试）")
    print("  R - 继续执行（不刷新，直接继续）")
    print("  P - 跳过当前任务")
    print("=" * 60)
    
    logger.warning(f"[{error_code}] 暂停等待人工介入: {reason}")
    
    while True:
        try:
            user_input = input("\n请输入选项 (C/R/P): ").strip().upper()
            
            if user_input == 'C':
                logger.info("用户选择继续执行（刷新页面）")
                print("\n✓ 继续执行，正在刷新页面...")
                return 'continue'
            elif user_input == 'R':
                logger.info("用户选择继续执行（不刷新）")
                print("\n✓ 继续执行，不刷新页面...")
                return 'continue_no_refresh'
            elif user_input == 'P':
                logger.info("用户选择跳过当前任务")
                print("\n→ 跳过当前任务")
                return 'skip'
            else:
                print("无效输入，请输入 C、R 或 P")
        except KeyboardInterrupt:
            print("\n用户中断")
            return 'skip'
        except EOFError:
            # 处理编码问题
            print("\n输入错误，请重试")
            continue


def log_task_start(task_id: str, url: str):
    """记录任务开始"""
    logger = get_logger()
    logger.info(f"任务开始: {task_id} | URL: {url[:80]}...")


def log_task_end(task_id: str, items_count: int, success: bool = True):
    """记录任务结束"""
    logger = get_logger()
    status = "成功" if success else "失败"
    logger.info(f"任务结束: {task_id} | 状态: {status} | 提取条目: {items_count}")


def log_extraction(parser_name: str, items_count: int):
    """记录数据提取"""
    logger = get_logger()
    logger.debug(f"数据提取: 解析器={parser_name}, 条目数={items_count}")


def log_filter_result(before: int, after: int, reason: str = ""):
    """记录筛选结果"""
    logger = get_logger()
    logger.info(f"筛选结果: {before} → {after} ({reason})")

