import asyncio
import logging
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..models.schemas import CollaboratorRequest, Collaborator, SessionStatus
from ..utils.selenium_manager import SeleniumManager
from ..utils.file_manager import FileManager

logger = logging.getLogger(__name__)

class CollaboratorScraperTool:
    """İşbirlikçi scraper tool'u"""
    
    def __init__(self):
        self.selenium_manager = SeleniumManager()
        self.file_manager = FileManager()
        self.base_url = "https://akademik.yok.gov.tr/"
        self.default_photo_url = "/default_photo.jpg"
    
    async def get_collaborators(self, **kwargs) -> Dict[str, Any]:
        """İşbirlikçileri getir"""
        try:
            # Request'i doğrula
            request = CollaboratorRequest(**kwargs)
            
            # Session kontrolü
            session_status = await self.file_manager.get_session_status(request.session_id)
            if session_status["status"] == "not_found":
                return {
                    "error": f"Session {request.session_id} bulunamadı",
                    "status": "failed"
                }
            
            # Profil URL'ini al
            profile_url = request.profile_url
            if not profile_url and request.profile_id:
                profile_url = await self._get_profile_url_by_id(request.session_id, request.profile_id)
                if not profile_url:
                    return {
                        "error": f"Profile ID {request.profile_id} için URL bulunamadı",
                        "status": "failed"
                    }
            
            if not profile_url:
                return {
                    "error": "Profil URL'i gerekli",
                    "status": "failed"
                }
            
            # WebDriver ile scraping başlat
            driver = await self.selenium_manager.get_driver()
            
            try:
                collaborators = await self._scrape_collaborators(driver, profile_url)
                
                # Sonuçları kaydet
                await self.file_manager.save_collaborators(request.session_id, collaborators)
                await self.file_manager.mark_session_complete(request.session_id, "collaborators")
                
                return {
                    "session_id": request.session_id,
                    "collaborators": collaborators,
                    "total_count": len(collaborators),
                    "status": "completed"
                }
            finally:
                # Driver'ı kapat
                await self.selenium_manager.close_driver(driver)
                
        except Exception as e:
            logger.error(f"İşbirlikçi scraping hatası: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _get_profile_url_by_id(self, session_id: str, profile_id: int) -> Optional[str]:
        """Profile ID'ye göre URL'i al"""
        try:
            session_data = await self.file_manager.load_session_data(session_id, "profiles")
            if not session_data:
                return None
            
            profiles = session_data.get("profiles", [])
            for profile in profiles:
                if profile.get("id") == profile_id:
                    return profile.get("url")
            
            return None
        except Exception as e:
            logger.error(f"Profile URL alınamadı: {e}")
            return None
    
    async def _scrape_collaborators(self, driver, profile_url: str) -> List[Dict[str, Any]]:
        """İşbirlikçi scraping işlemi"""
        collaborators = []
        
        try:
            # Profil sayfasına git
            logger.info(f"Profil sayfasına gidiliyor: {profile_url}")
            await self.selenium_manager.navigate_to_page(driver, profile_url)
            
            # İşbirlikçiler sekmesine geç
            if not await self.selenium_manager.wait_for_clickable(
                driver, By.XPATH, "//a[@href='viewAuthorGraphs.jsp']"
            ):
                raise Exception("İşbirlikçiler sekmesi bulunamadı")
            
            driver.find_element(By.XPATH, "//a[@href='viewAuthorGraphs.jsp']").click()
            
            # Graph yüklenmesini bekle
            if not await self.selenium_manager.wait_for_element(driver, By.CSS_SELECTOR, "svg g"):
                raise Exception("İşbirlikçi grafiği yüklenemedi")
            
            # JavaScript ile işbirlikçi verilerini çek
            script = """
const gs = document.querySelectorAll('svg g');
const results = [];
for (let i = 2; i < gs.length; i++) {
    const name = gs[i].querySelector('text')?.textContent.trim() || '';
    gs[i].dispatchEvent(new MouseEvent('click', { bubbles: true }));
    const href = document.getElementById('pageUrl')?.href || '';
    results.push({ name, href });
}
return results;
"""
            isimler_ve_linkler = await self.selenium_manager.execute_script_safe(driver, script)
            
            if not isimler_ve_linkler:
                logger.warning("İşbirlikçi verileri çekilemedi")
                return collaborators
            
            # Her işbirlikçi için detay bilgileri al
            for idx, obj in enumerate(isimler_ve_linkler, start=1):
                try:
                    collaborator = await self._extract_collaborator_data(driver, obj, idx)
                    if collaborator:
                        collaborators.append(collaborator)
                        
                        # Progressive saving
                        if len(collaborators) % 10 == 0:
                            await self.file_manager.save_collaborators(
                                "temp_session", collaborators
                            )
                        
                        # Rate limiting
                        await asyncio.sleep(0.5)
                
                except Exception as e:
                    logger.error(f"İşbirlikçi verisi çıkarılamadı: {e}")
            
            return collaborators
            
        except Exception as e:
            logger.error(f"İşbirlikçi scraping hatası: {e}")
            return collaborators
    
    async def _extract_collaborator_data(self, driver, obj: Dict[str, str], idx: int) -> Optional[Dict[str, Any]]:
        """İşbirlikçi verilerini çıkar"""
        try:
            isim = obj['name']
            href = obj['href']
            
            # Varsayılan değerler
            info = ""
            deleted = False
            title = ''
            header = ''
            green_label = ''
            blue_label = ''
            keywords_str = ''
            photo_url = ''
            email = ''
            
            if not href:
                photo_url = self.default_photo_url
                deleted = True
            else:
                # İşbirlikçi profil sayfasına git
                await self.selenium_manager.navigate_to_page(driver, href)
                
                # Profil bilgilerini çek
                tds = driver.find_elements(By.XPATH, "//td[h6]")
                if not tds:
                    photo_url = self.default_photo_url
                    deleted = True
                else:
                    info = tds[0].text
                    info_lines = info.splitlines()
                    
                    if len(info_lines) > 1:
                        title = info_lines[0].strip()
                        name = info_lines[1].strip()
                    else:
                        title = isim
                        name = isim
                    
                    header = info_lines[2].strip() if len(info_lines) > 2 else ''
                    
                    # Label'ları çek
                    try:
                        green_span = tds[0].find_element(By.CSS_SELECTOR, 'span.label-success')
                        green_label = green_span.text.strip()
                    except Exception:
                        pass
                    
                    try:
                        blue_span = tds[0].find_element(By.CSS_SELECTOR, 'span.label-primary')
                        blue_label = blue_span.text.strip()
                        
                        # Keywords'i çek
                        td_html = tds[0].get_attribute('innerHTML')
                        import re
                        if isinstance(td_html, str):
                            m = re.search(r'<span[^>]*label-primary[^>]*>.*?</span>([^<]*)', td_html)
                            if m:
                                kw = m.group(1).strip()
                                if kw:
                                    keywords_str = kw
                    except Exception:
                        pass
                    
                    # Email
                    try:
                        email_link = tds[0].find_element(By.CSS_SELECTOR, "a[href^='mailto']")
                        email = email_link.text.strip().replace('[at]', '@')
                    except Exception:
                        email = ''
                    
                    # Fotoğraf
                    try:
                        img = driver.find_element(By.CSS_SELECTOR, "img.img-circle")
                        photo_url = img.get_attribute("src")
                    except Exception:
                        try:
                            img = driver.find_element(By.CSS_SELECTOR, "img#imgPicture")
                            photo_url = img.get_attribute("src")
                        except Exception:
                            photo_url = self.default_photo_url
            
            return {
                "id": idx,
                "name": isim,
                "title": title,
                "info": info,
                "green_label": green_label,
                "blue_label": blue_label,
                "keywords": keywords_str,
                "photoUrl": photo_url,
                "status": "completed",
                "deleted": deleted,
                "url": href if not deleted else "",
                "email": email
            }
            
        except Exception as e:
            logger.error(f"İşbirlikçi verisi çıkarılamadı: {e}")
            return None 