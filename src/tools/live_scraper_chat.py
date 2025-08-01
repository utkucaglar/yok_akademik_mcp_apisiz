#!/usr/bin/env python3
"""
Live Scraper Chat Tool - Real-time streaming chat tool
"""

import asyncio
import json
import logging
from typing import Dict, Any, AsyncGenerator
from datetime import datetime
import os
import time

from ..models.schemas import SearchRequest
from ..utils.stream_manager import stream_manager
from ..utils.file_manager import FileManager

logger = logging.getLogger(__name__)

class LiveScraperChatTool:
    """Real-time streaming chat tool for scraping"""
    
    def __init__(self):
        self.file_manager = FileManager()
        self.base_url = "https://akademik.yok.gov.tr/"
    
    async def handle_chat_request(self, messages: list, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle chat request with streaming responses"""
        try:
            # İlk mesajı gönder
            yield {
                "role": "assistant",
                "content": "🔍 YÖK Akademik veri tabanında arama başlatılıyor...\n\nLütfen aradığınız akademisyenin adını belirtin."
            }
            
            # Son kullanıcı mesajını al
            last_user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break
            
            if not last_user_message:
                yield {
                    "role": "assistant", 
                    "content": "❌ Arama terimi belirtilmedi. Lütfen bir akademisyen adı girin."
                }
                return
            
            # Arama parametrelerini hazırla
            search_params = {
                "name": last_user_message.strip(),
                "max_results": kwargs.get("max_results", 50)
            }
            
            # Field ve specialty parametrelerini ekle
            if "field_id" in kwargs:
                search_params["field_id"] = kwargs["field_id"]
            if "specialty_ids" in kwargs:
                search_params["specialty_ids"] = kwargs["specialty_ids"]
            if "email" in kwargs:
                search_params["email"] = kwargs["email"]
            
            yield {
                "role": "assistant",
                "content": f"🔎 **{search_params['name']}** için arama başlatılıyor...\n\nArama parametreleri:\n- İsim: {search_params['name']}\n- Maksimum sonuç: {search_params['max_results']}"
            }
            
            # Session ID oluştur
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            import random
            import string
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            session_id = f"session_{timestamp}_{random_suffix}"
            
            yield {
                "role": "assistant",
                "content": f"📋 **Session ID:** `{session_id}`\n\nScraping başlatılıyor, sonuçlar canlı olarak gelecek..."
            }
            
            # Session dizinini oluştur
            session_dir = f"data/sessions/{session_id}"
            os.makedirs(session_dir, exist_ok=True)
            session_file_path = f"{session_dir}/main_profile.json"
            
            # Background scraping başlat
            scraping_task = asyncio.create_task(self._start_background_scraping(session_id, search_params))
            
            # Dosya değişikliklerini sık kontrol et
            last_profile_count = 0
            last_file_size = 0
            last_file_mtime = 0
            max_wait_time = 300  # 5 dakika maksimum bekleme
            start_time = datetime.now()
            
            while True:
                try:
                    # Dosya var mı ve değişmiş mi kontrol et
                    if os.path.exists(session_file_path):
                        current_file_size = os.path.getsize(session_file_path)
                        current_file_mtime = os.path.getmtime(session_file_path)
                        
                        # Dosya değişmiş mi kontrol et (boyut veya zaman)
                        if current_file_size > last_file_size or current_file_mtime > last_file_mtime:
                            # Dosya değişmiş - oku ve yeni profilleri göster
                            current_data = await self._read_session_file(session_file_path)
                            if current_data and current_data.get("profiles"):
                                current_profile_count = len(current_data["profiles"])
                                
                                if current_profile_count > last_profile_count:
                                    # Yeni profiller bulundu - her 5 profilde bir göster
                                    new_profiles = current_data["profiles"][last_profile_count:]
                                    
                                    # Her 5 profilde bir batch göster (daha sık güncelleme)
                                    batch_size = 5
                                    for i in range(0, len(new_profiles), batch_size):
                                        batch = new_profiles[i:i+batch_size]
                                        yield {
                                            "role": "assistant",
                                            "content": f"✅ **{len(batch)} yeni profil bulundu!**\n\n" +
                                                     self._format_new_profiles(batch) +
                                                     f"\n\n📊 **Toplam: {last_profile_count + i + len(batch)} profil**"
                                        }
                                        await asyncio.sleep(0.1)  # Çok kısa bekleme
                                    
                                    last_profile_count = current_profile_count
                            
                            last_file_size = current_file_size
                            last_file_mtime = current_file_mtime
                    
                    # JSON dosyasında completed kontrolü yap
                    current_data = await self._read_session_file(session_file_path)
                    if current_data and current_data.get("completed") == True:
                        # İşlem tamamlandı - tüm profiller gösterildi
                        profiles = current_data.get("profiles", [])
                        total_count = current_data.get("total_count", len(profiles))
                        
                        yield {
                            "role": "assistant",
                            "content": f"🏁 **İşlem tamamlandı!**\n\n📊 **Toplam {total_count} profil bulundu:**\n\n" + 
                                     self._format_profiles_summary(profiles) +
                                     f"\n\n💾 **Session ID:** `{session_id}`\nTüm veriler JSON dosyasına kaydedildi."
                        }
                        
                        # Scraping tamamlandığında hemen dur
                        logger.info(f"Scraping completed for session {session_id} - {total_count} profiles")
                        break
                    
                    # Session durumunu kontrol et (fallback)
                    status = await self.file_manager.get_session_status(session_id)
                    if status.get("status") == "completed":
                        # İşlem tamamlandı
                        final_data = await self._read_session_file(session_file_path)
                        if final_data and final_data.get("profiles"):
                            profiles = final_data["profiles"]
                            yield {
                                "role": "assistant",
                                "content": f"🏁 **İşlem tamamlandı!**\n\n📊 **Toplam {len(profiles)} profil bulundu:**\n\n" + 
                                         self._format_profiles_summary(profiles) +
                                         f"\n\n💾 **Session ID:** `{session_id}`\nTüm veriler JSON dosyasına kaydedildi."
                            }
                        else:
                            yield {
                                "role": "assistant",
                                "content": "🏁 **İşlem tamamlandı!**\n\nTüm veriler başarıyla kaydedildi."
                            }
                        # Scraping tamamlandığında hemen dur
                        logger.info(f"Scraping completed for session {session_id}")
                        break
                        
                    elif status.get("status") == "error":
                        yield {
                            "role": "assistant",
                            "content": f"❌ **Hata:** {status.get('error', 'Bilinmeyen hata')}"
                        }
                        break
                    
                    # Çok kısa bekleme (daha sık kontrol)
                    await asyncio.sleep(0.2)
                    
                    # Timeout kontrolü
                    elapsed_time = (datetime.now() - start_time).total_seconds()
                    if elapsed_time > max_wait_time:
                        yield {
                            "role": "assistant",
                            "content": f"⏰ **Timeout:** Scraping işlemi {max_wait_time} saniye sonra durduruldu. Session ID ile durumu kontrol edebilirsiniz."
                        }
                        logger.warning(f"Timeout reached for session {session_id}")
                        break
                        
                except asyncio.CancelledError:
                    logger.info("Chat request cancelled by user")
                    break
                except Exception as e:
                    logger.error(f"Error in file monitoring: {e}")
                    await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Chat request error: {e}")
            yield {
                "role": "assistant",
                "content": f"❌ **Sistem hatası:** {str(e)}"
            }
    
    async def _read_session_file(self, file_path: str) -> Dict[str, Any]:
        """Session dosyasını oku"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():  # Dosya boş değilse
                        return json.loads(content)
                    else:
                        return None
        except json.JSONDecodeError as e:
            # JSON parse hatası - dosya henüz tam yazılmamış olabilir
            return None
        except Exception as e:
            logger.error(f"Error reading session file: {e}")
        return None
    
    def _format_profiles_summary(self, profiles: list) -> str:
        """Profil özetini formatla"""
        if not profiles:
            return "Hiç profil bulunamadı."
        
        summary = []
        for i, profile in enumerate(profiles[:10], 1):  # İlk 10 profili göster
            name = profile.get("name", "N/A")
            title = profile.get("title", "N/A")
            university = profile.get("header", "N/A").split("/")[0] if profile.get("header") else "N/A"
            email = profile.get("email", "")
            
            summary.append(f"{i}. **{name}** - {title}")
            summary.append(f"   📍 {university}")
            if email:
                summary.append(f"   📧 {email}")
            summary.append("")
        
        if len(profiles) > 10:
            summary.append(f"... ve {len(profiles) - 10} profil daha")
        
        return "\n".join(summary)
    
    def _format_new_profiles(self, new_profiles: list) -> str:
        """Yeni profilleri formatla"""
        if not new_profiles:
            return ""
        
        summary = []
        for profile in new_profiles:
            name = profile.get("name", "N/A")
            title = profile.get("title", "N/A")
            university = profile.get("header", "N/A").split("/")[0] if profile.get("header") else "N/A"
            
            summary.append(f"• **{name}** - {title}")
            summary.append(f"  📍 {university}")
        
        return "\n".join(summary)
    
    async def _start_background_scraping(self, session_id: str, search_params: Dict[str, Any]):
        """Background scraping işlemini başlat"""
        try:
            from .profile_scraper import ProfileScraperTool
            
            scraper = ProfileScraperTool()
            
            # Search request oluştur
            request = SearchRequest(**search_params)
            
            # Scraping başlat
            await scraper._async_scrape_profiles(
                request, 
                session_id, 
                search_params.get("selected_field"), 
                search_params.get("selected_specialties", [])
            )
            
        except Exception as e:
            logger.error(f"Background scraping error: {e}")
            await stream_manager.update_session_status(session_id, "error", {"error": str(e)})

# Global instance
live_scraper_chat = LiveScraperChatTool() 