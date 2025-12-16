"""
Selenium动作库模块
提供各种浏览器操作动作
"""
import time
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)


def perform_wait(driver: webdriver.Edge, delay: float = 3.0):
    """
    简单等待
    
    Args:
        driver: WebDriver实例
        delay: 等待时间（秒）
    """
    time.sleep(delay)


def perform_scroll_by(driver: webdriver.Edge, pixels: int = 1000, times: int = 5, delay: float = 0.7):
    """
    滚动加载更多内容
    
    Args:
        driver: WebDriver实例
        pixels: 每次滚动的像素数
        times: 滚动次数
        delay: 每次滚动后的等待时间（秒）
    """
    for i in range(times):
        driver.execute_script(f"window.scrollBy(0, {pixels});")
        time.sleep(delay)
        
        # 检查是否到达页面底部
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        scroll_top = driver.execute_script("return window.pageYOffset + window.innerHeight")
        
        if scroll_top >= scroll_height:
            # 已到达底部，提前结束
            break


def perform_scroll_to_bottom(driver: webdriver.Edge, max_scrolls: int = 10, delay: float = 1.0):
    """
    滚动到页面底部（用于无限滚动页面）
    
    Args:
        driver: WebDriver实例
        max_scrolls: 最大滚动次数
        delay: 每次滚动后的等待时间（秒）
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for _ in range(max_scrolls):
        # 滚动到底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)
        
        # 获取新的页面高度
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            # 页面高度未变化，可能已加载完成
            break
        
        last_height = new_height


def perform_click_all(driver: webdriver.Edge, selector: str, delay: float = 0.5, by: str = "css"):
    """
    批量点击所有匹配的元素（用于展开更多内容）
    
    Args:
        driver: WebDriver实例
        selector: 选择器
        delay: 每次点击后的等待时间（秒）
        by: 选择器类型 ("css", "xpath")
    """
    locator = By.CSS_SELECTOR if by == "css" else By.XPATH
    
    try:
        elements = driver.find_elements(locator, selector)
        
        for element in elements:
            try:
                # 滚动到元素可见
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.2)
                
                # 尝试点击
                element.click()
                time.sleep(delay)
                
            except (ElementClickInterceptedException, StaleElementReferenceException):
                # 如果普通点击失败，尝试JavaScript点击
                try:
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(delay)
                except Exception:
                    continue
            except Exception:
                continue
                
    except NoSuchElementException:
        pass


def perform_click_element(driver: webdriver.Edge, selector: str, by: str = "css", 
                          timeout: int = 10) -> bool:
    """
    点击单个元素
    
    Args:
        driver: WebDriver实例
        selector: 选择器
        by: 选择器类型 ("css", "xpath")
        timeout: 等待超时时间（秒）
        
    Returns:
        点击成功返回True，失败返回False
    """
    locator = By.CSS_SELECTOR if by == "css" else By.XPATH
    
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.element_to_be_clickable((locator, selector)))
        element.click()
        return True
    except (TimeoutException, NoSuchElementException):
        return False
    except ElementClickInterceptedException:
        # 尝试JavaScript点击
        try:
            element = driver.find_element(locator, selector)
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            return False


def perform_refresh(driver: webdriver.Edge):
    """
    刷新页面
    
    Args:
        driver: WebDriver实例
    """
    driver.refresh()


def perform_navigate(driver: webdriver.Edge, url: str, timeout: int = 30) -> bool:
    """
    导航到指定URL
    
    Args:
        driver: WebDriver实例
        url: 目标URL
        timeout: 页面加载超时时间（秒）
        
    Returns:
        导航成功返回True，超时返回False
    """
    try:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        return True
    except TimeoutException:
        print(f"⚠ 页面加载超时: {url[:60]}...")
        # 停止加载
        driver.execute_script("window.stop();")
        return False


def wait_for_element(driver: webdriver.Edge, selector: str, by: str = "css", 
                     timeout: int = 10) -> bool:
    """
    等待元素出现
    
    Args:
        driver: WebDriver实例
        selector: 选择器
        by: 选择器类型 ("css", "xpath")
        timeout: 等待超时时间（秒）
        
    Returns:
        元素出现返回True，超时返回False
    """
    locator = By.CSS_SELECTOR if by == "css" else By.XPATH
    
    try:
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_element_located((locator, selector)))
        return True
    except TimeoutException:
        return False


def check_for_captcha(driver: webdriver.Edge) -> bool:
    """
    检测页面是否存在验证码
    
    Args:
        driver: WebDriver实例
        
    Returns:
        检测到验证码返回True
    """
    # 常见验证码特征
    captcha_indicators = [
        # Google reCAPTCHA
        'g-recaptcha',
        'recaptcha',
        # hCaptcha
        'h-captcha',
        'hcaptcha',
        # Cloudflare
        'cf-turnstile',
        'challenge-form',
        # 通用关键词
        'captcha',
        'verify',
        'robot',
        'human'
    ]
    
    page_source = driver.page_source.lower()
    
    for indicator in captcha_indicators:
        if indicator in page_source:
            # 进一步确认是否真的是验证码页面
            if 'please verify' in page_source or 'are you a robot' in page_source:
                return True
            if 'captcha' in page_source and ('solve' in page_source or 'verify' in page_source):
                return True
    
    return False


def check_for_block(driver: webdriver.Edge) -> bool:
    """
    检测页面是否被反爬封锁
    
    Args:
        driver: WebDriver实例
        
    Returns:
        检测到封锁返回True
    """
    block_indicators = [
        'access denied',
        'forbidden',
        '403',
        'blocked',
        'rate limit',
        'too many requests',
        '429'
    ]
    
    page_source = driver.page_source.lower()
    page_title = driver.title.lower()
    
    for indicator in block_indicators:
        if indicator in page_source or indicator in page_title:
            return True
    
    return False


def input_text(driver: webdriver.Edge, selector: str, text: str, by: str = "css",
               clear_first: bool = True, submit: bool = False) -> bool:
    """
    在输入框中输入文本
    
    Args:
        driver: WebDriver实例
        selector: 选择器
        text: 要输入的文本
        by: 选择器类型 ("css", "xpath")
        clear_first: 是否先清空输入框
        submit: 是否在输入后按回车提交
        
    Returns:
        输入成功返回True
    """
    locator = By.CSS_SELECTOR if by == "css" else By.XPATH
    
    try:
        element = driver.find_element(locator, selector)
        
        if clear_first:
            element.clear()
        
        element.send_keys(text)
        
        if submit:
            element.send_keys(Keys.RETURN)
        
        return True
    except Exception:
        return False

