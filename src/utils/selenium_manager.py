import asyncio
import logging
from typing import Optional
from selenium import webdriver  # Normal Selenium kullan (uyumluluk için)
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
        """Yeni Chrome WebDriver oluştur (Selenium-Wire ile)"""
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Performans optimizasyonları - Smithery için hızlandırıldı
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.javascript": 1,  # JS aktif
            "profile.managed_default_content_settings.plugins": 2,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.notifications": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        logger.info("Creating Chrome driver...")
        
        try:
            driver = webdriver.Chrome(options=options)
            logger.info("Successfully created Chrome driver")
        except Exception as e:
            logger.error(f"Driver creation failed: {e}")
            raise e
        
        driver.set_window_size(1920, 1080)
        return driver
    
    async def get_driver(self):
        """WebDriver al"""
        driver = self._create_driver()
        return driver
    
    async def close_driver(self, driver: webdriver.Chrome):
        """WebDriver'ı kapat"""
        try:
            driver.quit()
        except Exception as e:
            logger.warning(f"Driver kapatılırken hata: {e}")
    
    async def navigate_to_page(self, driver: webdriver.Chrome, url: str, timeout: int = 10):
        """Sayfaya git ve yüklenmeyi bekle"""
        try:
            driver.get(url)
            await asyncio.sleep(0.5)  # Sayfa yüklenme beklemesi çok kısaltıldı
            return True
        except Exception as e:
            logger.error(f"Sayfa yüklenemedi {url}: {e}")
            return False
    
    async def wait_for_element(self, driver: webdriver.Chrome, by: By, value: str, timeout: int = 2):
        """Element için bekle ve element'i döndür"""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logger.error(f"Element bulunamadı {by}={value}: {e}")
            return None
    
    async def wait_for_clickable(self, driver: webdriver.Chrome, by: By, value: str, timeout: int = 2):
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
    
    def get_network_requests(self, driver: webdriver.Chrome, url_filter: str = None):
        """Network isteklerini al (simüle edilmiş)"""
        try:
            # Normal Selenium'da network monitoring yok, boş liste döndür
            logger.info("Network monitoring simüle ediliyor")
            return []
        except Exception as e:
            logger.error(f"Network requests alınamadı: {e}")
            return []
    
    def get_last_request(self, driver: webdriver.Chrome, url_filter: str = None):
        """Son network isteğini al (simüle edilmiş)"""
        try:
            requests = self.get_network_requests(driver, url_filter)
            if requests:
                return requests[-1]  # Son istek
            return None
        except Exception as e:
            logger.error(f"Last request alınamadı: {e}")
            return None
    
    def clear_network_requests(self, driver: webdriver.Chrome):
        """Network isteklerini temizle (simüle edilmiş)"""
        try:
            logger.info("Network requests temizlendi (simüle)")
        except Exception as e:
            logger.error(f"Network requests temizlenemedi: {e}") 