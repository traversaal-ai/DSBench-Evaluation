"""
Test script to verify Vertex AI authentication and connectivity
Run this after setting up Application Default Credentials
"""

import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def retry_with_backoff(func, max_retries=5, initial_delay=10):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_msg = str(e)
            
            # Check for quota/rate limit errors (429)
            is_quota_error = "429" in error_msg or "quota" in error_msg.lower() or "resource exhausted" in error_msg.lower()
            
            if is_quota_error and attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff: 10s, 20s, 40s, 80s, 160s
                print(f"   [RETRY] Quota exceeded (429). Waiting {delay}s... (attempt {attempt+1}/{max_retries})")
                time.sleep(delay)
                continue
            
            # For other errors or final attempt, raise immediately
            raise e
    
    raise Exception(f"Failed after {max_retries} retries")


def test_vertex_ai_auth():
    """Test Vertex AI authentication and basic connectivity"""

    print("=" * 80)
    print("VERTEX AI CONNECTION TEST")
    print("=" * 80)

    # Check environment variables
    print("\n1. Checking environment variables...")
    project_id = os.getenv("VERTEX_PROJECT_ID")
    location = os.getenv("VERTEX_LOCATION")
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI")

    print(f"   VERTEX_PROJECT_ID: {project_id}")
    print(f"   VERTEX_LOCATION: {location}")
    print(f"   GOOGLE_GENAI_USE_VERTEXAI: {use_vertex}")

    if not project_id or not location:
        print("   [ERROR] Environment variables not set!")
        return False

    print("   [OK] Environment variables configured")

    # Test Vertex AI initialization
    print("\n2. Initializing Vertex AI...")
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=project_id, location=location)
        print("   [OK] Vertex AI initialized successfully")
    except Exception as e:
        print(f"   [ERROR] Failed to initialize Vertex AI: {e}")
        return False

    # Test simple API call with Gemini (with retry logic)
    print("\n3. Testing API call with Gemini 2.0 Flash (with retry logic)...")
    try:
        model = GenerativeModel("gemini-2.0-flash-exp")
        
        # Wrap the API call in retry logic
        def make_api_call():
            response = model.generate_content(
                "Say 'Hello from Vertex AI!' and nothing else.",
                generation_config={"temperature": 0, "max_output_tokens": 20}
            )
            return response.text.strip()
        
        # Call with retry
        result = retry_with_backoff(make_api_call, max_retries=5, initial_delay=10)
        
        print(f"   Response: {result}")
        print("   [OK] API call successful!")

    except Exception as e:
        error_msg = str(e)
        print(f"   [ERROR] API call failed: {error_msg}")

        # Provide specific guidance based on error
        if "authentication" in error_msg.lower() or "credentials" in error_msg.lower():
            print("\n   [TIP] Authentication issue detected:")
            print("      - Make sure you ran: gcloud auth application-default login")
            print("      - Restart your Python kernel/terminal after authentication")
            print("      - Check credentials exist at:")
            print("        C:\\Users\\ustra\\AppData\\Roaming\\gcloud\\application_default_credentials.json")
        elif "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
            print("\n   [TIP] Rate limit/quota issue detected:")
            print("      - Check your Google Cloud project has billing enabled")
            print("      - Verify Vertex AI API quota limits")
            print("      - Wait a few minutes before trying again")

        return False

    print("\n" + "=" * 80)
    print("[SUCCESS] ALL TESTS PASSED - Vertex AI is ready to use!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_vertex_ai_auth()
    exit(0 if success else 1)