"""
OpenRouter API Testing Script with Temperature Control and Cost Tracking
------------------------------------------------------------------------
This script tests the OpenRouter API with different models and temperature settings,
and tracks the cost of each request.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

key = os.getenv("OPENROUTER_API_KEY")
print(f"Key loaded: {key[:10]}...{key[-10:]}" if key else "❌ No key found")

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your-api-key-here")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Test models - mix of different providers
TEST_MODELS = [
    # "openai/gpt-5.2",
    "google/gemini-3-pro-preview",
    # "anthropic/claude-opus-4.5",
    # "deepseek/deepseek-v3.2",
    # "z-ai/glm-4.7",
    # "xiaomi/mimo-v2-flash:free"
]


# Pricing information (per million tokens)
MODEL_PRICING = {
    "openai/gpt-5.2": {
        "input": 1.75,   # $1.75 per 1M input tokens
        "output": 14.0,  # $14 per 1M output tokens
    },
    "google/gemini-3-pro-preview": {
        "input": 2.0,
        "output": 12.0,
    },
    "anthropic/claude-opus-4.5": {
        "input": 5.0,
        "output": 25.0,
    },
    "z-ai/glm-4.7": {
        "input": 0.40,
        "output": 1.50,
    },
    "deepseek/deepseek-v3.2": {
        "input": 0.25,
        "output": 0.38,
    },
    "xiaomi/mimo-v2-flash:free": {
        "input": 0.0,
        "output": 0.0,
    },
}

# Temperature values to test
TEMPERATURE_VALUES = [0.0, 0.0, 1.0]

# Test prompt
TEST_PROMPT = "Write a creative one-sentence story about a robot."


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the cost of a request."""
    pricing = MODEL_PRICING.get(model, {"input": 0, "output": 0})
    
    # Cost = (tokens / 1,000,000) * price_per_million
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    
    return input_cost + output_cost


class OpenRouterClient:
    """Simple OpenRouter API client."""
    
    def __init__(self, api_key: str, base_url: str = OPENROUTER_BASE_URL):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: int = 500,
        timeout: int = 120,
        seed: int = 42,
        force_provider: bool = True,  # New parameter
    ) -> Dict[str, Any]:
        """Send a chat completion request."""
        import requests
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
    

        if temperature is not None:
            payload["temperature"] = temperature
        
        # Seed might not be supported by OpenRouter for all models
        # Only add it if explicitly testing determinism
        if seed is not None:
            payload["seed"] = seed

        # Add provider routing if requested
        if force_provider:
            # Extract provider from model name (e.g., "openai/gpt-4o" -> "OpenAI")
            provider_map = {
                "openai": "OpenAI",
                "anthropic": "Anthropic",
                "google": "Google",
                "deepseek": "Deepseek",
                "z-ai": "Zhipu",
            }
            
            model_prefix = model.split("/")[0].lower()
            provider_name = provider_map.get(model_prefix)
            
            if provider_name:
                payload["provider"] = {
                    "order": [provider_name],
                    "allow_fallbacks": False
                }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_models(self) -> Dict[str, Any]:
        """Fetch available models and their parameters."""
        import requests
        
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


