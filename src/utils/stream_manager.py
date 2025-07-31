import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import aiofiles

logger = logging.getLogger(__name__)

class StreamManager:
    """Real-time stream manager for MCP data processing"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.callback_handlers: Dict[str, List[Callable]] = {}
        self.file_observer = None
        self.is_running = False
        
    async def start_streaming(self, session_id: str, callback: Callable):
        """Stream başlat"""
        if session_id not in self.callback_handlers:
            self.callback_handlers[session_id] = []
        
        self.callback_handlers[session_id].append(callback)
        self.active_sessions[session_id] = {
            "status": "starting",
            "start_time": time.time(),
            "profiles_found": 0,
            "last_update": time.time()
        }
        
        logger.info(f"Stream started for session: {session_id}")
        
    async def update_session_status(self, session_id: str, status: str, data: Dict[str, Any] = None):
        """Session durumunu güncelle"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].update({
                "status": status,
                "last_update": time.time()
            })
            
            if data:
                self.active_sessions[session_id].update(data)
            
            # Callback'leri çağır
            await self._notify_callbacks(session_id, {
                "session_id": session_id,
                "status": status,
                "data": data or {},
                "timestamp": time.time()
            })
    
    async def _notify_callbacks(self, session_id: str, message: Dict[str, Any]):
        """Callback'leri çağır"""
        if session_id in self.callback_handlers:
            for callback in self.callback_handlers[session_id]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    async def monitor_session_files(self, session_id: str, session_dir: str):
        """Session dosyalarını izle"""
        while self.is_running and session_id in self.active_sessions:
            try:
                # Profil dosyasını kontrol et
                profile_file = os.path.join(session_dir, "main_profile.json")
                if os.path.exists(profile_file):
                    async with aiofiles.open(profile_file, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        if content.strip():
                            data = json.loads(content)
                            profiles_count = len(data.get("profiles", []))
                            
                            await self.update_session_status(session_id, "profiles_found", {
                                "profiles_found": profiles_count,
                                "profiles": data.get("profiles", [])
                            })
                
                # Status dosyasını kontrol et
                status_file = os.path.join(session_dir, "main_done.txt")
                if os.path.exists(status_file):
                    await self.update_session_status(session_id, "completed")
                    break
                
                await asyncio.sleep(2)  # 2 saniye bekle
                
            except Exception as e:
                logger.error(f"File monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def start_file_monitoring(self):
        """Dosya izleme başlat"""
        self.is_running = True
        logger.info("File monitoring started")
    
    async def stop_file_monitoring(self):
        """Dosya izleme durdur"""
        self.is_running = False
        logger.info("File monitoring stopped")
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Session durumunu al"""
        return self.active_sessions.get(session_id)
    
    async def cleanup_session(self, session_id: str):
        """Session'ı temizle"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        if session_id in self.callback_handlers:
            del self.callback_handlers[session_id]
        logger.info(f"Session cleaned up: {session_id}")

# Global stream manager instance
stream_manager = StreamManager() 