# Live Scraper Chat Tool - Real-time Streaming

Bu proje, YÖK Akademik veri tabanından scraping yaparken **canlı bilgi paylaşımı** yapabilen bir MCP (Model Context Protocol) server'ıdır.

## 🎯 Özellikler

### ✅ Mevcut Özellikler
- **Real-time streaming**: Scraping sırasında canlı güncellemeler
- **JSON kaydetme**: Tüm veriler JSON dosyalarına kaydedilir
- **Session yönetimi**: Her scraping işlemi için benzersiz session ID
- **Background processing**: Scraping arka planda çalışır
- **Progress tracking**: İşlem durumu takip edilir

### 🔄 Yeni Chat Tool Özelliği
- **`live_scraper_chat`**: Scraping yaparken canlı bilgi paylaşır
- **Streaming responses**: Gerçek zamanlı yanıtlar
- **Interactive chat**: Kullanıcı ile etkileşimli arama

## 🛠️ Kurulum

```bash
# Gerekli paketleri yükle
pip install -r requirements.txt

# MCP server'ı başlat
python -m src.server
```

## 📋 Kullanım

### 1. Normal Tool Kullanımı

```python
# Akademisyen arama
{
  "name": "search_academic_profiles",
  "arguments": {
    "name": "Ahmet Yılmaz",
    "max_results": 50
  }
}

# Session durumu kontrol
{
  "name": "get_session_status", 
  "arguments": {
    "session_id": "session_20241201_123456_abc123"
  }
}
```

### 2. Live Chat Tool Kullanımı

```python
# Chat tool ile real-time scraping
{
  "name": "live_scraper_chat",
  "arguments": {
    "messages": [
      {"role": "user", "content": "Ahmet Yılmaz"}
    ],
    "max_results": 50,
    "field_id": 1,
    "specialty_ids": "1,2,3"
  }
}
```

## 🔄 Streaming Nasıl Çalışır?

### 1. Chat Tool Çağrısı
```python
# Kullanıcı chat tool'u çağırır
live_scraper_chat.handle_chat_request(messages, **kwargs)
```

### 2. Background Scraping
```python
# Arka planda scraping başlar
asyncio.create_task(self._start_background_scraping(session_id, search_params))
```

### 3. Real-time Updates
```python
# Her 2 saniyede bir durum kontrol edilir
while True:
    await asyncio.sleep(2)
    status = await self.file_manager.get_session_status(session_id)
    # Progress updates gönderilir
```

### 4. JSON Kaydetme
```python
# Veriler JSON'a kaydedilir
await self.file_manager.save_profiles(session_id, profiles)
```

## 📊 Örnek Çıktı

### Chat Tool Response:
```json
{
  "role": "assistant",
  "content": "🔍 YÖK Akademik veri tabanında arama başlatılıyor...\n\nLütfen aradığınız akademisyenin adını belirtin."
}
```

### Progress Update:
```json
{
  "role": "assistant", 
  "content": "⏳ **Scraping devam ediyor...** (Update #3)\n\nVeriler toplanıyor, lütfen bekleyin..."
}
```

### Completion:
```json
{
  "role": "assistant",
  "content": "🏁 **İşlem tamamlandı!**\n\nTüm veriler başarıyla kaydedildi."
}
```

## 📁 Dosya Yapısı

```
yok-akademik-scraper-mcp/
├── src/
│   ├── tools/
│   │   ├── live_scraper_chat.py    # 🆕 Chat tool
│   │   ├── profile_scraper.py      # Ana scraping
│   │   └── collaborator_scraper.py # İşbirlikçi scraping
│   ├── utils/
│   │   ├── stream_manager.py       # Stream yönetimi
│   │   └── file_manager.py         # Dosya işlemleri
│   └── server.py                   # MCP server
├── data/
│   └── sessions/                   # Session verileri
└── mcp.json                        # MCP konfigürasyonu
```

## 🎯 Avantajlar

### ✅ Mevcut Sistem + Chat Tool
1. **İki yönlü çalışma**: Normal tool + Chat tool
2. **Real-time feedback**: Kullanıcı ilerlemeyi görür
3. **Background processing**: Scraping arka planda devam eder
4. **JSON persistence**: Veriler kalıcı olarak saklanır
5. **Session tracking**: Her işlem takip edilir

### 🔄 Streaming Özellikleri
- **Canlı güncellemeler**: Her adımda bilgi paylaşımı
- **Progress tracking**: İşlem durumu takibi
- **Error handling**: Hata durumlarında bilgilendirme
- **Timeout management**: Uzun süren işlemler için timeout

## 🚀 Test Etme

```bash
# Chat tool'u test et
python test_live_chat.py

# MCP server'ı başlat
python -m src.server
```

## 📝 Notlar

- Chat tool, normal tool'lardan farklı olarak **streaming response** döner
- Her scraping işlemi için **benzersiz session ID** oluşturulur
- Veriler hem **JSON'a kaydedilir** hem de **chat'te gösterilir**
- Background scraping sayesinde kullanıcı beklemek zorunda kalmaz

Bu sistem sayesinde scraping yaparken kullanıcı canlı olarak ilerlemeyi görebilir ve aynı zamanda veriler JSON dosyalarına kaydedilir! 🎉 