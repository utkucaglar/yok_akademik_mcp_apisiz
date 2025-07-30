const { spawn } = require('child_process');

/**
 * Example usage of the YOK Akademik MCP Server
 * This demonstrates how to use the async tools for academic profile searching
 */

class MCPClient {
  constructor() {
    this.serverProcess = null;
  }

  async startServer() {
    console.log('🚀 Starting YOK Akademik MCP Server...');
    
    this.serverProcess = spawn('node', ['dist/index.js'], {
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // Wait for server to initialize
    await new Promise(resolve => setTimeout(resolve, 2000));
    console.log('✅ Server started successfully');
  }

  async sendRequest(method, params) {
    const request = {
      jsonrpc: '2.0',
      id: Date.now(),
      method,
      params
    };

    return new Promise((resolve, reject) => {
      let response = '';
      
      this.serverProcess.stdout.once('data', (data) => {
        response = data.toString();
        try {
          const parsed = JSON.parse(response);
          resolve(parsed);
        } catch (e) {
          reject(new Error(`Invalid JSON response: ${response}`));
        }
      });

      this.serverProcess.stdin.write(JSON.stringify(request) + '\n');
    });
  }

  async getYokInfo() {
    console.log('\n📚 Getting YOK Akademik API information...');
    
    const response = await this.sendRequest('tools/call', {
      name: 'get_yok_info',
      arguments: {}
    });

    console.log('Response:', JSON.stringify(response, null, 2));
    return response;
  }

  async searchAcademicProfiles(searchParams) {
    console.log(`\n🔍 Searching for academic profiles: ${searchParams.name}`);
    
    const response = await this.sendRequest('tools/call', {
      name: 'search_academic_profiles',
      arguments: searchParams
    });

    console.log('Response:', JSON.stringify(response, null, 2));
    return response;
  }

  async getAcademicCollaborators(sessionId, profileId) {
    console.log(`\n🤝 Getting collaborators for session: ${sessionId}, profile: ${profileId}`);
    
    const response = await this.sendRequest('tools/call', {
      name: 'get_academic_collaborators',
      arguments: { sessionId, profileId }
    });

    console.log('Response:', JSON.stringify(response, null, 2));
    return response;
  }

  async stopServer() {
    if (this.serverProcess) {
      this.serverProcess.kill();
      console.log('🛑 Server stopped');
    }
  }
}

// Example usage
async function runExample() {
  const client = new MCPClient();
  
  try {
    // Start the server
    await client.startServer();

    // Example 1: Get API information
    await client.getYokInfo();

    // Example 2: Search for academic profiles
    const searchResult = await client.searchAcademicProfiles({
      name: 'mert yıl',
      field_id: 8  // Engineering field
    });

    // Example 3: Get collaborators (if we have a session and profile ID)
    if (searchResult.result && searchResult.result.content) {
      // Extract session ID from the response (this would be parsed from the actual response)
      const sessionId = 'session_example';
      const profileId = 1;
      
      // Uncomment to test collaborators (requires valid session/profile IDs)
      // await client.getAcademicCollaborators(sessionId, profileId);
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.stopServer();
  }
}

// Run the example
console.log('🎯 YOK Akademik MCP Server Example');
console.log('=====================================\n');

runExample().catch(console.error); 