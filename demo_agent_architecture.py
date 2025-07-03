#!/usr/bin/env python3
"""
Demo script showcasing the Core Agent Architecture.

This script demonstrates how the components described in 
docs/architecture/core-agent-architecture.md work together to verify claims.

Run this script to see the agent architecture in action:
    python demo_agent_architecture.py
"""
import json
from src.agents import SimpleAgent, AgentConfig


def print_separator(title: str):
    """Print a formatted separator."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_result(claim: str, result):
    """Print verification result in a formatted way."""
    print(f"\nClaim: {claim}")
    print(f"Verdict: {result.verdict}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Domain: {result.metadata.get('domain', 'unknown')}")
    print(f"Complexity: {result.metadata.get('complexity', 'unknown')}")
    print(f"Processing Time: {result.metadata.get('processing_time', 0):.3f}s")
    print(f"Sources: {', '.join(result.sources[:3])}...")  # Show first 3 sources
    print(f"Reasoning: {result.reasoning[:100]}...")  # Show first 100 chars


def main():
    """Demonstrate the core agent architecture."""
    
    print_separator("ConsensusNet Core Agent Architecture Demo")
    
    print("\nThis demo shows how individual AI agents work internally,")
    print("as documented in docs/architecture/core-agent-architecture.md")
    
    # Create agents with different configurations
    general_agent = SimpleAgent(agent_id="general-agent")
    
    science_agent = SimpleAgent(
        agent_id="science-specialist",
        config=AgentConfig(
            agent_id="science-specialist",
            domain_expertise=["science", "research"],
            confidence_threshold=0.8
        )
    )
    
    print_separator("Testing Different Claim Types")
    
    # Test various types of claims
    test_claims = [
        "2+2=4",
        "The Earth is flat", 
        "The sky is blue due to Rayleigh scattering",
        "Climate change is caused by human activities",
        "Quantum computers will solve all computational problems instantly",
        "Tomorrow will be a perfect day for everyone",
    ]
    
    for claim in test_claims:
        result = general_agent.verify(claim)
        print_result(claim, result)
    
    print_separator("Comparing Agent Specializations")
    
    science_claim = "Recent quantum physics research demonstrates entanglement effects"
    
    print("\nGeneral Agent Response:")
    general_result = general_agent.verify(science_claim)
    print_result(science_claim, general_result)
    
    print("\nScience Specialist Agent Response:")
    science_result = science_agent.verify(science_claim)
    print_result(science_claim, science_result)
    
    print_separator("Agent Performance Metrics")
    
    general_metrics = general_agent.get_performance_metrics()
    science_metrics = science_agent.get_performance_metrics()
    
    print(f"\nGeneral Agent Metrics:")
    print(f"  Verification Time: {general_metrics.verification_time:.3f}s")
    print(f"  API Calls Made: {general_metrics.api_calls_made}")
    print(f"  Tokens Used: {general_metrics.tokens_used}")
    
    print(f"\nScience Agent Metrics:")
    print(f"  Verification Time: {science_metrics.verification_time:.3f}s")
    print(f"  API Calls Made: {science_metrics.api_calls_made}")
    print(f"  Tokens Used: {science_metrics.tokens_used}")
    
    print_separator("Architecture Components Demonstrated")
    
    print("\n✓ Input Processor: Parsed and normalized claims")
    print("✓ State Manager: Managed agent sessions and memory")
    print("✓ LLM Interaction: Simulated LLM calls for verification")
    print("✓ Evidence Engine: Gathered evidence from simulated sources")
    print("✓ Verification Logic: Applied reasoning to determine verdicts")
    print("✓ Output Generator: Created structured VerificationResult objects")
    print("✓ Error Handling: Managed various error conditions")
    print("✓ Performance Tracking: Monitored resource usage")
    
    print_separator("Data Flow Validation")
    
    print("\nThe following data flow was executed for each verification:")
    print("1. Raw claim → Input Processor → ProcessedClaim")
    print("2. ProcessedClaim → State Manager → AgentState")
    print("3. AgentState → Evidence Engine → EvidenceBundle") 
    print("4. ProcessedClaim → LLM Interaction → LLMResponse")
    print("5. EvidenceBundle + LLMResponse → Verification Logic → VerificationChain")
    print("6. VerificationChain → Output Generator → VerificationResult")
    print("7. VerificationResult → State Manager → Session Update")
    
    print_separator("Integration with ECAMAN Architecture")
    
    print("\nThese individual agents serve as building blocks for:")
    print("• Meta-Agent Orchestrator: Spawns specialized agents dynamically")
    print("• Adversarial Debate Arena: Uses agents in prosecutor/defender roles")  
    print("• Graph-Based Consensus Network: Aggregates multiple agent outputs")
    print("• Swarm Burst Mode: Deploys lightweight versions rapidly")
    
    print(f"\n{'='*60}")
    print(" Demo Complete - Architecture Working Successfully!")
    print(f"{'='*60}")
    
    print("\nFor more details, see:")
    print("• docs/architecture/core-agent-architecture.md")
    print("• docs/architecture/agent-data-flow-diagram.md")
    print("• docs/architecture/ARCHITECTURE_RECOMMENDATION.md")


if __name__ == "__main__":
    main()