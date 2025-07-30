import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { YokAkademikService } from './yokAkademikService.js';

class YokAkademikMCPServer {
  private server: Server;
  private yokService: YokAkademikService;

  constructor() {
    this.server = new Server(
      {
        name: 'yok-akademik-mcp-async',
        version: '1.0.0',
      }
    );

    this.yokService = new YokAkademikService();

    this.setupToolHandlers();
  }

  private setupToolHandlers() {
    // List tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'search_academic_profiles',
            description: 'Search for academic profiles in Turkish universities using YOK Akademik API',
            inputSchema: {
              type: 'object',
              properties: {
                name: {
                  type: 'string',
                  description: 'Name to search for (e.g., "mert yıl")',
                },
                email: {
                  type: 'string',
                  description: 'Email filter (optional)',
                },
                field_id: {
                  type: 'number',
                  description: 'Field ID filter (optional)',
                },
                specialty_ids: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Specialty IDs filter (optional)',
                },
              },
              required: ['name'],
            },
          },
          {
            name: 'get_academic_collaborators',
            description: 'Get collaborators for a specific academic profile using YOK Akademik API',
            inputSchema: {
              type: 'object',
              properties: {
                sessionId: {
                  type: 'string',
                  description: 'Session ID from search results',
                },
                profileId: {
                  type: 'number',
                  description: 'Profile ID to get collaborators for',
                },
              },
              required: ['sessionId', 'profileId'],
            },
          },
          {
            name: 'get_yok_info',
            description: 'Get information about YOK Akademik API and available features',
            inputSchema: {
              type: 'object',
              properties: {},
            },
          },
        ],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'search_academic_profiles':
            return await this.handleSearchAcademicProfiles(args);

          case 'get_academic_collaborators':
            return await this.handleGetAcademicCollaborators(args);

          case 'get_yok_info':
            return await this.handleGetYokInfo();

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        console.error(`Error handling tool call ${name}:`, error);
        throw error;
      }
    });
  }

  private async handleSearchAcademicProfiles(args: any) {
    const { name, email, field_id, specialty_ids } = args;

    if (!name) {
      throw new Error('Name parameter is required');
    }

    console.log(`[MCP] Searching academic profiles for: ${name}`);
    
    const result = await this.yokService.searchAcademicProfiles({
      name,
      email,
      field_id,
      specialty_ids,
    });

    return {
      content: [
        {
          type: 'text',
          text: `✅ Search completed! Found ${result.total_profiles} profiles.\n\nSession ID: ${result.sessionId}\n\nProfiles:\n${result.profiles.map(p => `- ${p.name} (${p.title}) - ${p.email}`).join('\n')}`,
        },
      ],
    };
  }

  private async handleGetAcademicCollaborators(args: any) {
    const { sessionId, profileId } = args;

    if (!sessionId || !profileId) {
      throw new Error('Session ID and Profile ID are required');
    }

    console.log(`[MCP] Getting collaborators for session: ${sessionId}, profile: ${profileId}`);
    
    const result = await this.yokService.getAcademicCollaborators({
      sessionId,
      profileId,
    });

    return {
      content: [
        {
          type: 'text',
          text: `✅ Collaborators analysis completed!\n\nProfile: ${result.profile.name} (${result.profile.title})\nTotal Collaborators: ${result.total_collaborators}\n\nCollaborators:\n${result.collaborators.map(c => `- ${c.name} (${c.title}) - ${c.email}`).join('\n')}`,
        },
      ],
    };
  }

  private async handleGetYokInfo() {
    const info = await this.yokService.getYokInfo();

    return {
      content: [
        {
          type: 'text',
          text: `📚 ${info.name}\n\n${info.description}\n\nBase URL: ${info.baseUrl}\n\nFeatures:\n${info.features.map((f: string) => `- ${f}`).join('\n')}\n\nEndpoints:\n${info.endpoints.map((e: string) => `- ${e}`).join('\n')}`,
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);

    // Handle cleanup on exit
    process.on('SIGINT', async () => {
      console.log('[MCP] Shutting down...');
      await this.yokService.cleanup();
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      console.log('[MCP] Shutting down...');
      await this.yokService.cleanup();
      process.exit(0);
    });

    console.log('[MCP] YOK Akademik MCP Server started');
  }
}

// Start the server
const server = new YokAkademikMCPServer();
server.run().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
}); 