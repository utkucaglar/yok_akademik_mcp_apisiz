#!/usr/bin/env python3
"""
Debug test script - timeout sorununu tespit etmek için
"""

import asyncio
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_selenium_manager():
    """Selenium manager'ı test et"""
    print("🔍 Selenium Manager Test Başlıyor...")
    
    try:
        from src.utils.selenium_manager import SeleniumManager
        
        manager = SeleniumManager()
        
        print("🔄 Driver oluşturuluyor...")
        start_time = time.time()
        
        async with manager.get_driver() as driver:
            elapsed = time.time() - start_time
            print(f"✅ Driver başarıyla oluşturuldu! ({elapsed:.2f} saniye)")
            
            # Basit test
            print("🔄 Google sayfasına gidiliyor...")
            success = await manager.navigate_to_page(driver, "https://www.google.com", timeout=10)
            
            if success:
                print("✅ Google sayfasına başarıyla gidildi!")
            else:
                print("❌ Google sayfasına gidilemedi!")
        
        return True
        
    except Exception as e:
        print(f"❌ Selenium Manager test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_profile_scraper_basic():
    """Profile scraper'ın temel fonksiyonlarını test et"""
    print("🔍 Profile Scraper Basic Test Başlıyor...")
    
    try:
        from src.tools.profile_scraper import ProfileScraperTool
        
        scraper = ProfileScraperTool()
        
        # Session ID test
        session_id = scraper._generate_session_id()
        print(f"✅ Session ID: {session_id}")
        
        # Label parsing test
        test_labels = "Eğitim Bilimleri Temel Alanı (5) > Açık ve Uzaktan Eğitim (1)"
        result = scraper._parse_labels_and_keywords(test_labels)
        print(f"✅ Label parsing: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Profile Scraper basic test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_file_manager():
    """File manager'ı test et"""
    print("🔍 File Manager Test Başlıyor...")
    
    try:
        from src.utils.file_manager import FileManager
        
        manager = FileManager()
        
        # Fields yükleme
        fields = await manager.load_fields()
        print(f"✅ Fields yüklendi: {len(fields)} alan")
        
        # Field name lookup
        field_name = manager.get_field_name_by_id(5)
        print(f"✅ Field ID 5: {field_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ File Manager test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Ana test fonksiyonu"""
    print("=" * 50)
    print("YÖK Akademik Scraper MCP - Debug Test")
    print("=" * 50)
    
    # Temel testler
    file_success = await test_file_manager()
    print("-" * 30)
    
    profile_basic_success = await test_profile_scraper_basic()
    print("-" * 30)
    
    # Selenium test (en son)
    selenium_success = await test_selenium_manager()
    print("-" * 30)
    
    print("\n" + "=" * 50)
    if file_success and profile_basic_success and selenium_success:
        print("🎉 Tüm testler başarılı!")
    else:
        print("❌ Bazı testler başarısız.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 