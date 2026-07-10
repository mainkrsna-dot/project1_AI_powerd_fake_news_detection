"""
Test suite for new features in Fake News Detection API - Iteration 2
Tests: History API, News Verification, Batch Processing
"""
import pytest
import requests
import os
import base64
from io import BytesIO
from PIL import Image

# Get backend URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API_URL = f"{BASE_URL}/api"


class TestHealthAndStatus:
    """Basic health and status endpoint tests"""
    
    def test_api_health(self):
        """Test API root endpoint"""
        response = requests.get(f"{API_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        print("✓ API health check passed")
    
    def test_news_api_status_not_configured(self):
        """Test News API status shows not configured"""
        response = requests.get(f"{API_URL}/news-api-status")
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] == False
        assert "not configured" in data["message"].lower()
        print("✓ News API status correctly shows not configured")


class TestHistoryAPI:
    """History API endpoint tests"""
    
    def test_get_history_empty(self):
        """Test GET /api/history returns paginated results"""
        response = requests.get(f"{API_URL}/history")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        print(f"✓ History GET works - Total: {data['total']}, Items: {len(data['items'])}")
    
    def test_get_history_with_type_filter(self):
        """Test GET /api/history with type filter"""
        for filter_type in ["text", "image", "video", "verification"]:
            response = requests.get(f"{API_URL}/history", params={"type": filter_type})
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            # All items should match the filter type
            for item in data["items"]:
                assert item["type"] == filter_type
            print(f"✓ History filter by '{filter_type}' works")
    
    def test_get_history_pagination(self):
        """Test GET /api/history with pagination params"""
        response = requests.get(f"{API_URL}/history", params={"limit": 5, "offset": 0})
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0
        print("✓ History pagination works")
    
    def test_clear_history(self):
        """Test DELETE /api/history clears all history"""
        response = requests.delete(f"{API_URL}/history")
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data
        print(f"✓ History cleared - Deleted: {data['deleted_count']}")
        
        # Verify history is empty
        verify_response = requests.get(f"{API_URL}/history")
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["total"] == 0
        print("✓ History verified empty after clear")


