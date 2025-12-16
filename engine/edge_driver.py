"""
Edge浏览器驱动管理模块
负责创建和管理Edge WebDriver实例
"""
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import WebDriverException
import os


def create_driver(headless: bool = False, timeout: int = 30) -> webdriver.Edge:
    """
    创建Edge浏览器实例
    
    Args:
        headless: 是否使用无头模式（默认False，显示浏览器窗口）
        timeout: 页面加载超时时间（秒）
        
    Returns:
        配置好的Edge WebDriver实例
    """
    options = Options()
    
    # 基础配置
    options.add_argument('--start-maximized')  # 最大化窗口
    options.add_argument('--disable-notifications')  # 禁用通知
    options.add_argument('--disable-popup-blocking')  # 禁用弹窗拦截
    options.add_argument('--disable-infobars')  # 禁用信息栏
    
    # 反检测配置
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 性能优化
    options.add_argument('--disable-gpu')  # 禁用GPU加速（避免某些环境问题）
    options.add_argument('--no-sandbox')  # 禁用沙箱（Linux环境可能需要）
    options.add_argument('--disable-dev-shm-usage')  # 禁用/dev/shm使用
    
    # 无头模式
    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
    
    # 设置User-Agent
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    )
    
    try:
        # 创建WebDriver
        driver = webdriver.Edge(options=options)
        
        # 设置超时
        driver.set_page_load_timeout(timeout)
        driver.implicitly_wait(10)  # 隐式等待
        
        # 执行CDP命令隐藏webdriver特征
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
        print("✓ Edge浏览器启动成功")
        return driver
        
    except WebDriverException as e:
        print(f"❌ Edge浏览器启动失败: {e}")
        raise


def close_driver(driver: webdriver.Edge):
    """
    安全关闭浏览器
    
    Args:
        driver: WebDriver实例
    """
    if driver:
        try:
            driver.quit()
            print("✓ 浏览器已关闭")
        except Exception as e:
            print(f"⚠ 关闭浏览器时出错: {e}")


def get_current_url(driver: webdriver.Edge) -> str:
    """获取当前页面URL"""
    try:
        return driver.current_url
    except Exception:
        return ""


def get_page_source(driver: webdriver.Edge) -> str:
    """获取当前页面HTML源码"""
    try:
        return driver.page_source
    except Exception:
        return ""


def take_screenshot(driver: webdriver.Edge, filename: str = None) -> str:
    """
    截取当前页面截图
    
    Args:
        driver: WebDriver实例
        filename: 可选的文件名（默认使用时间戳）
        
    Returns:
        截图文件路径
    """
    if filename is None:
        from datetime import datetime
        filename = datetime.now().strftime('%Y%m%d_%H%M%S') + '_screenshot.png'
    
    # 确保目录存在
    screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp', 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    
    filepath = os.path.join(screenshot_dir, filename)
    
    try:
        driver.save_screenshot(filepath)
        return filepath
    except Exception as e:
        print(f"截图失败: {e}")
        return ""

