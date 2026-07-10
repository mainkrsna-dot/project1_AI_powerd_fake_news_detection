"""
Test suite for Multilingual Features in Fake News Detection API - Iteration 3
Tests: Multilingual text detection, multilingual verify-news, language detection
"""
import pytest
import requests
import os
import time

# Get backend URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API_URL = f"{BASE_URL}/api"


class TestMultilingualTextDetection:
    """Test multilingual text detection endpoint"""
    
    def test_detect_text_hindi_returns_language_fields(self):
        """Test POST /api/detect-text with Hindi text returns detected_language and explanation_english"""
        hindi_text = "भारत ने चांद पर पानी की खोज की। यह एक ऐतिहासिक उपलब्धि है।"
        
        response = requests.post(
            f"{API_URL}/detect-text",
            json={"text": hindi_text},
            timeout=90
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check required fields exist
        assert "status" in data, "Response missing 'status' field"
        assert data["status"] in ["REAL", "FAKE", "UNKNOWN"], f"Invalid status: {data['status']}"
        
        assert "confidence" in data, "Response missing 'confidence' field"
        assert isinstance(data["confidence"], (int, float)), "Confidence should be numeric"
        assert 0 <= data["confidence"] <= 100, f"Confidence out of range: {data['confidence']}"
        
        assert "explanation" in data, "Response missing 'explanation' field"
        assert len(data["explanation"]) > 0, "Explanation should not be empty"
        
        # Check multilingual fields
        assert "detected_language" in data, "Response missing 'detected_language' field"
        assert data["detected_language"] in ["english", "hindi", "marathi", "tamil", "hinglish"], \
            f"Invalid detected_language: {data['detected_language']}"
        
        assert "explanation_english" in data, "Response missing 'explanation_english' field"
        assert len(data["explanation_english"]) > 0, "explanation_english should not be empty"
        
        print(f"✓ Hindi text detection works")
        print(f"  Status: {data['status']}, Confidence: {data['confidence']}%")
        print(f"  Detected Language: {data['detected_language']}")
        print(f"  Explanation (first 100 chars): {data['explanation'][:100]}...")
        print(f"  English Explanation (first 100 chars): {data['explanation_english'][:100]}...")
    
    def test_detect_text_english_returns_english_language(self):
        """Test POST /api/detect-text with English text returns 'english' as detected_language"""
        english_text = "Scientists have discovered a new species of deep-sea fish in the Pacific Ocean. The discovery was made during a research expedition."
        
        response = requests.post(
            f"{API_URL}/detect-text",
            json={"text": english_text},
            timeout=90
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "confidence" in data
        assert "explanation" in data
        assert "detected_language" in data
        assert "explanation_english" in data
        
        # For English text, detected_language should be 'english'
        assert data["detected_language"] == "english", \
            f"Expected 'english', got '{data['detected_language']}'"
        
        # For English, explanation and explanation_english should be similar
        # (they might not be exactly the same due to LLM variation)
        assert len(data["explanation_english"]) > 0
        
        print(f"✓ English text detection works")
        print(f"  Status: {data['status']}, Confidence: {data['confidence']}%")
        print(f"  Detected Language: {data['detected_language']}")
    
    def test_detect_text_marathi(self):
        """Test POST /api/detect-text with Marathi text"""
        marathi_text = "मुंबईत आज मोठा पाऊस पडला. अनेक भागात पाणी साचले आहे."
        
        response = requests.post(
            f"{API_URL}/detect-text",
            json={"text": marathi_text},
            timeout=90
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "detected_language" in data
        assert "explanation_english" in data
        assert len(data["explanation_english"]) > 0
        
        print(f"✓ Marathi text detection works")
        print(f"  Detected Language: {data['detected_language']}")
    
    def test_detect_text_hinglish(self):
        """Test POST /api/detect-text with Hinglish text"""
        hinglish_text = "Aaj ka weather bahut accha hai. Main office jaane ke liye ready hoon."
        
        response = requests.post(
            f"{API_URL}/detect-text",
            json={"text": hinglish_text},
            timeout=90
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "detected_language" in data
        assert "explanation_english" in data
        
        print(f"✓ Hinglish text detection works")
        print(f"  Detected Language: {data['detected_language']}")


class TestMultilingualVerifyNews:
    """Test multilingual verify-news endpoint"""
    
    def test_verify_news_hindi_claim(self):
        """Test POST /api/verify-news with Hindi claim returns multilingual response"""
        hindi_claim = "भारत दुनिया का सबसे बड़ा लोकतंत्र है"
        
        response = requests.post(
            f"{API_URL}/verify-news",
            json={"claim": hindi_claim},
            timeout=90
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert data["status"] in ["REAL", "FAKE", "UNCERTAIN"]
        
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        
        assert "explanation" in data
        assert len(data["explanation"]) > 0
        
        # Check multilingual fields
        assert "detected_language" in data, "Response missing 'detected_language' field"
        assert "explanation_english" in data, "Response missing 'explanation_english' field"
        assert len(data["explanation_english"]) > 0
        
        print(f"✓ Hindi claim verification works")
        print(f"  Status: {data['status']}, Confidence: {data['confidence']}%")
        print(f"  Detected Language: {data['detected_language']}")
        print(f"  English Explanation (first 100 chars): {data['explanation_english'][:100]}...")
    
    def test_verify_news_english_claim(self):
        """Test POST /api/verify-news with English claim"""
        english_claim = "The Great Wall of China is visible from space"
        
        response = requests.post(
            f"{API_URL}/verify-news",
            json={"claim": english_claim},
            timeout=90
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "detected_language" in data
        assert data["detected_language"] == "english"
        assert "explanation_english" in data
        
        print(f"✓ English claim verification works")
        print(f"  Status: {data['status']}, Confidence: {data['confidence']}%")


class TestAPIHealthAndExistingFeatures:
    """Verify existing features still work"""
    
    def test_api_health(self):
        """Test API root endpoint"""
        response = requests.get(f"{API_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        print("✓ API health check passed")
    
    def test_history_endpoint(self):
        """Test history endpoint still works"""
        response = requests.get(f"{API_URL}/history")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        print(f"✓ History endpoint works - Total: {data['total']}")
    
    def test_news_api_status(self):
        """Test news API status endpoint"""
        response = requests.get(f"{API_URL}/news-api-status")
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        print(f"✓ News API status endpoint works - Configured: {data['configured']}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_history(self):
        """Clean up test history entries"""
        response = requests.delete(f"{API_URL}/history")
        assert response.status_code == 200
        print("✓ Test cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