class TestNewsVerification:
    """News verification endpoint tests"""
    
    def test_verify_news_with_ai_fallback(self):
        """Test POST /api/verify-news with AI fallback (News API not configured)"""
        claim = "The Earth is approximately 4.5 billion years old"
        response = requests.post(
            f"{API_URL}/verify-news",
            json={"claim": claim},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "status" in data
        assert data["status"] in ["REAL", "FAKE", "UNCERTAIN"]
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert 0 <= data["confidence"] <= 100
        assert "explanation" in data
        assert "timestamp" in data
        assert "news_api_available" in data
        assert data["news_api_available"] == False  # News API not configured
        
        print(f"✓ News verification works - Status: {data['status']}, Confidence: {data['confidence']}%")
        print(f"  News API available: {data['news_api_available']}")
    
    def test_verify_news_saves_to_history(self):
        """Test that news verification saves to history"""
        # Clear history first
        requests.delete(f"{API_URL}/history")
        
        # Verify a claim
        claim = "TEST_CLAIM: Water boils at 100 degrees Celsius at sea level"
        response = requests.post(
            f"{API_URL}/verify-news",
            json={"claim": claim},
            timeout=60
        )
        assert response.status_code == 200
        
        # Check history
        history_response = requests.get(f"{API_URL}/history", params={"type": "verification"})
        assert history_response.status_code == 200
        history_data = history_response.json()
        
        assert history_data["total"] >= 1
        # Find our test claim in history
        found = False
        for item in history_data["items"]:
            if "TEST_CLAIM" in item.get("content_preview", ""):
                found = True
                assert item["type"] == "verification"
                break
        
        assert found, "Verification should be saved to history"
        print("✓ News verification saves to history")


class TestTextDetectionHistory:
    """Test that text detection saves to history"""
    
    def test_text_detection_saves_to_history(self):
        """Test that text detection analysis appears in history"""
        # Clear history first
        requests.delete(f"{API_URL}/history")
        
        # Perform text detection
        test_text = "TEST_TEXT_HISTORY: Breaking news - Scientists discover new planet"
        response = requests.post(
            f"{API_URL}/detect-text",
            json={"text": test_text},
            timeout=60
        )
        assert response.status_code == 200
        
        # Check history
        history_response = requests.get(f"{API_URL}/history", params={"type": "text"})
        assert history_response.status_code == 200
        history_data = history_response.json()
        
        assert history_data["total"] >= 1
        # Find our test text in history
        found = False
        for item in history_data["items"]:
            if "TEST_TEXT_HISTORY" in item.get("content_preview", ""):
                found = True
                assert item["type"] == "text"
                assert "status" in item
                assert "confidence" in item
                break
        
        assert found, "Text detection should be saved to history"
        print("✓ Text detection saves to history")


class TestBatchImageDetection:
    """Batch image detection endpoint tests"""
    
    def _create_test_image(self, color=(255, 0, 0), size=(100, 100)):
        """Create a simple test image with visual features"""
        # Create image with gradient for visual features
        img = Image.new('RGB', size, color)
        # Add some variation
        pixels = img.load()
        for i in range(size[0]):
            for j in range(size[1]):
                r = min(255, color[0] + i % 50)
                g = min(255, color[1] + j % 50)
                b = min(255, color[2] + (i + j) % 50)
                pixels[i, j] = (r, g, b)
        
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        return buffer
    
    def test_batch_detect_images_single(self):
        """Test batch image detection with single image"""
        # Create test image
        img_buffer = self._create_test_image(color=(100, 150, 200))
        
        files = [
            ('files', ('test_image_1.jpg', img_buffer, 'image/jpeg'))
        ]
        
        response = requests.post(
            f"{API_URL}/batch-detect-images",
            files=files,
            timeout=120
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_files" in data
        assert data["total_files"] == 1
        assert "successful" in data
        assert "failed" in data
        assert "results" in data
        assert len(data["results"]) == 1
        
        result = data["results"][0]
        assert "filename" in result
        assert "status" in result
        assert "confidence" in result
        assert "success" in result
        
        print(f"✓ Batch image detection (single) works - Status: {result['status']}, Success: {result['success']}")
    
    def test_batch_detect_images_multiple(self):
        """Test batch image detection with multiple images"""
        # Create multiple test images
        images = []
        for i, color in enumerate([(255, 100, 100), (100, 255, 100), (100, 100, 255)]):
            img_buffer = self._create_test_image(color=color)
            images.append(('files', (f'test_image_{i+1}.jpg', img_buffer, 'image/jpeg')))
        
        response = requests.post(
            f"{API_URL}/batch-detect-images",
            files=images,
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_files"] == 3
        assert len(data["results"]) == 3
        
        for i, result in enumerate(data["results"]):
            assert result["index"] == i
            print(f"  Image {i+1}: {result['filename']} - {result['status']} ({result['confidence']}%)")
        
        print(f"✓ Batch image detection (multiple) works - {data['successful']}/{data['total_files']} successful")
    
    def test_batch_detect_images_max_limit(self):
        """Test batch image detection rejects more than 10 files"""
        # Create 11 test images
        images = []
        for i in range(11):
            img_buffer = self._create_test_image(color=(i * 20, i * 20, i * 20))
            images.append(('files', (f'test_image_{i+1}.jpg', img_buffer, 'image/jpeg')))
        
        response = requests.post(
            f"{API_URL}/batch-detect-images",
            files=images,
            timeout=30
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "10" in str(data.get("detail", ""))
        print("✓ Batch image detection correctly rejects >10 files")
    
    def test_batch_images_save_to_history(self):
        """Test that batch image detection saves to history"""
        # Clear history first
        requests.delete(f"{API_URL}/history")
        
        # Create and upload test image
        img_buffer = self._create_test_image(color=(200, 100, 50))
        files = [('files', ('batch_test_image.jpg', img_buffer, 'image/jpeg'))]
        
        response = requests.post(
            f"{API_URL}/batch-detect-images",
            files=files,
            timeout=120
        )
        assert response.status_code == 200
        
        # Check history
        history_response = requests.get(f"{API_URL}/history", params={"type": "image"})
        assert history_response.status_code == 200
        history_data = history_response.json()
        
        assert history_data["total"] >= 1
        print("✓ Batch image detection saves to history")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_history(self):
        """Clean up test history entries"""
        response = requests.delete(f"{API_URL}/history")
        assert response.status_code == 200
        print("✓ Test cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
