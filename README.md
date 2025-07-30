# YOK Akademik MCP Server (Async)

[![smithery badge](https://smithery.ai/badge/@utkucaglar/yok_akademik_mcp_apisiz)](https://smithery.ai/server/@utkucaglar/yok_akademik_mcp_apisiz)

A Model Context Protocol (MCP) server that provides **async tools** for interacting with the YOK Akademik API. This server enables searching for academic profiles and analyzing collaborators in Turkish universities with improved performance and non-blocking operations.

## 🚀 Features

This MCP server provides the following **async tools**:

### 🔍 `search_academic_profiles`

Search for academic profiles in Turkish universities using YOK Akademik API with async web scraping

* **Parameters:**  
   * `name` (string): Name to search for (e.g., 'mert yıl')  
   * `email` (string, optional): Email filter  
   * `field_id` (number, optional): Field ID filter  
   * `specialty_ids` (array of strings, optional): Specialty IDs filter

### 🤝 `get_academic_collaborators`

Get collaborators for a specific academic profile using YOK Akademik API with async processing

* **Parameters:**  
   * `sessionId` (string): Session ID from search results  
   * `profileId` (number): Profile ID to get collaborators for

### ℹ️ `get_yok_info`

Get information about YOK Akademik API and available features

* **Parameters:** None

## 🛠️ Installation

### Installing via Smithery

To install yok_akademik_mcp_apisiz for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@utkucaglar/yok_akademik_mcp_apisiz):

```bash
npx -y @smithery/cli install @utkucaglar/yok_akademik_mcp_apisiz --client claude
```

1. **Navigate to the project directory:**
   ```bash
   cd proje_mcp
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Build the project:**
   ```bash
   npm run build
   ```

## 🚀 Development

To run the server in development mode:

```bash
npm run dev
```

## ⚡ Async Features

This MCP server is built with **async-first architecture**:

- **Non-blocking operations**: All web scraping operations are async
- **Progressive loading**: Results are saved incrementally
- **Session management**: Automatic session ID generation and management
- **Error handling**: Robust error handling with graceful degradation
- **Resource cleanup**: Automatic browser cleanup on server shutdown

## 📊 Configuration

The server accepts the following configuration options:

* `baseUrl` (default: "https://akademik.yok.gov.tr/"): Base URL for YOK Akademik API
* `timeout` (default: 30000): Request timeout in milliseconds
* `headless` (default: true): Run browser in headless mode
* `maxProfiles` (default: 100): Maximum number of profiles to collect

## 💡 Usage Examples

### Search for academic profiles

```typescript
// Search by name
await search_academic_profiles({ name: "mert yıl" })

// Search with email filter
await search_academic_profiles({ 
  name: "mert yıl", 
  email: "mert@example.com" 
})

// Search with field filter
await search_academic_profiles({ 
  name: "mert yıl", 
  field_id: 8 
})
```

### Get collaborators for a profile

```typescript
await get_academic_collaborators({
  sessionId: "session_1753701905_niig92wwj",
  profileId: 4
})
```

### Get API information

```typescript
await get_yok_info()
```

## 🔧 API Endpoints

The server integrates with the following YOK Akademik API endpoints:

* **Search:** `POST /api/search` - Search for academic profiles
* **Collaborators:** `POST /api/collaborators/{sessionId}` - Get collaborators for a profile

## 📋 Response Format

### Search Response

```json
{
  "success": true,
  "sessionId": "session_1753701905_niig92wwj",
  "profiles": [
    {
      "id": 1,
      "name": "MERT YILDIRIM",
      "title": "PROFESÖR",
      "url": "https://akademik.yok.gov.tr/...",
      "info": "PROFESÖR\nMERT YILDIRIM\nDÜZCE ÜNİVERSİTESİ/...",
      "photoUrl": "data:image/jpg;base64,...",
      "header": "DÜZCE ÜNİVERSİTESİ/MÜHENDİSLİK FAKÜLTESİ/...",
      "green_label": "Fen Bilimleri ve Matematik Temel Alanı",
      "blue_label": "Fizik",
      "keywords": "Yoğun Madde Fiziği ; Yarı İletkenler ; Malzeme Fiziği",
      "email": "mertyildirim@duzce.edu.tr"
    }
  ],
  "total_profiles": 12
}
```

### Collaborators Response

```json
{
  "success": true,
  "sessionId": "session_1753701905_niig92wwj",
  "profile": { /* profile object */ },
  "collaborators": [
    {
      "id": 1,
      "name": "ABDULLAH ÇAĞLAR",
      "title": "PROFESÖR",
      "info": "KOCAELİ ÜNİVERSİTESİ/...",
      "green_label": "Mühendislik Temel Alanı",
      "blue_label": "Gıda Bilimleri ve Mühendisliği",
      "keywords": "Süt ve Süt Ürünleri Teknolojisi, Gıda Mikrobiyolojisi",
      "photoUrl": "data:image/jpg;base64,...",
      "status": "completed",
      "deleted": false,
      "url": "https://akademik.yok.gov.tr/...",
      "email": "abdullah.caglar@kocaeli.edu.tr"
    }
  ],
  "total_collaborators": 4,
  "completed": true,
  "status": "✅ Scraping tamamlandı! 4 işbirlikçi bulundu.",
  "timestamp": 1753702225
}
```

## 🏗️ Architecture

### Async Service Layer

The server uses a dedicated `YokAkademikService` class that handles:

- **Async web scraping** with Puppeteer
- **Session management** with automatic ID generation
- **Progressive data saving** to prevent data loss
- **Error recovery** with retry mechanisms
- **Resource management** with automatic cleanup

### MCP Integration

The server implements the Model Context Protocol with:

- **Tool registration** for async operations
- **Request/response handling** with proper error handling
- **Schema validation** for input parameters
- **Graceful shutdown** with resource cleanup

## 📁 File Structure

```
proje_mcp/
├── src/
│   ├── index.ts              # MCP server entry point
│   ├── types.ts              # TypeScript type definitions
│   └── yokAkademikService.ts # Async service implementation
├── main_codes/               # Original Python scripts
│   ├── scripts/
│   │   ├── scrape_main_profile.py
│   │   └── scrape_collaborators.py
│   └── public/
│       ├── fields.json
│       └── collaborator-sessions/
├── package.json
├── tsconfig.json
└── README.md
```

## 🔍 What is YOK Akademik?

YOK Akademik is a comprehensive database containing information about academics working in Turkish universities. The API provides:

* **Academic Profile Search**: Search by name, email, field, and specialty
* **Collaborator Analysis**: Analyze academic collaboration networks
* **Detailed Profile Information**: Title, institution, email, research areas

## 🎯 Use Cases

1. **Academic Research**: Find academics working in specific fields
2. **Collaboration Analysis**: Analyze academic collaboration networks
3. **Network Mapping**: Understand the structure of academic communities
4. **Contact Information**: Find contact details for academics

## 🚀 Performance Benefits

- **Async operations**: Non-blocking web scraping
- **Progressive loading**: Results saved incrementally
- **Session persistence**: Data saved to disk for recovery
- **Resource optimization**: Efficient browser management
- **Error resilience**: Graceful handling of network issues

## 📝 License

MIT

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ for the Turkish academic community** 