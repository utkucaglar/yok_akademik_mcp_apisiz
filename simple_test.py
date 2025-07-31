#!/usr/bin/env python3
"""
Basit test scripti - Selenium olmadan temel fonksiyonları test et
"""

import asyncio
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_basic_functionality():
    """Temel fonksiyonları test et"""
    print("🚀 Basit Test Başlıyor...")
    
    try:
        # File manager test
        from src.utils.file_manager import FileManager
        file_manager = FileManager()
        
        # Fields yükleme
        fields = await file_manager.load_fields()
        print(f"✅ Fields yüklendi: {len(fields)} alan")
        
        # Field name lookup
        field_name = file_manager.get_field_name_by_id(5)
        print(f"✅ Field ID 5: {field_name}")
        
        # Session directory
        session_dir = file_manager.get_session_dir("test_session")
        print(f"✅ Session directory: {session_dir}")
        
        # Profile scraper basic test
        from src.tools.profile_scraper import ProfileScraperTool
        profile_scraper = ProfileScraperTool()
        
        # Session ID generation
        session_id = profile_scraper._generate_session_id()
        print(f"✅ Session ID: {session_id}")
        
        # Label parsing
        test_labels = "Eğitim Bilimleri Temel Alanı (5) > Açık ve Uzaktan Eğitim (1)"
        result = profile_scraper._parse_labels_and_keywords(test_labels)
        print(f"✅ Label parsing: {result}")
        
        # Collaborator scraper basic test
        from src.tools.collaborator_scraper import CollaboratorScraperTool
        collaborator_scraper = CollaboratorScraperTool()
        print("✅ Collaborator scraper oluşturuldu")
        
        print("🎉 Tüm temel testler başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mcp_server():
    """MCP server'ı test et"""
    print("\n🔍 MCP Server Test Başlıyor...")
    
    try:
        from src.server import server
        
        # Tools listesi
        tools_func = server.list_tools()
        tools = await tools_func()
        print(f"✅ Tools listesi: {len(tools)} tool")
        
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        print("✅ MCP Server test başarılı!")
        return True
        
    except Exception as e:
        print(f"❌ MCP Server test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Ana test fonksiyonu"""
    print("=" * 50)
    print("YÖK Akademik Scraper MCP - Basit Test")
    print("=" * 50)
    
    # Temel fonksiyonlar test
    basic_success = await test_basic_functionality()
    
    # MCP server test
    mcp_success = await test_mcp_server()
    
    print("\n" + "=" * 50)
    if basic_success and mcp_success:
        print("🎉 Tüm testler başarılı! MCP server hazır.")
    else:
        print("❌ Bazı testler başarısız. Lütfen hataları kontrol edin.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 