import asyncio
import re
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..models.schemas import SearchRequest, AcademicProfile, SessionStatus
from ..utils.selenium_manager import SeleniumManager
from ..utils.file_manager import FileManager
from ..utils.stream_manager import stream_manager


logger = logging.getLogger(__name__)

class ProfileScraperTool:
    """Akademisyen profil scraper tool'u"""
    
    def __init__(self):
        self.selenium_manager = SeleniumManager()
        self.file_manager = FileManager()
        self.base_url = "https://akademik.yok.gov.tr/"
        self.default_photo_url = "/default_photo.jpg"
    
    def _generate_session_id(self) -> str:
        """Benzersiz session ID oluştur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{unique_id}"
    
    def _parse_labels_and_keywords(self, line: str) -> tuple[str, str, List[str]]:
        """Label ve keyword'leri ayır"""
        parts = [p.strip() for p in line.split(';')]
        left = parts[0] if parts else ''
        rest_keywords = [p.strip() for p in parts[1:] if p.strip()]
        left_parts = re.split(r'\s{2,}|\t+', left)
        green_label = left_parts[0].strip() if len(left_parts) > 0 else '-'
        blue_label = left_parts[1].strip() if len(left_parts) > 1 else '-'
        keywords = []
        if len(left_parts) > 2:
            keywords += [p.strip() for p in left_parts[2:] if p.strip()]
        keywords += rest_keywords
        if not keywords:
            keywords = ['-']
        return green_label, blue_label, keywords
    
    async def search_profiles(self, **kwargs) -> Dict[str, Any]:
        """Akademisyen profillerini ara - Stream version"""
        try:
            logger.info(f"Search profiles başlatıldı: {kwargs}")
            # Request'i doğrula
            request = SearchRequest(**kwargs)
            
            # Session ID oluştur
            session_id = self._generate_session_id()
            logger.info(f"Yeni session başlatıldı: {session_id}")
            
            # Stream başlat
            await stream_manager.start_streaming(session_id, self._stream_callback)
            
            # Fields verilerini yükle
            fields_data = await self.file_manager.load_fields()
            
            # Filtreleme parametrelerini hazırla
            selected_field = None
            selected_specialties = []
            
            if request.field_id:
                field_name = self.file_manager.get_field_name_by_id(request.field_id)
                if field_name:
                    selected_field = field_name
                    logger.info(f"Alan ID {request.field_id} -> '{field_name}' olarak ayarlandı")
                else:
                    logger.warning(f"Alan ID {request.field_id} bulunamadı!")
            
            if request.specialty_ids and request.field_id:
                specialty_ids = [int(s.strip()) for s in request.specialty_ids.split(',')]
                for specialty_id in specialty_ids:
                    specialty_name = self.file_manager.get_specialty_name_by_id(
                        fields_data, request.field_id, specialty_id
                    )
                    if specialty_name:
                        selected_specialties.append(specialty_name)
                        logger.info(f"Uzmanlık ID {specialty_id} -> '{specialty_name}' olarak ayarlandı")
                    else:
                        logger.warning(f"Uzmanlık ID {specialty_id} bulunamadı!")
            
            # Background task olarak scraping başlat
            asyncio.create_task(self._async_scrape_profiles(
                request, session_id, selected_field, selected_specialties
            ))
            
                            return {
                    "session_id": session_id,
                    "status": "streaming",
                    "message": "Scraping başlatıldı, sonuçlar stream olarak gelecek"
                }
                
        except Exception as e:
            logger.error(f"Profil arama hatası: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _stream_callback(self, message: Dict[str, Any]):
        """Stream callback - real-time updates"""
        logger.info(f"Stream update: {message}")
        # Bu callback MCP server'a real-time updates gönderecek
    
    async def _async_scrape_profiles(self, request: SearchRequest, session_id: str, 
                                   selected_field: Optional[str], selected_specialties: List[str]):
        """Async scraping işlemi"""
        try:
            await stream_manager.update_session_status(session_id, "scraping_started")
            
            # WebDriver ile scraping başlat
            logger.info("WebDriver oluşturuluyor...")
            async with self.selenium_manager.get_driver() as driver:
                logger.info("WebDriver başarıyla oluşturuldu, scraping başlıyor...")
                await stream_manager.update_session_status(session_id, "driver_ready")
                
                profiles = await self._scrape_profiles(
                    driver, request, session_id, selected_field, selected_specialties
                )
                
                # Sonuçları kaydet
                await self.file_manager.save_profiles(session_id, profiles)
                await self.file_manager.mark_session_complete(session_id, "main")
                
                await stream_manager.update_session_status(session_id, "completed", {
                    "total_count": len(profiles),
                    "profiles": profiles
                })
                
        except Exception as e:
            logger.error(f"Async scraping hatası: {e}")
            await stream_manager.update_session_status(session_id, "failed", {
                "error": str(e)
            })
    
    async def _scrape_profiles(
        self, 
        driver, 
        request: SearchRequest, 
        session_id: str,
        selected_field: Optional[str],
        selected_specialties: List[str]
    ) -> List[Dict[str, Any]]:
        """Profil scraping işlemi"""
        profiles = []
        profile_urls = set()
        profile_id_counter = 1
        page_num = 1
        
        try:
            # Ana sayfaya git
            logger.info("YÖK ana sayfasına gidiliyor...")
            await self.selenium_manager.navigate_to_page(driver, self.base_url + "AkademikArama/")
            
            # Arama kutusunu bekle
            logger.info("Arama kutusu bekleniyor...")
            if not await self.selenium_manager.wait_for_element(driver, By.ID, "aramaTerim"):
                raise Exception("Arama kutusu bulunamadı")
            logger.info("Arama kutusu bulundu!")
            
            # Çerez onayını dene
            await self.selenium_manager.handle_cookies(driver)
            
            # Arama yap
            logger.info(f"Arama yapılıyor: {request.name}")
            search_box = driver.find_element(By.ID, "aramaTerim")
            search_box.send_keys(request.name)
            driver.find_element(By.ID, "searchButton").click()
            logger.info("Arama butonu tıklandı!")
            
            # Akademisyenler sekmesine geç
            if not await self.selenium_manager.wait_for_clickable(driver, By.LINK_TEXT, "Akademisyenler"):
                raise Exception("Akademisyenler sekmesi bulunamadı")
            
            driver.find_element(By.LINK_TEXT, "Akademisyenler").click()
            
            # Profil satırlarını topla
            while True:
                logger.info(f"{page_num}. sayfa yükleniyor...")
                
                if not await self.selenium_manager.wait_for_element(driver, By.CSS_SELECTOR, "tr[id^='authorInfo_']"):
                    logger.info("Profil satırları yüklenemedi, döngü bitiyor")
                    break
                
                profile_rows = driver.find_elements(By.CSS_SELECTOR, "tr[id^='authorInfo_']")
                logger.info(f"{page_num}. sayfada {len(profile_rows)} profil bulundu")
                
                if len(profile_rows) == 0:
                    logger.info("Profil bulunamadı, döngü bitiyor")
                    break
                
                for row in profile_rows:
                    try:
                        profile = await self._extract_profile_data(
                            row, profile_id_counter, selected_field, selected_specialties
                        )
                        
                        if profile:
                            url = profile["url"]
                            if url in profile_urls:
                                logger.info(f"Profil zaten eklenmiş: {url}")
                                continue
                            
                            profiles.append(profile)
                            profile_urls.add(url)
                            profile_id_counter += 1
                            
                            logger.info(f"Profil eklendi: {profile['name']} - {url}")
                            
                            # Email kontrolü
                            if request.email and profile.get('email', '').lower() == request.email.lower():
                                logger.info(f"Email eşleşmesi bulundu: {profile['name']} - {profile['email']}")
                                return profiles
                            
                            # Limit kontrolü
                            if len(profiles) >= request.max_results:
                                logger.info(f"Maksimum sonuç sayısına ulaşıldı: {len(profiles)}")
                                return profiles
                    
                    except Exception as e:
                        logger.error(f"Profil satırı işlenemedi: {e}")
                
                # Sonraki sayfaya geç
                if not await self._go_to_next_page(driver, page_num):
                    break
                
                page_num += 1
                
                # Smithery için sadece ilk 3 sonuç
                if len(profiles) >= 3:
                    break
                
                # Hızlı scraping için sadece ilk sayfa
                if page_num > 1:
                    break
            
            return profiles
            
        except Exception as e:
            logger.error(f"Scraping hatası: {e}")
            return profiles
    
    async def _extract_profile_data(
        self, 
        row, 
        profile_id: int, 
        selected_field: Optional[str],
        selected_specialties: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Profil verilerini çıkar"""
        try:
            info_td = row.find_element(By.XPATH, "./td[h6]")
            
            # Label'ları çek
            all_links = info_td.find_elements(By.CSS_SELECTOR, 'a.anahtarKelime')
            green_label = all_links[0].text.strip() if len(all_links) > 0 else ''
            blue_label = all_links[1].text.strip() if len(all_links) > 1 else ''
            
            # Filtreleme
            if selected_field and green_label != selected_field:
                return None
            if selected_specialties and blue_label not in selected_specialties:
                return None
            
            # Link ve URL
            link = row.find_element(By.CSS_SELECTOR, "a")
            link_text = link.text.strip()
            url = link.get_attribute("href")
            
            # Fotoğraf
            img = row.find_element(By.CSS_SELECTOR, "img")
            img_src = img.get_attribute("src") if img else None
            if not img_src:
                img_src = self.default_photo_url
            
            # Bilgileri ayır
            info = info_td.text.strip() if info_td else ""
            info_lines = info.splitlines()
            
            if len(info_lines) > 1:
                title = info_lines[0].strip()
                name = info_lines[1].strip()
            else:
                title = link_text
                name = link_text
            
            header = info_lines[2].strip() if len(info_lines) > 2 else ''
            
            # Keywords
            label_text = f"{green_label}   {blue_label}"
            keywords_text = info_td.text.replace(label_text, '').strip()
            keywords_text = keywords_text.lstrip(';:,. \u000b\n\t')
            lines = [l.strip() for l in keywords_text.split('\n') if l.strip()]
            
            if lines:
                keywords_line = lines[-1]
                if header.strip() == keywords_line or header.strip() in keywords_line:
                    keywords_str = ""
                else:
                    keywords = [k.strip() for k in keywords_line.split(';') if k.strip()]
                    keywords_str = " ; ".join(keywords) if keywords else ""
            else:
                keywords_str = ""
            
            # Email
            email = ''
            try:
                email_link = row.find_element(By.CSS_SELECTOR, "a[href^='mailto']")
                email = email_link.text.strip().replace('[at]', '@')
            except Exception:
                email = ''
            
            return {
                "id": profile_id,
                "name": name,
                "title": title,
                "url": url,
                "info": info,
                "photoUrl": img_src,
                "header": header,
                "green_label": green_label,
                "blue_label": blue_label,
                "keywords": keywords_str,
                "email": email
            }
            
        except Exception as e:
            logger.error(f"Profil verisi çıkarılamadı: {e}")
            return None
    
    async def _go_to_next_page(self, driver, page_num: int) -> bool:
        """Sonraki sayfaya geç"""
        try:
            pagination = driver.find_element(By.CSS_SELECTOR, "ul.pagination")
            active_li = pagination.find_element(By.CSS_SELECTOR, "li.active")
            all_lis = pagination.find_elements(By.TAG_NAME, "li")
            active_index = all_lis.index(active_li)
            
            if active_index == len(all_lis) - 1:
                logger.info("Son sayfaya gelindi")
                return False
            
            next_li = all_lis[active_index + 1]
            next_a = next_li.find_element(By.TAG_NAME, "a")
            logger.info(f"{page_num+1}. sayfaya geçiliyor...")
            next_a.click()
            
            # Sayfa yüklenmesini bekle
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            logger.info(f"Sonraki sayfa bulunamadı: {e}")
            return False
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Session durumunu kontrol et"""
        return await self.file_manager.get_session_status(session_id) 