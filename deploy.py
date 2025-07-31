#!/usr/bin/env python3
"""
YÖK Akademik Scraper MCP Deployment Script
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_dependencies():
    """Gerekli dependencies'leri kontrol et"""
    required_packages = [
        'mcp',
        'selenium',
        'webdriver-manager',
        'pydantic',
        'aiofiles'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Eksik paketler: {missing_packages}")
        print("Lütfen şu komutu çalıştırın:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✓ Tüm dependencies mevcut")
    return True

def check_structure():
    """Proje yapısını kontrol et"""
    required_files = [
        'mcp.json',
        'requirements.txt',
        'README.md',
        'src/server.py',
        'src/tools/profile_scraper.py',
        'src/tools/collaborator_scraper.py',
        'src/models/schemas.py',
        'src/utils/selenium_manager.py',
        'src/utils/file_manager.py',
        'data/fields.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"Eksik dosyalar: {missing_files}")
        return False
    
    print("✓ Proje yapısı doğru")
    return True

def test_server():
    """Server'ı test et"""
    try:
        result = subprocess.run([
            sys.executable, '-c', 
            'import src.server; print("Server test successful")'
        ], capture_output=True, text=True, cwd=Path.cwd())
        
        if result.returncode == 0:
            print("✓ Server test başarılı")
            return True
        else:
            print(f"✗ Server test başarısız: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Server test hatası: {e}")
        return False

def validate_mcp_config():
    """MCP konfigürasyonunu doğrula"""
    try:
        with open('mcp.json', 'r') as f:
            config = json.load(f)
        
        required_fields = ['name', 'version', 'description', 'mcpServers']
        for field in required_fields:
            if field not in config:
                print(f"✗ MCP config eksik alan: {field}")
                return False
        
        print("✓ MCP konfigürasyonu geçerli")
        return True
    except Exception as e:
        print(f"✗ MCP config hatası: {e}")
        return False

def main():
    """Ana deployment fonksiyonu"""
    print("🚀 YÖK Akademik Scraper MCP Deployment")
    print("=" * 50)
    
    # Dependency kontrolü
    print("\n1. Dependencies kontrol ediliyor...")
    if not check_dependencies():
        sys.exit(1)
    
    # Yapı kontrolü
    print("\n2. Proje yapısı kontrol ediliyor...")
    if not check_structure():
        sys.exit(1)
    
    # MCP config kontrolü
    print("\n3. MCP konfigürasyonu kontrol ediliyor...")
    if not validate_mcp_config():
        sys.exit(1)
    
    # Server testi
    print("\n4. Server test ediliyor...")
    if not test_server():
        sys.exit(1)
    
    print("\n✅ Deployment hazır!")
    print("\nKullanım:")
    print("1. Smithery'ye yüklemek için:")
    print("   - Bu klasörü GitHub'a push edin")
    print("   - Smithery'de yeni MCP server olarak ekleyin")
    print("   - mcp.json dosyasındaki konfigürasyonu kullanın")
    
    print("\n2. Local test için:")
    print("   python -m src.server")
    
    print("\n3. Tool'ları test etmek için:")
    print("   - search_academic_profiles")
    print("   - get_collaborators")
    print("   - get_session_status")

if __name__ == "__main__":
    main() 