#!/usr/bin/env python3
"""
Full test script for live scraper chat tool - Tests complete streaming
"""

import asyncio
import json
import time
from src.tools.live_scraper_chat import live_scraper_chat

async def test_full_live_chat():
    """Test the complete live scraper chat tool with streaming"""
    
    # Test messages
    messages = [
        {"role": "user", "content": "Mehmet Özkan"}
    ]
    
    print("🔍 Testing complete live scraper chat tool...")
    print("=" * 60)
    print("Bu test, chat tool'unun tam streaming özelliğini test eder")
    print("Scraping işlemi arka planda başlayacak ve progress updates gelecek")
    print("=" * 60)
    
    try:
        start_time = time.time()
        response_count = 0
        
        # Chat tool'u çağır ve tüm response'ları al
        async for response in live_scraper_chat.handle_chat_request(messages, max_results=5):
            response_count += 1
            elapsed_time = time.time() - start_time
            
            print(f"⏱️  [{elapsed_time:.1f}s] Response #{response_count}:")
            print(f"📤 Content: {response.get('content', 'No content')}")
            print("-" * 50)
            
            # 10 response'dan sonra veya 60 saniye sonra dur
            if response_count >= 10 or elapsed_time > 60:
                print(f"✅ Test completed - {response_count} responses received in {elapsed_time:.1f}s")
                break
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_error_handling():
    """Test error handling"""
    
    print("\n🧪 Testing error handling...")
    print("=" * 40)
    
    # Boş mesaj testi
    messages = []
    
    try:
        async for response in live_scraper_chat.handle_chat_request(messages):
            print(f"📤 Error response: {response.get('content', 'No content')}")
            break
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting comprehensive live chat test...")
    
    # Ana test
    asyncio.run(test_full_live_chat())
    
    # Hata testi
    asyncio.run(test_error_handling())
    
    print("\n🎉 All tests completed!") 