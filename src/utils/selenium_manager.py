import asyncio
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import subprocess
import os
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class SeleniumManager:
    """Asenkron Selenium WebDriver yöneticisi"""
    
    def __init__(self):
        self._driver: Optional[webdriver.Chrome] = None
        self._driver_pool = []
        self._max_pool_size = 3
        
    def _get_chrome_version(self) -> str:
        """Chrome versiyonunu al"""
        try:
            # Linux'ta Chrome versiyonunu al
            result = subprocess.run(['google-chrome', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1]
                return version
        except Exception:
            pass
        
        try:
            # Chromium versiyonunu al
            result = subprocess.run(['chromium', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1]
                return version
        except Exception:
            pass
        
        return "latest"  # Fallback
    
    def _create_driver(self) -> webdriver.Chrome:
        """Yeni Chrome WebDriver oluştur"""
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Performans optimizasyonları
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.fonts": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Chrome versiyonunu al ve uyumlu ChromeDriver kullan
        chrome_version = self._get_chrome_version()
        logger.info(f"Detected Chrome version: {chrome_version}")
        
        try:
            # Selenium 4.16+ ile otomatik ChromeDriver kullan
            driver = webdriver.Chrome(options=options)
            logger.info("Successfully created driver with automatic ChromeDriver")
        except Exception as e:
            logger.warning(f"Automatic ChromeDriver failed: {e}")
            try:
                # Önce Chrome versiyonuna uygun ChromeDriver dene
                service = Service(ChromeDriverManager(version=chrome_version).install())
                driver = webdriver.Chrome(service=service, options=options)
                logger.info(f"Successfully created driver with ChromeDriver for version {chrome_version}")
            except Exception as e2:
                logger.warning(f"ChromeDriver for version {chrome_version} failed: {e2}")
                try:
                    # Latest versiyonu dene
                    service = Service(ChromeDriverManager(version="latest").install())
                    driver = webdriver.Chrome(service=service, options=options)
                    logger.info("Successfully created driver with latest ChromeDriver")
                except Exception as e3:
                    logger.warning(f"Latest ChromeDriver failed: {e3}")
                    # Son çare olarak stable versiyon
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                    logger.info("Successfully created driver with stable ChromeDriver")
        
        driver.set_window_size(1920, 1080)
        return driver
    
    @asynccontextmanager
    async def get_driver(self):
        """Asenkron context manager ile WebDriver al"""
        driver = self._create_driver()
        try:
            yield driver
        finally:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Driver kapatılırken hata: {e}")
    
    async def navigate_to_page(self, driver: webdriver.Chrome, url: str, timeout: int = 10):
        """Sayfaya git ve yüklenmeyi bekle"""
        try:
            driver.get(url)
            await asyncio.sleep(2)  # Sayfa yüklenme beklemesi
            return True
        except Exception as e:
            logger.error(f"Sayfa yüklenemedi {url}: {e}")
            return False
    
    async def wait_for_element(self, driver: webdriver.Chrome, by: By, value: str, timeout: int = 10):
        """Element için bekle"""
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except Exception as e:
            logger.error(f"Element bulunamadı {by}={value}: {e}")
            return False
    
    async def wait_for_clickable(self, driver: webdriver.Chrome, by: By, value: str, timeout: int = 10):
        """Tıklanabilir element için bekle"""
        try:
            WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return True
        except Exception as e:
            logger.error(f"Tıklanabilir element bulunamadı {by}={value}: {e}")
            return False
    
    async def handle_cookies(self, driver: webdriver.Chrome):
        """Çerez onayını dene"""
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Tümünü Kabul Et')]"))
            )
            cookie_button.click()
            logger.debug("Çerez onaylandı")
            return True
        except Exception:
            logger.debug("Çerez butonu bulunamadı")
            return False
    
    async def execute_script_safe(self, driver: webdriver.Chrome, script: str):
        """JavaScript'i güvenli şekilde çalıştır"""
        try:
            return driver.execute_script(script)
        except Exception as e:
            logger.error(f"JavaScript çalıştırılamadı: {e}")
            return None 