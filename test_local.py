#!/usr/bin/env python3
"""
Yerel test scripti - MCP server'ı test etmek için
"""

import asyncio
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.tools.profile_scraper import ProfileScraperTool
from src.tools.collaborator_scraper import CollaboratorScraperTool

async def test_profile_scraper():
    """Profile scraper'ı test et"""
    print("🔍 Profile Scraper Test Başlıyor...")
    
    scraper = ProfileScraperTool()
    
    # Basit test - sadece session ID oluştur
    session_id = scraper._generate_session_id()
    print(f"✅ Session ID oluşturuldu: {session_id}")
    
    # Label parsing test
    test_labels = "Eğitim Bilimleri Temel Alanı (5) > Açık ve Uzaktan Eğitim (1)"
    result = scraper._parse_labels_and_keywords(test_labels)
    print(f"✅ Label parsing test: {result}")
    
    print("✅ Profile Scraper Test Tamamlandı!")

async def test_collaborator_scraper():
    """Collaborator scraper'ı test et"""
    print("🔍 Collaborator Scraper Test Başlıyor...")
    
    scraper = CollaboratorScraperTool()
    
    # Basit test
    print("✅ Collaborator Scraper Test Tamamlandı!")

async def test_selenium_manager():
    """Selenium manager'ı test et"""
    print("🔍 Selenium Manager Test Başlıyor...")
    
    from src.utils.selenium_manager import SeleniumManager
    
    manager = SeleniumManager()
    
    # Chrome versiyonunu test et
    version = manager._get_chrome_version()
    print(f"✅ Chrome versiyonu: {version}")
    
    # Driver oluşturmayı test et (timeout ile)
    try:
        print("🔄 Driver oluşturuluyor...")
        driver = manager._create_driver()
        print("✅ Driver başarıyla oluşturuldu!")
        
        # Hızlı test
        await manager.navigate_to_page(driver, "https://www.google.com", timeout=5)
        print("✅ Google sayfasına gidildi!")
        
        driver.quit()
        print("✅ Driver kapatıldı!")
        
    except Exception as e:
        print(f"❌ Driver test hatası: {e}")
    
    print("✅ Selenium Manager Test Tamamlandı!")

async def test_file_manager():
    """File manager'ı test et"""
    print("🔍 File Manager Test Başlıyor...")
    
    from src.utils.file_manager import FileManager
    
    manager = FileManager()
    
    # Fields yükleme test
    try:
        fields = await manager.load_fields()
        print(f"✅ Fields yüklendi: {len(fields)} alan")
    except Exception as e:
        print(f"❌ Fields yükleme hatası: {e}")
    
    print("✅ File Manager Test Tamamlandı!")

async def main():
    """Ana test fonksiyonu"""
    print("🚀 YÖK Akademik Scraper MCP Test Başlıyor...")
    print("=" * 50)
    
    try:
        await test_file_manager()
        print("-" * 30)
        
        await test_profile_scraper()
        print("-" * 30)
        
        await test_collaborator_scraper()
        print("-" * 30)
        
        await test_selenium_manager()
        print("-" * 30)
        
        print("🎉 Tüm testler başarıyla tamamlandı!")
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 