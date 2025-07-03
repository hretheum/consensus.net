"""
Demo script to showcase real LLM integration with ConsensusNet.

This script demonstrates:
1. Agent with simulation mode (default)
2. Agent with real LLM mode (if API keys available)  
3. Error handling and fallback behavior
"""

import os
from src.agents.simple_agent import SimpleAgent
from src.agents.agent_models import AgentConfig

def demo_llm_integration():
    """Demonstrate LLM integration capabilities."""
    
    print("=== ConsensusNet LLM Integration Demo ===\n")
    
    # Test claims for verification
    test_claims = [
        "The sky is blue",
        "The Earth is flat", 
        "2 plus 2 equals 4",
        "It's raining right now"
    ]
    
    print("1. Testing Simulation Mode (Default)")
    print("-" * 40)
    
    # Create agent with simulation mode (default)
    sim_agent = SimpleAgent("simulation-agent")
    
    for claim in test_claims[:2]:  # Test first 2 claims
        print(f"\nVerifying: '{claim}'")
        result = sim_agent.verify(claim)
        print(f"  Verdict: {result.verdict}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Reasoning: {result.reasoning[:100]}...")
    
    print("\n" + "="*60 + "\n")
    print("2. Testing Real LLM Mode")
    print("-" * 40)
    
    # Create agent with real LLM mode enabled
    real_llm_config = AgentConfig(
        agent_id="real-llm-agent",
        use_real_llm=True,
        primary_model="gpt-4o-mini"
    )
    
    real_agent = SimpleAgent("real-llm-agent", real_llm_config)
    
    # Check if real LLM is actually being used
    if hasattr(real_agent.llm_interaction, '_clients'):
        print("✅ Real LLM integration is active!")
        
        # Check available providers
        available_providers = real_agent.llm_interaction.get_available_providers()
        print(f"📡 Available providers: {[p.value for p in available_providers]}")
        
        # Note about API keys
        has_openai = os.getenv("OPENAI_API_KEY") is not None
        has_anthropic = os.getenv("ANTHROPIC_API_KEY") is not None
        
        print(f"🔑 OpenAI API Key: {'✅ Set' if has_openai else '❌ Not set'}")
        print(f"🔑 Anthropic API Key: {'✅ Set' if has_anthropic else '❌ Not set'}")
        
        if not has_openai and not has_anthropic:
            print("\n⚠️  No API keys found. Real LLM calls will fail gracefully.")
            print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test actual API calls.")
        
    else:
        print("🔄 Fell back to simulation mode")
        print("   (Real LLM integration not available)")
    
    # Test verification with real LLM agent
    for claim in test_claims[2:]:  # Test last 2 claims 
        print(f"\nVerifying: '{claim}'")
        try:
            result = real_agent.verify(claim)
            print(f"  Verdict: {result.verdict}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Reasoning: {result.reasoning[:100]}...")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "="*60 + "\n")
    print("3. Performance Comparison")
    print("-" * 40)
    
    # Compare performance
    sim_metrics = sim_agent.get_performance_metrics()
    real_metrics = real_agent.get_performance_metrics()
    
    print(f"Simulation Mode:")
    print(f"  - Verification time: {sim_metrics.verification_time:.3f}s")
    print(f"  - API calls made: {sim_metrics.api_calls_made}")
    print(f"  - Tokens used: {sim_metrics.tokens_used}")
    
    print(f"\nReal LLM Mode:")
    print(f"  - Verification time: {real_metrics.verification_time:.3f}s")
    print(f"  - API calls made: {real_metrics.api_calls_made}")
    print(f"  - Tokens used: {real_metrics.tokens_used}")
    
    print("\n✅ Demo completed successfully!")
    print("\n📋 Integration Features Demonstrated:")
    print("   ✅ Simulation mode (backward compatibility)")
    print("   ✅ Real LLM mode (when configured)")
    print("   ✅ Graceful fallback on errors")
    print("   ✅ Multiple provider support (OpenAI, Anthropic, Ollama)")
    print("   ✅ Error handling and retry logic")
    print("   ✅ Performance metrics tracking")


if __name__ == "__main__":
    demo_llm_integration()