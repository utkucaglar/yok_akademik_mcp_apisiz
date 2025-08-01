#!/usr/bin/env python3
"""
Test script for live scraper chat tool
"""

import asyncio
import json
from src.tools.live_scraper_chat import live_scraper_chat

async def test_live_chat():
    """Test the live scraper chat tool"""
    
    # Test messages
    messages = [
        {"role": "user", "content": "Ahmet Yılmaz"}
    ]
    
    print("🔍 Testing live scraper chat tool...")
    print("=" * 50)
    
    try:
        # Chat tool'u çağır ve tüm response'ları al
        response_count = 0
        async for response in live_scraper_chat.handle_chat_request(messages, max_results=10):
            response_count += 1
            print(f"📤 Response #{response_count}: {json.dumps(response, ensure_ascii=False, indent=2)}")
            print("-" * 30)
            
            # İlk 3 response'dan sonra dur (test için)
            if response_count >= 3:
                print("✅ Test completed - First 3 responses received")
                break
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_live_chat()) 