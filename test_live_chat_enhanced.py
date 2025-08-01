#!/usr/bin/env python3
"""
Enhanced test script for live scraper chat tool - Tests real-time data reading
"""

import asyncio
import json
import time
from src.tools.live_scraper_chat import live_scraper_chat

async def test_enhanced_live_chat():
    """Test the enhanced live scraper chat tool with real-time data reading"""
    
    # Test messages
    messages = [
        {"role": "user", "content": "Ali Yılmaz"}
    ]
    
    print("🔍 Testing enhanced live scraper chat tool...")
    print("=" * 70)
    print("Bu test, chat tool'unun gerçek zamanlı veri okuma özelliğini test eder")
    print("Scraping sırasında JSON dosyasından okunan veriler chat'te gösterilecek")
    print("=" * 70)
    
    try:
        start_time = time.time()
        response_count = 0
        
        # Chat tool'u çağır ve tüm response'ları al
        async for response in live_scraper_chat.handle_chat_request(messages, max_results=10):
            response_count += 1
            elapsed_time = time.time() - start_time
            
            print(f"⏱️  [{elapsed_time:.1f}s] Response #{response_count}:")
            print(f"📤 Content: {response.get('content', 'No content')}")
            print("-" * 60)
            
            # 15 response'dan sonra veya 120 saniye sonra dur
            if response_count >= 15 or elapsed_time > 120:
                print(f"✅ Test completed - {response_count} responses received in {elapsed_time:.1f}s")
                break
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting enhanced live chat test...")
    asyncio.run(test_enhanced_live_chat())
    print("\n🎉 Enhanced test completed!") 