import asyncio
import json
import logging
import sys
from typing import Any, Sequence, Dict
from mcp.server import Server
from mcp.server.models import InitializationOptions
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
        logging.info(f"Tool call: {name} with arguments: {arguments}")
        
        if name == "search_academic_profiles":
            result = await profile_scraper.search_profiles(**arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
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
            error_msg = f"Unknown tool: {name}"
            logging.error(error_msg)
            return [TextContent(type="text", text=f"Error: {error_msg}")]
    
    except Exception as e:
        error_msg = f"Error in tool {name}: {str(e)}"
        logging.error(error_msg)
        return [TextContent(type="text", text=f"Error: {error_msg}")]



async def main():
    """Main server entry point."""
    try:
        logging.info("Starting YÖK Akademik Scraper MCP Server...")
        
        async with stdio_server() as (read_stream, write_stream):
            logging.info("Server streams initialized")
            
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="yok-akademik-scraper",
                    server_version="1.0.0",
                    capabilities={
                        "tools": {}
                    }
                )
            )
    except KeyboardInterrupt:
        logging.info("Server interrupted by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1) 