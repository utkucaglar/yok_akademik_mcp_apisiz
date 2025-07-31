# YÖK Akademik Scraper MCP
[![Smithery Badge](https://smithery.ai/badge/@utkucaglar/yok_akademik_mcp_apisiz)](https://smithery.ai/server/@utkucaglar/yok_akademik_mcp_apisiz)

YÖK Akademik veri tabanından akademisyen profilleri ve işbirlikçilerini scrape eden MCP (Model Context Protocol) server.

## Özellikler

- **Akademisyen Arama**: İsim, alan, uzmanlık ve email ile filtreleme
- **İşbirlikçi Analizi**: Akademisyenlerin işbirlikçilerini otomatik olarak çekme
- **Asenkron İşlem**: Yüksek performans için asenkron yapı
- **Session Yönetimi**: Uzun süren işlemler için session tracking
- **Rate Limiting**: YÖK sitesine aşırı yük vermemek için akıllı bekleme

## Kurulum

### Installing via Smithery

To install yok_akademik_mcp_apisiz for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@utkucaglar/yok_akademik_mcp_apisiz):

```bash
npx -y @smithery/cli install @utkucaglar/yok_akademik_mcp_apisiz --client claude
```

### Manual Installation
```bash
pip install -r requirements.txt
```

## Kullanım

### MCP Server Başlatma

```bash
python -m src.server
```

### Tool'lar

#### 1. Akademisyen Arama
```json
{
  "tool": "search_academic_profiles",
  "arguments": {
    "name": "Ahmet Yılmaz",
    "field_id": 15,
    "specialty_ids": "102,105",
    "email": "ahmet.yilmaz@hotmail.com",
    "max_results": 50
  }
}
```

#### 2. İşbirlikçi Analizi
```json
{
  "tool": "get_collaborators",
  "arguments": {
    "session_id": "session_20240731_abc123",
    "profile_id": 5
  }
}
```

#### 3. Session Durumu
```json
{
  "tool": "get_session_status",
  "arguments": {
    "session_id": "session_20240731_abc123"
  }
}
```

## Konfigürasyon

`mcp.json` dosyasında server konfigürasyonu bulunur:

```json
{
  "mcpServers": {
    "yok-scraper": {
      "command": "python",
      "args": ["-m", "src.server"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

## Alan ve Uzmanlık ID'leri

`data/fields.json` dosyasında tüm alan ve uzmanlık ID'leri bulunur.

## Lisans

MIT License

## Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın 