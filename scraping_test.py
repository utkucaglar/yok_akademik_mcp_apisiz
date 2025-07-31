#!/usr/bin/env python3
"""
Scraping test script - gerçek scraping işlemini test etmek için
"""

import asyncio
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_scraping_process():
    """Gerçek scraping işlemini test et"""
    print("🔍 Scraping Process Test Başlıyor...")
    
    try:
        from src.tools.profile_scraper import ProfileScraperTool
        
        scraper = ProfileScraperTool()
        
        print("🔄 Scraping başlatılıyor...")
        start_time = time.time()
        
        # Basit bir arama yap
        result = await scraper.search_profiles(
            name="ahmet",
            max_results=5
        )
        
        elapsed = time.time() - start_time
        print(f"✅ Scraping tamamlandı! ({elapsed:.2f} saniye)")
        print(f"📊 Sonuç: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scraping test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_navigation_only():
    """Sadece navigasyon test et"""
    print("🔍 Navigation Only Test Başlıyor...")
    
    try:
        from src.utils.selenium_manager import SeleniumManager
        
        manager = SeleniumManager()
        
        print("🔄 YÖK sayfasına gidiliyor...")
        start_time = time.time()
        
        async with manager.get_driver() as driver:
            # Ana sayfaya git
            success = await manager.navigate_to_page(driver, "https://akademik.yok.gov.tr/AkademikArama/")
            
            if success:
                elapsed = time.time() - start_time
                print(f"✅ YÖK sayfasına başarıyla gidildi! ({elapsed:.2f} saniye)")
                
                from selenium.webdriver.common.by import By
                
                # Arama kutusunu bekle
                print("🔄 Arama kutusu bekleniyor...")
                if await manager.wait_for_element(driver, By.ID, "aramaTerim", timeout=10):
                    print("✅ Arama kutusu bulundu!")
                else:
                    print("❌ Arama kutusu bulunamadı!")
            else:
                print("❌ YÖK sayfasına gidilemedi!")
        
        return True
        
    except Exception as e:
        print(f"❌ Navigation test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Ana test fonksiyonu"""
    print("=" * 50)
    print("YÖK Akademik Scraper MCP - Scraping Test")
    print("=" * 50)
    
    # Önce sadece navigasyon test et
    nav_success = await test_navigation_only()
    print("-" * 30)
    
    # Sonra tam scraping test et
    if nav_success:
        scraping_success = await test_scraping_process()
    else:
        print("❌ Navigation başarısız, scraping test edilmiyor")
        scraping_success = False
    
    print("\n" + "=" * 50)
    if nav_success and scraping_success:
        print("🎉 Tüm testler başarılı!")
    else:
        print("❌ Bazı testler başarısız.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 