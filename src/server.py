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
            name="live_scraper_chat",
            description="Scraping yaparken canlı bilgi paylaşır - Real-time streaming chat tool",
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
                        "default": 50
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
            
            # İlk response'u hemen gönder
            first_response = None
            async for response in live_scraper_chat.handle_chat_request(messages, **chat_kwargs):
                if first_response is None:
                    first_response = response
                    break
            
            if first_response:
                return [TextContent(type="text", text=json.dumps(first_response, ensure_ascii=False, indent=2))]
            else:
                return [TextContent(type="text", text=json.dumps({"error": "No response generated"}, ensure_ascii=False, indent=2))]
        
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