def test_temperature_control(
    client: OpenRouterClient,
    model: str,
    temperatures: List[float],
    prompt: str,
) -> List[Dict[str, Any]]:
    """Test a model with different temperature settings."""
    results = []
    
    print(f"\n{'='*80}")
    print(f"Testing model: {model}")
    print(f"{'='*80}")
    
    for temp in temperatures:
        print(f"\n  Temperature: {temp}")
        
        messages = [{"role": "user", "content": prompt}]
        
        response = client.chat_completion(
            model=model,
            messages=messages,
            temperature=temp,
        )
        
        if "error" in response:
            print(f"  ❌ Error: {response['error']}")
            results.append({
                "model": model,
                "temperature": temp,
                "error": response["error"],
                "cost": 0.0,
            })
        else:
            # Replace lines 160-193 with this updated version:
            try:
                message = response["choices"][0]["message"]
                content = message.get("content", "")
                reasoning = message.get("reasoning", "")
                
                # Handle reasoning models - combine reasoning + content
                if reasoning and not content:
                    # Reasoning model with no final answer
                    display_content = f"🧠 {reasoning}"
                elif reasoning and content:
                    # Has both reasoning and answer
                    display_content = f"🧠 Reasoning: {reasoning}\n  💡 Answer: {content}"
                elif content:
                    # Regular response
                    display_content = content
                else:
                    # Completely empty
                    print(f"  ⚠ Empty response. Message keys: {message.keys()}")
                    display_content = "[Empty response]"
                
                usage = response.get("usage", {})
                
                # Calculate cost
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                cost = calculate_cost(model, input_tokens, output_tokens)
                
                print(f"  ✓ Response: \n{display_content}")
                print(f"  Tokens: Input={input_tokens}, Output={output_tokens}, Total={usage.get('total_tokens', 'N/A')}")
                
                # Show reasoning tokens if present
                completion_details = usage.get("completion_tokens_details", {})
                if completion_details.get("reasoning_tokens", 0) > 0:
                    print(f"  🧠 Reasoning tokens: {completion_details['reasoning_tokens']}")
                
                print(f"  💰 Cost: ${cost:.6f}")
                
                results.append({
                    "model": model,
                    "temperature": temp,
                    "response": content,
                    "reasoning": reasoning,  # Add this field
                    "full_response": display_content,
                    "usage": usage,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": cost,
                    "model_used": response.get("model"),
                })
            except (KeyError, IndexError) as e:
                print(f"  ❌ Unexpected response format: {e}")
                results.append({
                    "model": model,
                    "temperature": temp,
                    "error": f"Invalid response format: {e}",
                    "raw_response": response,
                    "cost": 0.0,
                })
        
        # Rate limiting - be nice to the API
        time.sleep(1)
    
    return results


def check_temperature_support(client: OpenRouterClient, models: List[str]) -> Dict[str, Any]:
    """Check which models officially support temperature parameter."""
    print("\n" + "="*80)
    print("CHECKING TEMPERATURE SUPPORT FOR MODELS")
    print("="*80)
    
    models_info = client.get_models()
    
    if "error" in models_info:
        print(f"❌ Error fetching model info: {models_info['error']}")
        return {}
    
    support_info = {}
    
    for model_name in models:
        # Find model in the list
        model_data = None
        for m in models_info.get("data", []):
            if m.get("id") == model_name:
                model_data = m
                break
        
        if model_data:
            # Check if temperature is in supported parameters
            supports_temp = "temperature" in str(model_data).lower()
            
            # Add pricing info
            pricing = MODEL_PRICING.get(model_name, {"input": 0, "output": 0})
            
            support_info[model_name] = {
                "supports_temperature": supports_temp,
                "context_length": model_data.get("context_length"),
                "pricing": pricing,
            }
            
            status = "✓ Supports" if supports_temp else "⚠ May not support"
            print(f"{status} temperature: {model_name}")
            print(f"  💰 Pricing: ${pricing['input']}/M input, ${pricing['output']}/M output")
        else:
            print(f"⚠ Model not found in API: {model_name}")
            support_info[model_name] = {"error": "Model not found"}
    
    return support_info


