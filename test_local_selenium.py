#!/usr/bin/env python3
"""
Local Selenium test - Gerçek web scraping testi
"""

import asyncio
import json
import logging
import time
from src.tools.profile_scraper import ProfileScraperTool
from src.utils.selenium_manager import SeleniumManager

# Logging ayarla
logging.basicConfig(level=logging.INFO)

async def test_selenium_basic():
    """Selenium temel testi"""
    print("=== Selenium Temel Test ===")
    
    try:
        selenium_manager = SeleniumManager()
        print("✅ SeleniumManager oluşturuldu")
        
        # Driver oluştur
        print("1. Chrome driver oluşturuluyor...")
        async with selenium_manager.get_driver() as driver:
            print("✅ Driver başarıyla oluşturuldu")
            
            # Basit sayfa testi
            print("2. Basit sayfa testi...")
            success = await selenium_manager.navigate_to_page(driver, "https://www.google.com")
            if success:
                print("✅ Google sayfası yüklendi")
                print(f"✅ Sayfa başlığı: {driver.title}")
            else:
                print("❌ Google sayfası yüklenemedi")
                return False
        
        print("✅ Selenium temel testi başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ Selenium test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_yok_website():
    """YÖK website testi"""
    print("=== YÖK Website Test ===")
    
    try:
        selenium_manager = SeleniumManager()
        
        async with selenium_manager.get_driver() as driver:
            print("1. YÖK website'ine gidiliyor...")
            success = await selenium_manager.navigate_to_page(driver, "https://akademik.yok.gov.tr/")
            
            if success:
                print("✅ YÖK website yüklendi")
                print(f"✅ Sayfa başlığı: {driver.title}")
                
                # Çerez butonu var mı kontrol et
                try:
                    cookie_button = driver.find_element("xpath", "//button[contains(text(),'Tümünü Kabul Et')]")
                    print("✅ Çerez butonu bulundu")
                except:
                    print("ℹ️ Çerez butonu bulunamadı (normal)")
                
                # Arama formu var mı kontrol et
                try:
                    search_input = driver.find_element("name", "q")
                    print("✅ Arama input'u bulundu")
                except:
                    print("❌ Arama input'u bulunamadı")
                
            else:
                print("❌ YÖK website yüklenemedi")
                return False
        
        print("✅ YÖK website testi başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ YÖK website test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_profile_scraper():
    """Profile scraper testi"""
    print("=== Profile Scraper Test ===")
    
    try:
        scraper = ProfileScraperTool()
        
        # Basit arama testi
        print("1. 'ahmet yılmaz' araması yapılıyor...")
        start_time = time.time()
        
        result = await scraper.search_profiles(name="ahmet yılmaz")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Arama tamamlandı ({duration:.2f} saniye)")
        print(f"✅ Sonuç: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get("status") == "completed":
            profiles = result.get("profiles", [])
            print(f"✅ {len(profiles)} profil bulundu")
            return True
        else:
            print(f"❌ Arama başarısız: {result.get('error', 'Bilinmeyen hata')}")
            return False
        
    except Exception as e:
        print(f"❌ Profile scraper test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Local Selenium test başlatılıyor...")
    print("Bu test gerçek web scraping yapacak!")
    
    async def main():
        print("\n" + "="*50)
        result1 = await test_selenium_basic()
        
        print("\n" + "="*50)
        result2 = await test_yok_website()
        
        print("\n" + "="*50)
        result3 = await test_profile_scraper()
        
        print("\n" + "="*50)
        if result1 and result2 and result3:
            print("🎉 Tüm testler başarılı! Kod localde çalışıyor.")
        else:
            print("❌ Bazı testler başarısız!")
    
    asyncio.run(main()) 