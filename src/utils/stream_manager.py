#!/usr/bin/env python3
"""
Stream Manager - Real-time MCP updates
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Callable, Optional
from pathlib import Path
import aiofiles
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class StreamManager:
    """Real-time stream manager for MCP updates"""
    
    def __init__(self):
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.file_cache: Dict[str, str] = {}  # Cache for file contents
        self.observer = None
        
    async def start_streaming(self, session_id: str, callback: Callable):
        """Start streaming for a session"""
        if session_id in self.active_streams:
            logger.warning(f"Stream already active for {session_id}")
            return
            
        self.callbacks[session_id] = callback
        task = asyncio.create_task(self._stream_session(session_id))
        self.active_streams[session_id] = task
        logger.info(f"Started streaming for session {session_id}")
        
    async def stop_streaming(self, session_id: str):
        """Stop streaming for a session"""
        if session_id in self.active_streams:
            task = self.active_streams[session_id]
            task.cancel()
            del self.active_streams[session_id]
            if session_id in self.callbacks:
                del self.callbacks[session_id]
            logger.info(f"Stopped streaming for session {session_id}")
            
    async def _stream_session(self, session_id: str):
        """Stream session updates"""
        session_dir = Path(f"data/sessions/{session_id}")
        main_file = session_dir / "main_profile.json"
        collaborators_file = session_dir / "collaborators.json"
        
        try:
            # Initial status
            await self._send_update(session_id, {
                "type": "status",
                "session_id": session_id,
                "status": "started",
                "message": "Scraping başlatıldı..."
            })
            
            # Monitor files for changes
            while True:
                await asyncio.sleep(1)  # Check every second
                
                # Debug: Log file status
                logger.info(f"Checking files for session {session_id}: main_file={main_file.exists()}, collab_file={collaborators_file.exists()}")
                
                # Check main profiles
                if main_file.exists():
                    try:
                        async with aiofiles.open(main_file, 'r', encoding='utf-8') as f:
                            content = await f.read()
                            
                        # Check if file content has changed
                        cache_key = f"{session_id}_main"
                        if cache_key not in self.file_cache or self.file_cache[cache_key] != content:
                            logger.info(f"File content changed for {session_id}, sending update")
                            self.file_cache[cache_key] = content
                            data = json.loads(content)
                            
                            await self._send_update(session_id, {
                                "type": "profiles",
                                "session_id": session_id,
                                "data": data,
                                "count": len(data.get("profiles", [])),
                                "status": "profiles_updated"
                            })
                            
                            # If completed, stop streaming
                            if data.get("status") == "completed":
                                await self._send_update(session_id, {
                                    "type": "completed",
                                    "session_id": session_id,
                                    "status": "completed",
                                    "message": "Scraping tamamlandı!"
                                })
                                break
                        else:
                            logger.info(f"No file content change for {session_id}")
                            
                    except Exception as e:
                        logger.error(f"Error reading main file: {e}")
                        
                # Check collaborators
                if collaborators_file.exists():
                    try:
                        async with aiofiles.open(collaborators_file, 'r', encoding='utf-8') as f:
                            content = await f.read()
                            
                        # Check if file content has changed
                        cache_key = f"{session_id}_collaborators"
                        if cache_key not in self.file_cache or self.file_cache[cache_key] != content:
                            self.file_cache[cache_key] = content
                            data = json.loads(content)
                            
                            await self._send_update(session_id, {
                                "type": "collaborators",
                                "session_id": session_id,
                                "data": data,
                                "status": "collaborators_updated"
                            })
                            
                    except Exception as e:
                        logger.error(f"Error reading collaborators file: {e}")
                        
        except asyncio.CancelledError:
            logger.info(f"Stream cancelled for {session_id}")
        except Exception as e:
            logger.error(f"Stream error for {session_id}: {e}")
            await self._send_update(session_id, {
                "type": "error",
                "session_id": session_id,
                "error": str(e),
                "status": "error"
            })
        finally:
            await self.stop_streaming(session_id)
            
    async def _send_update(self, session_id: str, data: Dict[str, Any]):
        """Send update to callback"""
        if session_id in self.callbacks:
            try:
                await self.callbacks[session_id](data)
            except Exception as e:
                logger.error(f"Callback error for {session_id}: {e}")
    
    async def update_session_status(self, session_id: str, status: str, data: Optional[Dict[str, Any]] = None):
        """Update session status and save to file"""
        try:
            session_dir = Path(f"data/sessions/{session_id}")
            session_dir.mkdir(parents=True, exist_ok=True)
            
            status_data = {
                "session_id": session_id,
                "status": status,
                "timestamp": time.time()
            }
            
            if data:
                status_data.update(data)
            
            # Save status to file
            status_file = session_dir / "status.json"
            async with aiofiles.open(status_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(status_data, ensure_ascii=False, indent=2))
            
            logger.info(f"Session {session_id} status updated to: {status}")
            
        except Exception as e:
            logger.error(f"Error updating session status: {e}")
    
    async def get_updates(self, session_id: str) -> Dict[str, Any]:
        """Get latest updates for session"""
        # Clean session_id to remove any whitespace or newline characters
        session_id = session_id.strip()
        session_dir = Path(f"data/sessions/{session_id}")
        main_file = session_dir / "main_profile.json"
        
        if main_file.exists():
            try:
                async with aiofiles.open(main_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                    return {
                        "session_id": session_id,
                        "status": "available",
                        "data": data
                    }
            except Exception as e:
                logger.error(f"Error reading updates: {e}")
                return {
                    "session_id": session_id,
                    "status": "error",
                    "error": str(e)
                }
        else:
            return {
                "session_id": session_id,
                "status": "not_found",
                "message": "Session data not found"
            }

# Global instance
stream_manager = StreamManager() 