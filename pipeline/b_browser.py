"""
B模块：执行动作
打开网页，执行Selenium动作
"""
import time
from typing import Optional
from selenium import webdriver

from utils.models import CrawlTask
from utils.logger import log_error, pause_for_manual_fix, log_task_start
from engine.actions import (
    perform_wait,
    perform_scroll_by,
    perform_scroll_to_bottom,
    perform_click_all,
    perform_refresh,
    perform_navigate,
    check_for_captcha,
    check_for_block
)


def run(task: CrawlTask, driver: webdriver.Edge, config: dict = None) -> Optional[str]:
    """
    执行任务：打开网页，执行动作
    
    Args:
        task: 爬取任务
        driver: WebDriver实例
        config: 配置字典（可选）
        
    Returns:
        页面HTML字符串，或None（跳过）
    """
    log_task_start(task.task_id, task.url)
    
    # 获取配置
    max_retries = 3
    timeout = 30
    if config:
        max_retries = config.get('settings', {}).get('MAX_RETRIES', 3)
        timeout = config.get('settings', {}).get('BROWSER_TIMEOUT', 30)
    
    for attempt in range(max_retries):
        try:
            # 导航到URL
            success = perform_navigate(driver, task.url, timeout)
            
            if not success:
                print(f"    ⚠ 页面加载超时，尝试 {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    continue
            
            # 等待页面初始加载
            time.sleep(2)
            
            # 检测反爬
            if check_for_captcha(driver):
                action = pause_for_manual_fix(
                    driver,
                    "检测到验证码，请在浏览器中手动完成验证",
                    "E001"
                )
                if action == 'skip':
                    return None
                elif action == 'continue':
                    perform_refresh(driver)
                    time.sleep(3)
                    continue
            
            if check_for_block(driver):
                action = pause_for_manual_fix(
                    driver,
                    "检测到访问被阻止（403/429），请稍后重试",
                    "E002"
                )
                if action == 'skip':
                    return None
                elif action == 'continue':
                    time.sleep(5)
                    perform_refresh(driver)
                    time.sleep(3)
                    continue
            
            # 执行动作
            _execute_action(driver, task.action_name)
            
            # 获取页面源码
            html = driver.page_source
            
            if html and len(html) > 1000:  # 基本检查
                return html
            else:
                print(f"    ⚠ 页面内容过短，可能加载失败")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                    
        except Exception as e:
            log_error("E003", f"浏览器操作异常: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
    
    # 所有重试都失败
    print(f"    ❌ 任务失败: {task.url[:50]}...")
    return None


def _execute_action(driver: webdriver.Edge, action_name: str):
    """
    根据动作名称执行相应操作
    
    Args:
        driver: WebDriver实例
        action_name: 动作名称
    """
    action_name = action_name.upper().strip()
    
    if action_name == "WAIT":
        # 简单等待3秒
        perform_wait(driver, delay=3.0)
        
    elif action_name == "INFINITE_SCROLL":
        # 无限滚动：滚动5次，每次1000px，间隔0.7秒
        perform_scroll_by(driver, pixels=1000, times=5, delay=0.7)
        
    elif action_name == "SCROLL_TO_BOTTOM":
        # 滚动到底部
        perform_scroll_to_bottom(driver, max_scrolls=10, delay=1.0)
        
    elif action_name == "CLICK_EXPAND":
        # 点击展开按钮（常见的展开类选择器）
        expand_selectors = [
            "button.load-more",
            "a.load-more",
            "button.show-more",
            "a.show-more",
            "[data-load-more]",
            ".expand-button",
            ".see-more"
        ]
        for selector in expand_selectors:
            perform_click_all(driver, selector, delay=0.5)
            
    elif action_name.startswith("CLICK:"):
        # 自定义点击选择器 CLICK:selector
        selector = action_name[6:].strip()
        if selector:
            perform_click_all(driver, selector, delay=0.5)
            
    elif action_name.startswith("SCROLL:"):
        # 自定义滚动 SCROLL:pixels,times,delay
        params = action_name[7:].strip().split(',')
        try:
            pixels = int(params[0]) if len(params) > 0 else 1000
            times = int(params[1]) if len(params) > 1 else 5
            delay = float(params[2]) if len(params) > 2 else 0.7
            perform_scroll_by(driver, pixels=pixels, times=times, delay=delay)
        except ValueError:
            perform_scroll_by(driver)
            
    else:
        # 默认等待
        perform_wait(driver, delay=2.0)


def batch_run(tasks: list, driver: webdriver.Edge, config: dict = None) -> dict:
    """
    批量执行任务
    
    Args:
        tasks: CrawlTask列表
        driver: WebDriver实例
        config: 配置字典
        
    Returns:
        {task_id: html} 字典
    """
    results = {}
    
    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] 处理: {task.url[:60]}...")
        html = run(task, driver, config)
        if html:
            results[task.task_id] = html
    
    return results

