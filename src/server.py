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
            name="quick_search",
            description="⚡ HIZLI ARAMA: Akademisyen arama yapar ve ilk 10 profili hemen gösterir (30 saniye)",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Aranacak akademisyen adı"
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
            name="check_scraping_status",
            description="📊 Scraping durumunu kontrol eder ve kaç profil bulunduğunu gösterir",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID (quick_search'ten alınan)"
                    }
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="get_full_results",
            description="📋 Tamamlanmış scraping sonuçlarını getirir",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID (quick_search'ten alınan)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maksimum sonuç sayısı",
                        "optional": True,
                        "default": 50
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
        if name == "quick_search":
            # Hızlı arama - ilk 10 profili hemen göster
            name = arguments.get("name", "")
            max_results = arguments.get("max_results", 100)
            
            result = await profile_scraper.quick_search_profiles(name, max_results)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "check_scraping_status":
            # Scraping durumunu kontrol et
            session_id = arguments["session_id"].strip()
            result = await profile_scraper.check_scraping_status(session_id)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "get_full_results":
            # Tamamlanmış sonuçları getir
            session_id = arguments["session_id"].strip()
            max_results = arguments.get("max_results", 50)
            result = await profile_scraper.get_full_results(session_id, max_results)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "get_collaborators":
            result = await collaborator_scraper.get_collaborators(**arguments)
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