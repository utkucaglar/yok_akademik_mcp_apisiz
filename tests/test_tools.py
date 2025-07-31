import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.tools.profile_scraper import ProfileScraperTool
from src.tools.collaborator_scraper import CollaboratorScraperTool
from src.models.schemas import SearchRequest, CollaboratorRequest

class TestProfileScraperTool:
    """ProfileScraperTool test sınıfı"""
    
    @pytest.fixture
    def profile_scraper(self):
        return ProfileScraperTool()
    
    @pytest.mark.asyncio
    async def test_generate_session_id(self, profile_scraper):
        """Session ID oluşturma testi"""
        session_id = profile_scraper._generate_session_id()
        assert session_id.startswith("session_")
        assert len(session_id) > 20
    
    @pytest.mark.asyncio
    async def test_parse_labels_and_keywords(self, profile_scraper):
        """Label ve keyword parsing testi"""
        line = "Bilgisayar Mühendisliği   Yazılım Mühendisliği   Python; Java; C++"
        green, blue, keywords = profile_scraper._parse_labels_and_keywords(line)
        assert green == "Bilgisayar Mühendisliği"
        assert blue == "Yazılım Mühendisliği"
        assert "Python" in keywords
        assert "Java" in keywords
        assert "C++" in keywords

class TestCollaboratorScraperTool:
    """CollaboratorScraperTool test sınıfı"""
    
    @pytest.fixture
    def collaborator_scraper(self):
        return CollaboratorScraperTool()
    
    @pytest.mark.asyncio
    async def test_get_profile_url_by_id(self, collaborator_scraper):
        """Profile URL alma testi"""
        # Mock session data
        mock_session_data = {
            "profiles": [
                {"id": 1, "url": "https://example.com/profile1"},
                {"id": 2, "url": "https://example.com/profile2"}
            ]
        }
        
        # Mock file manager
        collaborator_scraper.file_manager.load_session_data = AsyncMock(return_value=mock_session_data)
        
        url = await collaborator_scraper._get_profile_url_by_id("test_session", 1)
        assert url == "https://example.com/profile1"
        
        url = await collaborator_scraper._get_profile_url_by_id("test_session", 3)
        assert url is None

class TestSchemas:
    """Pydantic modelleri test sınıfı"""
    
    def test_search_request_valid(self):
        """Geçerli SearchRequest testi"""
        request = SearchRequest(
            name="Ahmet Yılmaz",
            field_id=15,
            specialty_ids="102,105",
            email="ahmet.yilmaz@example.com",
            max_results=50
        )
        assert request.name == "Ahmet Yılmaz"
        assert request.field_id == 15
        assert request.specialty_ids == "102,105"
        assert request.email == "ahmet.yilmaz@example.com"
        assert request.max_results == 50
    
    def test_search_request_minimal(self):
        """Minimal SearchRequest testi"""
        request = SearchRequest(name="Test User")
        assert request.name == "Test User"
        assert request.max_results == 100  # Default değer
        assert request.field_id is None
        assert request.specialty_ids is None
        assert request.email is None
    
    def test_collaborator_request_valid(self):
        """Geçerli CollaboratorRequest testi"""
        request = CollaboratorRequest(
            session_id="session_20240731_abc123",
            profile_id=5
        )
        assert request.session_id == "session_20240731_abc123"
        assert request.profile_id == 5
        assert request.profile_url is None
    
    def test_collaborator_request_with_url(self):
        """URL ile CollaboratorRequest testi"""
        request = CollaboratorRequest(
            session_id="session_20240731_abc123",
            profile_url="https://example.com/profile"
        )
        assert request.session_id == "session_20240731_abc123"
        assert request.profile_url == "https://example.com/profile"
        assert request.profile_id is None

if __name__ == "__main__":
    pytest.main([__file__]) 