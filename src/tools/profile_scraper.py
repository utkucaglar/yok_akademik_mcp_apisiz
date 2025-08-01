import asyncio
import re
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import string

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
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        session_id = f"session_{timestamp}_{random_suffix}"
        # Clean the session ID to remove any whitespace or newline characters
        return session_id.strip()
    
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
            logger.info(f"Async scraping başlatıldı: {session_id}")
            logger.info(f"Request: {request.name}, field: {selected_field}, specialties: {selected_specialties}")
            
            # WebDriver ile scraping başlat
            logger.info("WebDriver oluşturuluyor...")
            driver = await self.selenium_manager.get_driver()
            logger.info("WebDriver başarıyla oluşturuldu, scraping başlıyor...")
            
            try:
                profiles = await self._scrape_profiles(
                    driver, request, session_id, selected_field, selected_specialties
                )
                
                logger.info(f"Scraping tamamlandı: {len(profiles)} profil bulundu")
                
                # Sonuçları kaydet
                save_success = await self.file_manager.save_profiles(session_id, profiles)
                if save_success:
                    logger.info(f"Profil verileri kaydedildi: {len(profiles)} profil")
                    
                    # JSON dosyasına completed ekle
                    final_data = {
                        "profiles": profiles,
                        "completed": True,
                        "total_count": len(profiles),
                        "session_id": session_id,
                        "completed_at": datetime.now().isoformat()
                    }
                    
                    # Tamamlanmış veriyi kaydet
                    await self.file_manager.save_completed_profiles(session_id, final_data)
                    
                    # Sadece profil bulunduysa session'ı tamamlandı olarak işaretle
                    if len(profiles) > 0:
                        await self.file_manager.mark_session_complete(session_id, "main")
                        logger.info("Session tamamlandı olarak işaretlendi")
                    else:
                        logger.warning("Hiç profil bulunamadı, session tamamlanmadı")
                else:
                    logger.error("Profil verileri kaydedilemedi!")
            finally:
                # Driver'ı kapat
                await self.selenium_manager.close_driver(driver)
                
        except Exception as e:
            logger.error(f"Async scraping hatası: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Hata durumunda session'ı işaretleme
    
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
            success = await self.selenium_manager.navigate_to_page(driver, self.base_url + "AkademikArama/")
            if not success:
                raise Exception("Ana sayfa yüklenemedi")
            logger.info("Ana sayfa yüklendi")
            
            # Arama kutusunu bekle
            logger.info("Arama kutusu bekleniyor...")
            search_box = await self.selenium_manager.wait_for_element(driver, By.ID, "aramaTerim")
            if not search_box:
                raise Exception("Arama kutusu bulunamadı")
            logger.info("Arama kutusu bulundu!")
            
            # Çerez onayını dene
            await self.selenium_manager.handle_cookies(driver)
            
            # Arama yap
            logger.info(f"Arama yapılıyor: {request.name}")
            search_box = driver.find_element(By.ID, "aramaTerim")
            search_box.clear()
            search_box.send_keys(request.name)
            logger.info("Arama terimi girildi")
            
            search_button = driver.find_element(By.ID, "searchButton")
            search_button.click()
            logger.info("Arama butonu tıklandı!")
            
            # Hemen Akademisyenler sekmesini bekle ve tıkla
            try:
                # Önce sayfanın yüklenmesini bekle
                await asyncio.sleep(3)
                
                # Akademisyenler linkini farklı yöntemlerle bul
                akademisyenler_link = None
                
                # Yöntem 1: Link text ile
                try:
                    akademisyenler_link = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.LINK_TEXT, "Akademisyenler"))
                    )
                except:
                    pass
                
                # Yöntem 2: Partial text ile
                if not akademisyenler_link:
                    try:
                        akademisyenler_link = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Akademisyen"))
                        )
                    except:
                        pass
                
                # Yöntem 3: CSS selector ile
                if not akademisyenler_link:
                    try:
                        akademisyenler_link = driver.find_element(By.CSS_SELECTOR, "a[href*='akademisyen']")
                    except:
                        pass
                
                if akademisyenler_link:
                    akademisyenler_link.click()
                    logger.info("Akademisyenler sekmesine geçildi")
                    await asyncio.sleep(2)
                else:
                    logger.warning("Akademisyenler sekmesi bulunamadı, mevcut sayfada devam ediliyor")
                    
            except Exception as e:
                logger.error(f"Akademisyenler sekmesi hatası: {e}")
                # Sekme bulunamazsa devam et
            
            # Profil satırlarını topla
            profiles = []
            profile_urls = set()
            page_num = 1
            profile_id_counter = 1
            while True:
                logger.info(f"{page_num}. sayfa yükleniyor...")
                
                # Sayfa yüklenmesini bekle
                await asyncio.sleep(2)
                
                # Profil satırlarını farklı yöntemlerle bul
                profile_rows = []
                
                # Yöntem 1: authorInfo_ ile başlayan ID'ler
                try:
                    WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "tr[id^='authorInfo_']"))
                    )
                    profile_rows = driver.find_elements(By.CSS_SELECTOR, "tr[id^='authorInfo_']")
                except Exception as e:
                    logger.warning(f"authorInfo_ profilleri bulunamadı: {e}")
                
                # Yöntem 2: Tablo satırları
                if not profile_rows:
                    try:
                        profile_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                        # Boş satırları filtrele
                        profile_rows = [row for row in profile_rows if row.find_elements(By.CSS_SELECTOR, "td")]
                    except Exception as e:
                        logger.warning(f"Tablo satırları bulunamadı: {e}")
                
                # Yöntem 3: Link içeren satırlar
                if not profile_rows:
                    try:
                        profile_rows = driver.find_elements(By.CSS_SELECTOR, "tr:has(a)")
                    except Exception as e:
                        logger.warning(f"Link içeren satırlar bulunamadı: {e}")
                
                logger.info(f"{page_num}. sayfada {len(profile_rows)} profil bulundu")
                
                if len(profile_rows) == 0:
                    logger.info("Profil bulunamadı, döngü bitiyor")
                    break
                for row in profile_rows:
                    try:
                        info_td = row.find_element(By.XPATH, "./td[h6]")
                        all_links = info_td.find_elements(By.CSS_SELECTOR, 'a.anahtarKelime')
                        green_label = all_links[0].text.strip() if len(all_links) > 0 else ''
                        blue_label = all_links[1].text.strip() if len(all_links) > 1 else ''
                        if selected_field and green_label != selected_field:
                            continue
                        if selected_specialties and blue_label not in selected_specialties:
                            continue
                        link = row.find_element(By.CSS_SELECTOR, "a")
                        link_text = link.text.strip()
                        url = link.get_attribute("href")
                        if url in profile_urls:
                            logger.info(f"Profil zaten eklenmiş: {url}")
                            continue
                        info = info_td.text.strip() if info_td else ""
                        img = row.find_element(By.CSS_SELECTOR, "img")
                        img_src = img.get_attribute("src") if img else None
                        if not img_src:
                            img_src = self.default_photo_url
                        info_lines = info.splitlines()
                        if len(info_lines) > 1:
                            title = info_lines[0].strip()
                            name = info_lines[1].strip()
                        else:
                            title = link_text
                            name = link_text
                        header = info_lines[2].strip() if len(info_lines) > 2 else ''
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
                        email = ''
                        try:
                            email_link = row.find_element(By.CSS_SELECTOR, "a[href^='mailto']")
                            email = email_link.text.strip().replace('[at]', '@')
                        except Exception:
                            email = ''
                        profiles.append({
                            "id": profile_id_counter,
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
                        })
                        profile_id_counter += 1
                        profile_urls.add(url)
                        logger.info(f"Profil eklendi: {name} - {url}")
                        
                        # Her profil bulunduğunda dosyayı güncelle (real-time streaming için)
                        await self.file_manager.save_profiles(session_id, profiles)
                        
                        # Streaming update
                        if stream_manager:
                            await stream_manager._send_update(session_id, {
                                "type": "profiles",
                                "session_id": session_id,
                                "data": profiles,
                                "count": len(profiles),
                                "status": "profiles_updated"
                            })
                        if len(profiles) >= request.max_results:
                            logger.info(f"Maksimum sonuç sayısına ulaşıldı: {len(profiles)}")
                            return profiles
                    except Exception as e:
                        logger.error(f"Profil satırı işlenemedi: {e}")
                # Pagination: aktif sayfa <li> elementinden sonra gelen <a>'ya tıkla
                try:
                    pagination = driver.find_element(By.CSS_SELECTOR, "ul.pagination")
                    active_li = pagination.find_element(By.CSS_SELECTOR, "li.active")
                    all_lis = pagination.find_elements(By.TAG_NAME, "li")
                    active_index = all_lis.index(active_li)
                    if active_index == len(all_lis) - 1:
                        logger.info("Son sayfaya gelindi, döngü bitiyor.")
                        break
                    next_li = all_lis[active_index + 1]
                    next_a = next_li.find_element(By.TAG_NAME, "a")
                    logger.info(f"{page_num+1}. sayfaya geçiliyor...")
                    next_a.click()
                    page_num += 1
                    WebDriverWait(driver, 10).until(EC.staleness_of(profile_rows[0]))
                except Exception as e:
                    logger.info(f"Sonraki sayfa bulunamadı veya tıklanamadı: {e}")
                    break
            logger.info(f"Toplam {len(profiles)} profil toplandı.")
            return profiles
            
        except Exception as e:
            logger.error(f"Scraping hatası: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
    
    async def quick_search_profiles(self, name: str, max_results: int = 100) -> Dict[str, Any]:
        """Hızlı arama - ilk 10 profili hemen göster"""
        try:
            logger.info(f"Quick search başlatıldı: {name}")
            
            # Session ID oluştur
            session_id = self._generate_session_id()
            logger.info(f"Quick search session: {session_id}")
            
            # Request oluştur
            request = SearchRequest(name=name, max_results=max_results)
            
            # Arka planda scraping başlat
            asyncio.create_task(self._async_scrape_profiles(
                request, session_id, None, []
            ))
            
            # 30 saniye bekle ve ilk sonuçları al
            await asyncio.sleep(30)
            
            # Session dosyasını kontrol et
            session_data = await self.file_manager.load_session_data(session_id, "profiles")
            if session_data and session_data.get("profiles"):
                profiles = session_data["profiles"]
                # İlk 10 profili göster
                preview_profiles = profiles[:10]
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "message": f"'{name}' için hızlı arama tamamlandı!",
                    "preview_count": len(preview_profiles),
                    "total_found": len(profiles),
                    "max_results": max_results,
                    "preview_profiles": preview_profiles,
                    "next_steps": [
                        "check_scraping_status ile durum kontrol edebilirsiniz",
                        "get_full_results ile tüm sonuçları alabilirsiniz"
                    ]
                }
            else:
                return {
                    "success": False,
                    "session_id": session_id,
                    "message": f"'{name}' için arama başlatıldı, henüz sonuç yok",
                    "next_steps": [
                        "check_scraping_status ile durum kontrol edin"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Quick search error: {e}")
            return {
                "error": f"Hızlı arama hatası: {str(e)}",
                "name": name
            }
    
    async def check_scraping_status(self, session_id: str) -> Dict[str, Any]:
        """Scraping durumunu kontrol et"""
        try:
            logger.info(f"Scraping status kontrol ediliyor: {session_id}")
            
            # Session durumunu kontrol et
            status = await self.file_manager.get_session_status(session_id)
            
            # Session dosyasını oku
            session_data = await self.file_manager.load_session_data(session_id, "profiles")
            
            if session_data and session_data.get("profiles"):
                profiles = session_data["profiles"]
                completed = status.get("profiles_completed", False)
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "status": "completed" if completed else "in_progress",
                    "profiles_found": len(profiles),
                    "completed": completed,
                    "message": f"Scraping durumu: {len(profiles)} profil bulundu" + (" (tamamlandı)" if completed else " (devam ediyor)")
                }
            else:
                return {
                    "success": False,
                    "session_id": session_id,
                    "status": "not_found",
                    "message": "Session bulunamadı veya henüz sonuç yok"
                }
                
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {
                "error": f"Durum kontrol hatası: {str(e)}",
                "session_id": session_id
            }
    
    async def get_full_results(self, session_id: str, max_results: int = 50) -> Dict[str, Any]:
        """Tamamlanmış sonuçları getir"""
        try:
            logger.info(f"Full results getiriliyor: {session_id}")
            
            # Session dosyasını oku
            session_data = await self.file_manager.load_session_data(session_id, "profiles")
            if not session_data or not session_data.get("profiles"):
                return {
                    "error": "Session bulunamadı veya profil verisi yok",
                    "session_id": session_id
                }
            
            profiles = session_data["profiles"]
            
            # Maksimum sonuç sayısını sınırla
            limited_profiles = profiles[:max_results]
            
            # Detaylı bilgileri formatla
            detailed_profiles = []
            for profile in limited_profiles:
                detailed_profile = {
                    "name": profile.get("name", "N/A"),
                    "title": profile.get("title", "N/A"),
                    "university": profile.get("header", "N/A").split("/")[0] if profile.get("header") else "N/A",
                    "email": profile.get("email", ""),
                    "profile_url": profile.get("url", ""),
                    "photo_url": profile.get("photoUrl", ""),
                    "labels": [profile.get("green_label", ""), profile.get("blue_label", "")],
                    "keywords": profile.get("keywords", ""),
                    "full_header": profile.get("header", "N/A")
                }
                detailed_profiles.append(detailed_profile)
            
            return {
                "success": True,
                "session_id": session_id,
                "total_found": len(profiles),
                "shown_count": len(limited_profiles),
                "profiles": detailed_profiles
            }
            
        except Exception as e:
            logger.error(f"Full results error: {e}")
            return {
                "error": f"Sonuçlar alınırken hata: {str(e)}",
                "session_id": session_id
            }
    
    async def get_profile_details_from_session(self, session_id: str, profile_name: str, max_results: int = 10) -> Dict[str, Any]:
        """Session dosyasından belirli bir akademisyenin detaylarını getir"""
        try:
            logger.info(f"Session {session_id}'den {profile_name} profillerini getiriyor...")
            
            # Session dosyasını oku
            session_data = await self.file_manager.load_session_data(session_id, "profiles")
            if not session_data or not session_data.get("profiles"):
                return {
                    "error": "Session bulunamadı veya profil verisi yok",
                    "session_id": session_id,
                    "profile_name": profile_name
                }
            
            profiles = session_data["profiles"]
            
            # Profil adına göre filtrele (tam eşleşme)
            matching_profiles = []
            for profile in profiles:
                if profile.get("name", "").upper() == profile_name.upper():
                    matching_profiles.append(profile)
            
            if not matching_profiles:
                return {
                    "error": f"'{profile_name}' adında profil bulunamadı",
                    "session_id": session_id,
                    "profile_name": profile_name,
                    "total_profiles_in_session": len(profiles)
                }
            
            # Maksimum sonuç sayısını sınırla
            matching_profiles = matching_profiles[:max_results]
            
            # Detaylı bilgileri formatla
            detailed_profiles = []
            for profile in matching_profiles:
                detailed_profile = {
                    "name": profile.get("name", "N/A"),
                    "title": profile.get("title", "N/A"),
                    "university": profile.get("header", "N/A").split("/")[0] if profile.get("header") else "N/A",
                    "email": profile.get("email", ""),
                    "profile_url": profile.get("url", ""),
                    "photo_url": profile.get("photoUrl", ""),
                    "labels": [profile.get("green_label", ""), profile.get("blue_label", "")],
                    "keywords": profile.get("keywords", ""),
                    "full_header": profile.get("header", "N/A")
                }
                detailed_profiles.append(detailed_profile)
            
            return {
                "success": True,
                "session_id": session_id,
                "profile_name": profile_name,
                "found_count": len(matching_profiles),
                "total_in_session": len(profiles),
                "profiles": detailed_profiles
            }
            
        except Exception as e:
            logger.error(f"Profile details error: {e}")
            return {
                "error": f"Profil detayları alınırken hata: {str(e)}",
                "session_id": session_id,
                "profile_name": profile_name
            } 