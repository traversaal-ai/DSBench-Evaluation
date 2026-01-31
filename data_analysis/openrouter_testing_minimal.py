"""
Minimal OpenRouter API Test Script
Uses OpenAI-compatible interface
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client with OpenRouter
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# Test with a model
# model = "z-ai/glm-4.7"
# model = "google/gemini-3-pro-preview"
# model = "openai/gpt-5.2"
# model = "anthropic/claude-opus-4.5"
# model = "deepseek/deepseek-v3.2"
# model = "xiaomi/mimo-v2-flash"
model = "deepseek/deepseek-r1-0528:free"


response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "user", "content": "Say hello in one sentence"}
    ],
    temperature=0,
)

print(f"Model: {model}")
print(f"Response: {response.choices[0].message.content}")
print(f"Tokens used: {response.usage.total_tokens}")