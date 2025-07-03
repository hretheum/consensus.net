"""
Manual test script for LLM integration with API keys.

This script can be used to test real API calls when API keys are available.
Run with: python manual_llm_test.py
"""

import os
import asyncio
from src.llm.llm_client import RealLLMInteraction
from src.agents.agent_models import LLMRequest
from src.config.llm_config import LLMModel

async def test_real_api_calls():
    """Test real API calls if credentials are available."""
    
    print("=== Manual LLM API Test ===\n")
    
    # Initialize the LLM client
    llm_client = RealLLMInteraction()
    
    # Check what providers are available
    available_providers = llm_client.get_available_providers()
    print(f"Available providers: {[p.value for p in available_providers]}")
    
    # Test claims
    test_claims = [
        "The Earth is round",
        "Water boils at 100 degrees Celsius at sea level",
        "The moon is made of cheese"
    ]
    
    # Test each available model
    models_to_test = []
    
    if os.getenv("OPENAI_API_KEY"):
        models_to_test.append(("gpt-4o-mini", "OpenAI GPT-4o-mini"))
        print("✅ OpenAI API key found")
    else:
        print("❌ OpenAI API key not found")
    
    if os.getenv("ANTHROPIC_API_KEY"):
        models_to_test.append(("claude-3-haiku-20240307", "Anthropic Claude 3 Haiku"))
        print("✅ Anthropic API key found")
    else:
        print("❌ Anthropic API key not found")
    
    # Ollama is always available (local)
    models_to_test.append(("llama3.2", "Ollama Llama 3.2"))
    print("✅ Ollama available (local)")
    
    if not models_to_test:
        print("\n⚠️  No API keys found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test.")
        return
    
    print(f"\n🧪 Testing {len(models_to_test)} models with {len(test_claims)} claims\n")
    
    for model_id, model_name in models_to_test:
        print(f"--- Testing {model_name} ---")
        
        for claim in test_claims:
            print(f"  Claim: '{claim}'")
            
            try:
                # Create verification prompt
                prompt = llm_client.generate_verification_prompt(
                    type('MockClaim', (), {
                        'original_text': claim,
                        'domain': 'science',
                        'complexity': type('MockComplexity', (), {'value': 'simple'})(),
                        'context': {}
                    })()
                )
                
                # Create LLM request
                request = LLMRequest(
                    prompt=prompt,
                    model=model_id,
                    parameters={}
                )
                
                # Make API call
                response = await llm_client.call_llm_async(request)
                
                print(f"    ✅ Success!")
                print(f"    📝 Response: {response.content[:100]}...")
                print(f"    🎯 Confidence: {response.confidence}")
                print(f"    🔢 Tokens: {response.tokens_used}")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                
                # For Ollama, this might mean it's not running
                if "llama3.2" in model_id and "connection" in str(e).lower():
                    print("    💡 Tip: Make sure Ollama is running: `ollama serve`")
            
            print()
        
        print()

def test_synchronous_calls():
    """Test synchronous wrapper for compatibility."""
    print("=== Testing Synchronous Calls ===\n")
    
    llm_client = RealLLMInteraction()
    
    request = LLMRequest(
        prompt="Is the sky blue? Please answer with TRUE or FALSE and explain.",
        model="gpt-4o-mini",
        parameters={}
    )
    
    try:
        # This should work even if async loop is running
        response = llm_client.call_llm(request)
        print("✅ Synchronous call successful")
        print(f"Response: {response.content[:100]}...")
    except Exception as e:
        print(f"❌ Synchronous call failed: {e}")

if __name__ == "__main__":
    print("This script tests real LLM API calls.")
    print("Make sure to set your API keys as environment variables:")
    print("  export OPENAI_API_KEY='your-key'")
    print("  export ANTHROPIC_API_KEY='your-key'")
    print("  # Ollama requires local installation")
    print()
    
    # Test async calls
    asyncio.run(test_real_api_calls())
    
    # Test sync calls
    test_synchronous_calls()
    
    print("✅ Manual testing completed!")
    print("\n💡 To run with actual API keys:")
    print("   OPENAI_API_KEY=sk-... python manual_llm_test.py")