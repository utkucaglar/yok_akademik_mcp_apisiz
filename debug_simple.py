#!/usr/bin/env python3
"""
Basit debug script - Selenium olmadan test
"""

import asyncio
import json
import logging
from src.tools.profile_scraper import ProfileScraperTool
from src.utils.file_manager import FileManager

# Logging ayarla
logging.basicConfig(level=logging.INFO)

async def test_basic_functionality():
    """Temel fonksiyonları test et"""
    print("=== Basit Debug Test ===")
    
    try:
        # File Manager test
        print("1. File Manager test...")
        file_manager = FileManager()
        fields_data = await file_manager.load_fields()
        print(f"✅ Fields yüklendi: {len(fields_data)} alan")
        
        # Profile Scraper test (Selenium olmadan)
        print("2. Profile Scraper test...")
        scraper = ProfileScraperTool()
        
        # Session ID oluştur
        session_id = scraper._generate_session_id()
        print(f"✅ Session ID oluşturuldu: {session_id}")
        
        # Fields test
        field_name = file_manager.get_field_name_by_id(1)
        print(f"✅ Alan ID 1 -> {field_name}")
        
        print("✅ Tüm temel testler başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_server_import():
    """Server import test"""
    print("3. Server import test...")
    try:
        from src.server import server, handle_list_tools
        print("✅ Server import başarılı")
        
        # Tool listesi test
        tools = await handle_list_tools()
        print(f"✅ {len(tools)} tool bulundu")
        
        return True
    except Exception as e:
        print(f"❌ Server import hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Basit debug başlatılıyor...")
    
    async def main():
        result1 = await test_basic_functionality()
        result2 = await test_server_import()
        
        if result1 and result2:
            print("\n🎉 Tüm testler başarılı! Kod temel olarak çalışıyor.")
        else:
            print("\n❌ Bazı testler başarısız!")
    
    asyncio.run(main()) 