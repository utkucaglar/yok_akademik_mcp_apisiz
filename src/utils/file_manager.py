import os
import json
import aiofiles
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class FileManager:
    """Asenkron dosya yöneticisi"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.sessions_path = self.base_path / "sessions"
        self.fields_path = self.base_path / "fields.json"
        
        # Dizinleri oluştur
        self.sessions_path.mkdir(parents=True, exist_ok=True)
    
    async def load_fields(self) -> List[Dict[str, Any]]:
        """Fields.json dosyasını yükle"""
        try:
            async with aiofiles.open(self.fields_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Fields.json yüklenemedi: {e}")
            return []
    
    def get_field_name_by_id(self, field_id: int) -> Optional[str]:
        """Field ID'ye göre alan adını bul"""
        try:
            # Fields verilerini senkron olarak yükle
            with open(self.fields_path, 'r', encoding='utf-8') as f:
                fields_data = json.load(f)
            
            for field in fields_data:
                if field['id'] == field_id:
                    return field['name']
            return None
        except Exception as e:
            logger.error(f"Field name lookup failed: {e}")
            return None
    
    def get_specialty_name_by_id(self, fields_data: List[Dict], field_id: int, specialty_id: int) -> Optional[str]:
        """Specialty ID'ye göre uzmanlık adını bul"""
        for field in fields_data:
            if field['id'] == field_id:
                for specialty in field['specialties']:
                    if specialty['id'] == specialty_id:
                        return specialty['name']
        return None
    
    def get_session_dir(self, session_id: str) -> Path:
        """Session dizinini al"""
        return self.sessions_path / session_id
    
    async def create_session_dir(self, session_id: str) -> Path:
        """Session dizinini oluştur"""
        try:
            session_dir = self.get_session_dir(session_id)
            # Dizin yoksa oluştur
            if not session_dir.exists():
                session_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Session klasörü oluşturuldu: {session_dir}")
            else:
                logger.info(f"Session klasörü zaten mevcut: {session_dir}")
            return session_dir
        except Exception as e:
            logger.error(f"Session klasörü oluşturulamadı: {e}")
            # Hata durumunda base path'i döndür
            return self.sessions_path
    
    async def save_profiles(self, session_id: str, profiles: List[Dict[str, Any]]) -> bool:
        """Profil verilerini kaydet"""
        try:
            logger.info(f"Profil verileri kaydediliyor: {session_id}, {len(profiles)} profil")
            
            session_dir = await self.create_session_dir(session_id)
            profile_file = session_dir / "main_profile.json"
            
            data = {
                "session_id": session_id,
                "profiles": profiles,
                "created_at": datetime.now().isoformat(),
                "total_count": len(profiles)
            }
            
            # Dosya yazma işlemi
            async with aiofiles.open(profile_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            
            logger.info(f"Profil verileri başarıyla kaydedildi: {profile_file}")
            return True
        except Exception as e:
            logger.error(f"Profil verileri kaydedilemedi: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def save_completed_profiles(self, session_id: str, completed_data: Dict[str, Any]) -> bool:
        """Tamamlanmış profil verilerini kaydet (completed: true ile)"""
        try:
            logger.info(f"Tamamlanmış profil verileri kaydediliyor: {session_id}")
            
            session_dir = await self.create_session_dir(session_id)
            profile_file = session_dir / "main_profile.json"
            
            # Dosya yazma işlemi
            async with aiofiles.open(profile_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(completed_data, ensure_ascii=False, indent=2))
            
            logger.info(f"Tamamlanmış profil verileri başarıyla kaydedildi: {profile_file}")
            return True
        except Exception as e:
            logger.error(f"Tamamlanmış profil verileri kaydedilemedi: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def save_collaborators(self, session_id: str, collaborators: List[Dict[str, Any]]) -> bool:
        """İşbirlikçi verilerini kaydet"""
        try:
            session_dir = await self.create_session_dir(session_id)
            collab_file = session_dir / "collaborators.json"
            
            data = {
                "session_id": session_id,
                "collaborators": collaborators,
                "created_at": datetime.now().isoformat(),
                "total_count": len(collaborators)
            }
            
            async with aiofiles.open(collab_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            
            logger.info(f"İşbirlikçi verileri kaydedildi: {len(collaborators)} işbirlikçi")
            return True
        except Exception as e:
            logger.error(f"İşbirlikçi verileri kaydedilemedi: {e}")
            return False
    
    async def mark_session_complete(self, session_id: str, file_type: str) -> bool:
        """Session'ı tamamlandı olarak işaretle"""
        try:
            session_dir = await self.create_session_dir(session_id)
            done_file = session_dir / f"{file_type}_done.txt"
            
            async with aiofiles.open(done_file, 'w') as f:
                await f.write("completed")
            
            logger.info(f"Session {session_id} {file_type} tamamlandı olarak işaretlendi")
            return True
        except Exception as e:
            logger.error(f"Session tamamlandı işaretlenemedi: {e}")
            return False
    
    async def load_session_data(self, session_id: str, data_type: str) -> Optional[Dict[str, Any]]:
        """Session verilerini yükle"""
        try:
            session_dir = self.get_session_dir(session_id)
            if not session_dir.exists():
                return None
            
            if data_type == "profiles":
                file_path = session_dir / "main_profile.json"
            elif data_type == "collaborators":
                file_path = session_dir / "collaborators.json"
            else:
                return None
            
            if not file_path.exists():
                return None
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Session verileri yüklenemedi: {e}")
            return None
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Session durumunu kontrol et"""
        # Clean session_id to remove any whitespace or newline characters
        session_id = session_id.strip()
        session_dir = self.get_session_dir(session_id)
        
        if not session_dir.exists():
            return {
                "session_id": session_id,
                "status": "not_found",
                "profiles_count": 0,
                "collaborators_count": 0
            }
        
        # Profil durumu
        profile_file = session_dir / "main_profile.json"
        profile_done = session_dir / "main_done.txt"
        
        # İşbirlikçi durumu
        collab_file = session_dir / "collaborators.json"
        collab_done = session_dir / "collaborators_done.txt"
        
        status = {
            "session_id": session_id,
            "status": "found" if profile_file.exists() else "not_found",
            "profiles_count": 0,
            "collaborators_count": 0,
            "profiles_completed": profile_done.exists(),
            "collaborators_completed": collab_done.exists()
        }
        
        # Profil sayısını al
        if profile_file.exists():
            try:
                async with aiofiles.open(profile_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                    status["profiles_count"] = len(data.get("profiles", []))
            except Exception:
                pass
        
        # İşbirlikçi sayısını al
        if collab_file.exists():
            try:
                async with aiofiles.open(collab_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                    status["collaborators_count"] = len(data.get("collaborators", []))
            except Exception:
                pass
        
        return status 