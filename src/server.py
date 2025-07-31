import asyncio
import json
import logging
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.models import InitializationOptions

# Mock class for compatibility
class NotificationOptions:
    def __init__(self, tools_changed=False, resources_changed=False, prompts_changed=False):
        self.tools_changed = tools_changed
        self.resources_changed = resources_changed
        self.prompts_changed = prompts_changed
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .tools.profile_scraper import ProfileScraperTool
from .tools.collaborator_scraper import CollaboratorScraperTool
from .utils.stream_manager import stream_manager

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Server instance
server = Server("yok-akademik-scraper")

# Tool instances
profile_scraper = ProfileScraperTool()
collaborator_scraper = CollaboratorScraperTool()

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_academic_profiles",
            description="YÖK akademik veri tabanında akademisyen arama yapar",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Aranacak akademisyen adı"
                    },
                    "field_id": {
                        "type": "integer",
                        "description": "Alan ID (fields.json'dan)",
                        "optional": True
                    },
                    "specialty_ids": {
                        "type": "string",
                        "description": "Uzmanlık ID'leri (virgülle ayrılmış)",
                        "optional": True
                    },
                    "email": {
                        "type": "string",
                        "description": "Email ile filtreleme",
                        "optional": True
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maksimum sonuç sayısı (varsayılan: 100)",
                        "optional": True,
                        "default": 100
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_collaborators",
            description="Belirtilen akademisyenin işbirlikçilerini getirir",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID"
                    },
                    "profile_id": {
                        "type": "integer",
                        "description": "Profil ID",
                        "optional": True
                    },
                    "profile_url": {
                        "type": "string",
                        "description": "Profil URL'i",
                        "optional": True
                    }
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="get_session_status",
            description="Session durumunu kontrol eder",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID"
                    }
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="get_stream_updates",
            description="Real-time stream updates alır",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID"
                    }
                },
                "required": ["session_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    """Handle tool calls."""
    try:
        if name == "search_academic_profiles":
            result = await profile_scraper.search_profiles(**arguments)
            
            # Stream-based response
            if result.get("status") == "streaming":
                session_id = result["session_id"]
                # Stream callback'i ayarla
                await stream_manager.start_streaming(session_id, lambda msg: self._send_stream_update(msg))
                
                return [TextContent(type="text", text=json.dumps({
                    "session_id": session_id,
                    "status": "streaming",
                    "message": "Scraping başlatıldı. Sonuçlar real-time olarak gelecek.",
                    "stream_url": f"stream://{session_id}"
                }, ensure_ascii=False, indent=2))]
            else:
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "get_collaborators":
            result = await collaborator_scraper.get_collaborators(**arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "get_session_status":
            session_id = arguments["session_id"]
            # Stream manager'dan status al
            stream_status = stream_manager.get_session_status(session_id)
            if stream_status:
                return [TextContent(type="text", text=json.dumps(stream_status, ensure_ascii=False, indent=2))]
            else:
                # Fallback to file-based status
                result = await profile_scraper.get_session_status(session_id)
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "get_stream_updates":
            session_id = arguments["session_id"]
            status = stream_manager.get_session_status(session_id)
            if status:
                return [TextContent(type="text", text=json.dumps(status, ensure_ascii=False, indent=2))]
            else:
                return [TextContent(type="text", text=json.dumps({
                    "error": "Session not found",
                    "session_id": session_id
                }, ensure_ascii=False, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logging.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def _send_stream_update(self, message: Dict[str, Any]):
    """Stream update gönder"""
    try:
        # Bu fonksiyon MCP client'a real-time updates gönderecek
        update_text = json.dumps(message, ensure_ascii=False, indent=2)
        logging.info(f"Stream update: {update_text}")
        # TODO: Implement MCP notification system
    except Exception as e:
        logging.error(f"Stream update error: {e}")

async def main():
    """Main server entry point."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="yok-akademik-scraper",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(
                        tools_changed=False,
                        resources_changed=False,
                        prompts_changed=False
                    ),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main()) 