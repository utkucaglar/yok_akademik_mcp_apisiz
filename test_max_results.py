#!/usr/bin/env python3
"""
Test script for maximum results - Tests with higher max_results parameter
"""

import asyncio
import json
import time
from src.tools.live_scraper_chat import live_scraper_chat

async def test_max_results():
    """Test with higher max_results to get more profiles"""
    
    # Test messages
    messages = [
        {"role": "user", "content": "Nurettin"}
    ]
    
    print("🚀 Starting max results test...")
    print("🔍 Testing with higher max_results...")
    print("=" * 70)
    print("Bu test, daha fazla sonuç almak için max_results=100 kullanır")
    print("Tüm profilleri görmek için daha uzun süre bekleyecek")
    print("=" * 70)
    
    try:
        start_time = time.time()
        response_count = 0
        total_profiles = 0
        
        # Chat tool'u çağır ve tüm response'ları al
        async for response in live_scraper_chat.handle_chat_request(messages, max_results=100):
            response_count += 1
            elapsed_time = time.time() - start_time
            
            print(f"⏱️  [{elapsed_time:.1f}s] Response #{response_count}:")
            print(f"📤 Content: {response.get('content', 'No content')}")
            print("-" * 60)
            
            # Profil sayısını çıkar
            content = response.get('content', '')
            if 'Toplam:' in content:
                try:
                    # "Toplam: X profil" formatından sayıyı çıkar
                    total_line = [line for line in content.split('\n') if 'Toplam:' in line][0]
                    total_profiles = int(total_line.split('Toplam:')[1].split('profil')[0].strip())
                except:
                    pass
            
            # İlk 50 response'u göster, sonra dur
            if response_count >= 50:
                print(f"✅ Test completed - {response_count} responses received in {elapsed_time:.1f}s")
                print(f"📊 Total profiles found: {total_profiles}")
                break
                
    except asyncio.CancelledError:
        print("✅ Test cancelled by user")
    except KeyboardInterrupt:
        print("✅ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
    
    print("🎉 Max results test completed!")

if __name__ == "__main__":
    asyncio.run(test_max_results()) 