import requests
import sys
import base64
import io
from datetime import datetime
from PIL import Image
import json

class FakeNewsDetectionTester:
    def __init__(self, base_url="https://detect-real-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=60)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers, timeout=60)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"Response: {json.dumps(response_data, indent=2)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_api_health(self):
        """Test API health endpoint"""
        return self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )

    def test_text_detection(self):
        """Test text fake news detection"""
        sample_text = """
        BREAKING: Scientists have discovered that drinking water backwards can cure all diseases! 
        This revolutionary method, discovered by Dr. John Smith at the University of Nowhere, 
        has been proven to work 100% of the time. The medical establishment doesn't want you 
        to know this simple trick that doctors hate!
        """
        
        return self.run_test(
            "Text Detection",
            "POST",
            "detect-text",
            200,
            data={"text": sample_text}
        )

    def test_text_detection_real_news(self):
        """Test text detection with real news"""
        real_news = """
        The Federal Reserve announced today that it will maintain interest rates at their current level 
        following the latest Federal Open Market Committee meeting. Fed Chair Jerome Powell stated that 
        the decision reflects ongoing concerns about inflation while supporting continued economic growth. 
        The announcement was made at 2 PM EST and was widely anticipated by financial markets.
        """
        
        return self.run_test(
            "Text Detection - Real News",
            "POST",
            "detect-text",
            200,
            data={"text": real_news}
        )

    def create_test_image(self):
        """Create a simple test image with real visual features"""
        # Create a 200x200 image with some visual features
        img = Image.new('RGB', (200, 200), color='white')
        pixels = img.load()
        
        # Add some patterns and features
        for i in range(200):
            for j in range(200):
                # Create a gradient with some noise
                r = int((i / 200) * 255)
                g = int((j / 200) * 255)
                b = int(((i + j) / 400) * 255)
                pixels[i, j] = (r, g, b)
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        return img_buffer.getvalue()

    def test_image_detection(self):
        """Test image deepfake detection"""
        try:
            # Create test image
            image_data = self.create_test_image()
            
            files = {
                'file': ('test_image.jpg', image_data, 'image/jpeg')
            }
            
            return self.run_test(
                "Image Detection",
                "POST",
                "detect-image",
                200,
                files=files
            )
        except Exception as e:
            print(f"Error creating test image: {e}")
            return False, {}

    def create_test_video(self):
        """Create a simple test video file (mock)"""
        # For testing purposes, we'll create a minimal MP4-like file
        # In a real scenario, you'd use a proper video file
        video_header = b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom'
        return video_header + b'\x00' * 1000  # Minimal mock video data

    def test_video_detection(self):
        """Test video deepfake detection"""
        try:
            # Create mock video data
            video_data = self.create_test_video()
            
            files = {
                'file': ('test_video.mp4', video_data, 'video/mp4')
            }
            
            return self.run_test(
                "Video Detection",
                "POST",
                "detect-video",
                200,
                files=files
            )
        except Exception as e:
            print(f"Error creating test video: {e}")
            return False, {}

    def test_claim_verification(self):
        """Test claim verification endpoint"""
        test_claim = "The Earth is round and orbits around the Sun."
        
        return self.run_test(
            "Claim Verification",
            "POST",
            "verify-claim",
            200,
            data={"claim": test_claim}
        )

def main():
    print("🚀 Starting Fake News Detection API Tests")
    print("=" * 50)
    
    tester = FakeNewsDetectionTester()
    
    # Run all tests
    tests = [
        tester.test_api_health,
        tester.test_text_detection,
        tester.test_text_detection_real_news,
        tester.test_image_detection,
        tester.test_video_detection,
        tester.test_claim_verification
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            tester.failed_tests.append({
                "test": test.__name__,
                "error": str(e)
            })
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 Test Summary:")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ Failed Tests:")
        for failure in tester.failed_tests:
            print(f"  - {failure}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())