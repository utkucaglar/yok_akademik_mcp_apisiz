const { spawn } = require('child_process');
const path = require('path');

// Test the MCP server
async function testMCPServer() {
  console.log('🧪 Testing YOK Akademik MCP Server...\n');

  // Start the MCP server
  const serverProcess = spawn('node', ['dist/index.js'], {
    stdio: ['pipe', 'pipe', 'pipe']
  });

  let serverOutput = '';
  let serverError = '';

  serverProcess.stdout.on('data', (data) => {
    serverOutput += data.toString();
    console.log('Server output:', data.toString());
  });

  serverProcess.stderr.on('data', (data) => {
    serverError += data.toString();
    console.error('Server error:', data.toString());
  });

  // Wait a moment for server to start
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Test the get_yok_info tool
  const testRequest = {
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: 'get_yok_info',
      arguments: {}
    }
  };

  console.log('📤 Sending test request:', JSON.stringify(testRequest, null, 2));
  
  serverProcess.stdin.write(JSON.stringify(testRequest) + '\n');

  // Wait for response
  await new Promise(resolve => setTimeout(resolve, 3000));

  console.log('\n📊 Test Results:');
  console.log('Server Output:', serverOutput);
  console.log('Server Errors:', serverError);

  // Clean up
  serverProcess.kill();
  
  if (serverError) {
    console.log('❌ Test failed with errors');
    process.exit(1);
  } else {
    console.log('✅ Test completed successfully');
  }
}

testMCPServer().catch(console.error); 