# Replace the analyze_temperature_variance function (lines 263-290) with:
def analyze_temperature_variance(results: List[Dict[str, Any]]) -> None:
    """Analyze if temperature actually affects output."""
    print("\n" + "="*80)
    print("TEMPERATURE VARIANCE ANALYSIS")
    print("="*80)
    
    # Group by model
    by_model = {}
    for r in results:
        model = r.get("model")
        if model not in by_model:
            by_model[model] = []
        by_model[model].append(r)
    
    for model, model_results in by_model.items():
        print(f"\n{model}:")
        
        # Separate by temperature
        temp_0_responses = [r.get("full_response", "") for r in model_results 
                           if r.get("temperature") == 0.0 and "full_response" in r]
        temp_1_responses = [r.get("full_response", "") for r in model_results 
                           if r.get("temperature") == 1.0 and "full_response" in r]
        
        # Check temp 0 consistency (should be identical)
        if len(temp_0_responses) >= 2:
            if temp_0_responses[0] == temp_0_responses[1]:
                print(f"  ✓ Temperature 0.0: Consistent (deterministic)")
            else:
                print(f"  ⚠ Temperature 0.0: Inconsistent (should be identical!)")
        
        # Check if temp 1 differs from temp 0
        if temp_0_responses and temp_1_responses:
            if temp_1_responses[0] != temp_0_responses[0]:
                print(f"  ✓ Temperature 1.0: Different from 0.0 (working)")
            else:
                print(f"  ❌ Temperature 1.0: Same as 0.0 (NOT working)")
        
        # Overall variance
        all_responses = temp_0_responses + temp_1_responses
        unique_responses = len(set(all_responses))
        total_tests = len(all_responses)
        
        if total_tests > 0:
            print(f"  Total unique responses: {unique_responses}/{total_tests}")
        else:
            print(f"  ❌ No successful responses")


def print_cost_summary(results: List[Dict[str, Any]]) -> None:
    """Print a summary of costs."""
    print("\n" + "="*80)
    print("COST SUMMARY")
    print("="*80)
    
    # Group by model
    by_model = {}
    for r in results:
        model = r.get("model")
        if model not in by_model:
            by_model[model] = []
        by_model[model].append(r)
    
    total_cost = 0.0
    
    for model, model_results in by_model.items():
        model_cost = sum(r.get("cost", 0.0) for r in model_results)
        successful_requests = len([r for r in model_results if "response" in r])
        
        print(f"\n{model}:")
        print(f"  Requests: {successful_requests}/{len(model_results)}")
        print(f"  💰 Total cost: ${model_cost:.6f}")
        
        if successful_requests > 0:
            avg_cost = model_cost / successful_requests
            print(f"  💰 Average cost per request: ${avg_cost:.6f}")
        
        total_cost += model_cost
    
    print(f"\n{'='*80}")
    print(f"💰 GRAND TOTAL: ${total_cost:.6f}")
    print(f"{'='*80}")


def main():
    """Main test function."""
    print("OpenRouter API Temperature Testing Script with Cost Tracking")
    print("=" * 80)
    
    # Initialize client
    client = OpenRouterClient(OPENROUTER_API_KEY)
    
    # Check temperature support (requires requests library)
    try:
        support_info = check_temperature_support(client, TEST_MODELS)
    except ImportError:
        print("\n⚠ Install 'requests' library to check temperature support")
        support_info = {}
    
    # Test each model with different temperatures
    all_results = []
    
    for model in TEST_MODELS:
        results = test_temperature_control(
            client=client,
            model=model,
            temperatures=TEMPERATURE_VALUES,
            prompt=TEST_PROMPT,
        )
        all_results.extend(results)
    
    # Analyze variance
    analyze_temperature_variance(all_results)
    
    # Print cost summary
    print_cost_summary(all_results)
    
    # Save results
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "test_results")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"openrouter_temperature_test_{int(time.time())}.json")
    with open(output_file, "w") as f:
        json.dump({
            "test_info": {
                "timestamp": time.time(),
                "prompt": TEST_PROMPT,
                "temperatures": TEMPERATURE_VALUES,
                "models": TEST_MODELS,
            },
            "support_info": support_info,
            "results": all_results,
            "total_cost": sum(r.get("cost", 0.0) for r in all_results),
        }, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Results saved to: \n{output_file}")
    print(f"{'='*80}")


if __name__ == "__main__":
    # Check for requests library
    try:
        import requests
        main()
    except ImportError:
        print("❌ This script requires the 'requests' library.")
        print("Install it with: pip install requests")