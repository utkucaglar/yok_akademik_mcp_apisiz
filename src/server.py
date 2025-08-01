import asyncio
import json
import logging
from typing import Any, Sequence, Dict
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
from .tools.live_scraper_chat import live_scraper_chat
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
            description="❌ DEPRECATED: Eski arama tool'u - live_scraper_chat kullanın",
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
            name="live_scraper_chat",
            type="chat",
            description="🔴 LIVE SCRAPING: Akademisyen arama yaparken canlı sonuçları gösterir - Real-time streaming chat tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "description": "Chat mesajları",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        }
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maksimum sonuç sayısı",
                        "optional": True,
                        "default": 100
                    },
                    "field_id": {
                        "type": "integer",
                        "description": "Alan ID",
                        "optional": True
                    },
                    "specialty_ids": {
                        "type": "string",
                        "description": "Uzmanlık ID'leri",
                        "optional": True
                    },
                    "email": {
                        "type": "string",
                        "description": "Email filtreleme",
                        "optional": True
                    }
                },
                "required": ["messages"]
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
            description="Stream güncellemelerini alır",
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
            name="get_profile_details",
            description="📋 Scrape edilmiş profillerden detaylı bilgi getirir",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID (live_scraper_chat'ten alınan)"
                    },
                    "profile_name": {
                        "type": "string",
                        "description": "Aranacak akademisyen adı (tam eşleşme)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maksimum sonuç sayısı",
                        "optional": True,
                        "default": 10
                    }
                },
                "required": ["session_id", "profile_name"]
            }
        ),

    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    """Handle tool calls."""
    try:
        if name == "search_academic_profiles":
            result = await profile_scraper.search_profiles(**arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "live_scraper_chat":
            # Chat tool için streaming response
            messages = arguments.get("messages", [])
            chat_kwargs = {k: v for k, v in arguments.items() if k != "messages"}
            
            # Streaming response'ları direkt olarak yield et
            responses = []
            async for response in live_scraper_chat.handle_chat_request(messages, **chat_kwargs):
                responses.append(TextContent(type="text", text=json.dumps(response, ensure_ascii=False, indent=2)))
            
            return responses
        
        elif name == "get_collaborators":
            result = await collaborator_scraper.get_collaborators(**arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "get_session_status":
            session_id = arguments["session_id"].strip()
            result = await profile_scraper.get_session_status(session_id)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "get_stream_updates":
            session_id = arguments["session_id"].strip()
            result = await stream_manager.get_updates(session_id)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "get_profile_details":
            session_id = arguments["session_id"].strip()
            profile_name = arguments["profile_name"].strip()
            max_results = arguments.get("max_results", 10)
            
            # Session dosyasından profilleri oku
            result = await profile_scraper.get_profile_details_from_session(session_id, profile_name, max_results)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logging.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]



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