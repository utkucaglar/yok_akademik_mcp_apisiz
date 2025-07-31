#!/usr/bin/env python3
"""
Debug Test - Scraping işlemini test et
"""

import asyncio
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Logging setup
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG level for more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_scraping():
    """Test scraping işlemi"""
    try:
        from src.tools.profile_scraper import ProfileScraperTool
        from src.utils.selenium_manager import SeleniumManager
        
        print("🔍 Testing scraping...")
        
        # Test Selenium manager first
        print("🔧 Testing Selenium Manager...")
        selenium_manager = SeleniumManager()
        
        async with selenium_manager.get_driver() as driver:
            print("✅ Driver created successfully")
            
            # Test navigation
            print("🌐 Testing navigation...")
            success = await selenium_manager.navigate_to_page(driver, "https://akademik.yok.gov.tr/AkademikArama/")
            print(f"✅ Navigation: {success}")
            
            if success:
                # Test element finding
                print("🔍 Testing element finding...")
                from selenium.webdriver.common.by import By
                search_box = await selenium_manager.wait_for_element(driver, By.ID, "aramaTerim")
                print(f"✅ Search box found: {search_box is not None}")
                
                if search_box:
                    # Test search
                    print("🔍 Testing search...")
                    search_box.clear()
                    search_box.send_keys("ahmet yılmaz")
                    print("✅ Search term entered")
                    
                    # Find and click search button
                    search_button = driver.find_element(By.ID, "searchButton")
                    search_button.click()
                    print("✅ Search button clicked")
                    
                    # Wait for results and click Akademisyenler
                    await asyncio.sleep(3)
                    print("⏳ Waited for results...")
                    
                    # Click Akademisyenler link
                    try:
                        akademisyenler_link = driver.find_element(By.LINK_TEXT, "Akademisyenler")
                        akademisyenler_link.click()
                        print("✅ Akademisyenler link clicked")
                        await asyncio.sleep(3)
                    except Exception as e:
                        print(f"❌ Akademisyenler link not found: {e}")
                    
                    print("⏳ Waited for Akademisyenler page...")
                    
                    # Check for profile rows
                    print("🔍 Looking for profile rows...")
                    profile_rows = driver.find_elements(By.CSS_SELECTOR, "tr[id^='authorInfo_']")
                    print(f"✅ Profile rows found: {len(profile_rows)}")
                    
                    if len(profile_rows) == 0:
                        print("⚠️ No profile rows found, trying alternative selectors...")
                        
                        # Try alternative selectors
                        all_rows = driver.find_elements(By.CSS_SELECTOR, "tr")
                        print(f"📊 Total rows: {len(all_rows)}")
                        
                        for i, row in enumerate(all_rows[:5]):  # Check first 5 rows
                            try:
                                row_id = row.get_attribute("id")
                                row_class = row.get_attribute("class")
                                print(f"Row {i}: id='{row_id}', class='{row_class}'")
                            except Exception as e:
                                print(f"Row {i}: Error getting attributes - {e}")
                    
                    # Get page source for debugging
                    page_source = driver.page_source
                    print(f"📄 Page source length: {len(page_source)}")
                    
                    # Save page source for inspection
                    with open("debug_page.html", "w", encoding="utf-8") as f:
                        f.write(page_source)
                    print("💾 Page source saved to debug_page.html")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_scraping())
    sys.exit(0 if success else 1) 