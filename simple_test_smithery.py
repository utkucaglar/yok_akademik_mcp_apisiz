#!/usr/bin/env python3
"""
Simple test script for Smithery - minimal functionality test
"""

import asyncio
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_basic_functionality():
    """Test basic functionality without Selenium"""
    print("🔍 Basic Functionality Test Starting...")
    
    try:
        # Test file manager
        from src.utils.file_manager import FileManager
        file_manager = FileManager()
        
        # Load fields
        fields = await file_manager.load_fields()
        print(f"✅ Fields loaded: {len(fields)} fields")
        
        # Test field lookup
        field_name = file_manager.get_field_name_by_id(5)
        print(f"✅ Field ID 5: {field_name}")
        
        # Test session ID generation
        from src.tools.profile_scraper import ProfileScraperTool
        scraper = ProfileScraperTool()
        session_id = scraper._generate_session_id()
        print(f"✅ Session ID generated: {session_id}")
        
        return {
            "status": "success",
            "message": "Basic functionality test passed",
            "fields_count": len(fields),
            "session_id": session_id
        }
        
    except Exception as e:
        print(f"❌ Basic test error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }

async def main():
    """Main test function"""
    print("=" * 50)
    print("YÖK Akademik Scraper MCP - Simple Smithery Test")
    print("=" * 50)
    
    result = await test_basic_functionality()
    
    print("\n" + "=" * 50)
    if result["status"] == "success":
        print("🎉 Test successful!")
        print(f"📊 Result: {result}")
    else:
        print("❌ Test failed.")
        print(f"📊 Error: {result}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 