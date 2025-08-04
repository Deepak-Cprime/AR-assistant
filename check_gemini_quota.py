import google.generativeai as genai
import os
from datetime import datetime

# Configure with your API key
genai.configure(api_key="AIzaSyBZXHyHSezvefmyEa0Wimq4dEmQiQhcw9s")

print("Checking Gemini API Status...")
print(f"Time: {datetime.now()}")
print("-" * 50)

try:
    # Test with the same model used in the application
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print("Testing API connection...")
    response = model.generate_content("Hello, this is a test message.")
    
    print("API is working!")
    print(f"Response: {response.text[:100]}...")
    print(f"Response length: {len(response.text)} characters")
    
    # Test with a more complex query similar to your automation rule
    print("\nTesting complex query...")
    complex_response = model.generate_content(
        "Create a JavaScript automation rule that creates a bug when a user story is not in Done state"
    )
    
    print("Complex query working!")
    print(f"Complex response length: {len(complex_response.text)} characters")
    if len(complex_response.text) > 0:
        print(f"Complex response preview: {complex_response.text[:200]}...")
    else:
        print("WARNING: Complex query returned empty response!")
    
except Exception as e:
    error_msg = str(e)
    print(f"API Error: {error_msg}")
    
    # Check for specific error types
    if "quota" in error_msg.lower():
        print("QUOTA EXCEEDED! You've hit your API limits.")
        print("Solutions:")
        print("   - Wait for quota to reset (usually daily)")
        print("   - Upgrade to paid plan")
        print("   - Use a different API key")
    elif "limit" in error_msg.lower() or "429" in error_msg:
        print("RATE LIMIT EXCEEDED! Too many requests per minute.")
        print("Solutions:")
        print("   - Wait a few minutes before trying again")
        print("   - Reduce request frequency")
    elif "authentication" in error_msg.lower() or "401" in error_msg:
        print("AUTHENTICATION ERROR! API key issue.")
        print("Solutions:")
        print("   - Check if API key is correct")
        print("   - Verify API key has Gemini API access enabled")
    elif "blocked" in error_msg.lower() or "safety" in error_msg.lower():
        print("CONTENT BLOCKED! Safety filters triggered.")
        print("This might be why your automation rule query fails")
    else:
        print("Unknown error - check your internet connection and API key")

print("\n" + "=" * 50)
print("Quota check complete!")