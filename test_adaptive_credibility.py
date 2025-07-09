#!/usr/bin/env python3
"""
Test script for Adaptive Source Credibility Evolution system
"""
import asyncio
import os
from datetime import datetime

# Test if API keys are configured
print("=== Checking API Configuration ===")
api_keys = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    "NEWSAPI_KEY": os.getenv("NEWSAPI_KEY"),
    "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
    "GOOGLE_CSE_ID": os.getenv("GOOGLE_CSE_ID")
}

for key, value in api_keys.items():
    status = "✅ Configured" if value else "❌ Not configured"
    print(f"{key}: {status}")

print("\n=== Testing Evidence Sources ===")

async def test_evidence_sources():
    from src.services.evidence_service import evidence_service
    from src.agents.agent_models import ProcessedClaim, ClaimComplexity
    
    # Test claim
    test_claim = ProcessedClaim(
        original_text="COVID-19 vaccines are safe and effective",
        normalized_text="covid-19 vaccines are safe and effective",
        claim_type="factual",
        domain="health",
        entities=["COVID-19", "vaccines"],
        complexity=ClaimComplexity.MODERATE,
        language="en"
    )
    
    async with evidence_service as service:
        print("\n1. Testing Wikipedia...")
        try:
            wiki_results = await service.search_wikipedia("COVID-19 vaccine", limit=2)
            print(f"   ✅ Found {len(wiki_results)} Wikipedia results")
            if wiki_results:
                print(f"   - Credibility: {wiki_results[0].credibility_score}")
                print(f"   - Content preview: {wiki_results[0].content[:100]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n2. Testing PubMed...")
        try:
            pubmed_results = await service.search_pubmed("COVID-19 vaccine safety", limit=2)
            print(f"   ✅ Found {len(pubmed_results)} PubMed results")
            if pubmed_results:
                print(f"   - Credibility: {pubmed_results[0].credibility_score}")
                print(f"   - Content preview: {pubmed_results[0].content[:100]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n3. Testing arXiv...")
        try:
            arxiv_results = await service.search_arxiv("machine learning", limit=2)
            print(f"   ✅ Found {len(arxiv_results)} arXiv results")
            if arxiv_results:
                print(f"   - Credibility: {arxiv_results[0].credibility_score}")
                print(f"   - Content preview: {arxiv_results[0].content[:100]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        if api_keys["NEWSAPI_KEY"]:
            print("\n4. Testing NewsAPI...")
            try:
                news_results = await service.search_news("artificial intelligence", limit=2)
                print(f"   ✅ Found {len(news_results)} news results")
                if news_results:
                    print(f"   - Credibility: {news_results[0].credibility_score}")
                    print(f"   - Source: {news_results[0].source}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print("\n4. Skipping NewsAPI (no API key)")
        
        if api_keys["GOOGLE_API_KEY"] and api_keys["GOOGLE_CSE_ID"]:
            print("\n5. Testing Google Search...")
            try:
                google_results = await service.search_google("climate change facts", limit=2)
                print(f"   ✅ Found {len(google_results)} Google results")
                if google_results:
                    print(f"   - Credibility: {google_results[0].credibility_score}")
                    print(f"   - Source: {google_results[0].source}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print("\n5. Skipping Google Search (no API keys)")
        
        # Test full evidence gathering
        print("\n6. Testing Full Evidence Gathering...")
        try:
            evidence_bundle = await service.gather_evidence(test_claim, max_sources=5)
            print(f"   ✅ Evidence quality: {evidence_bundle.overall_quality:.2f}")
            print(f"   - Supporting: {len(evidence_bundle.supporting_evidence)}")
            print(f"   - Contradicting: {len(evidence_bundle.contradicting_evidence)}")
            print(f"   - Neutral: {len(evidence_bundle.neutral_evidence)}")
            print(f"   - Sources used: {evidence_bundle.metadata.get('sources_used', [])}")
            print(f"   - Requires LLM escalation: {evidence_bundle.metadata.get('requires_llm_escalation', False)}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

print("\n=== Testing LLM Service with Adaptive Routing ===")

async def test_llm_service():
    from src.services.llm_service import llm_service
    from src.agents.agent_models import LLMRequest
    from src.config.llm_config import ClaimComplexity, PrivacyLevel, UrgencyLevel
    
    if not (api_keys["OPENAI_API_KEY"] or api_keys["ANTHROPIC_API_KEY"]):
        print("❌ No LLM API keys configured, skipping LLM tests")
        return
    
    async with llm_service as service:
        # Test 1: High quality evidence (should use cheaper model)
        print("\n1. Testing with high quality evidence (0.85)...")
        request = LLMRequest(
            prompt="Is the Earth round? Provide a brief answer.",
            max_tokens=100,
            temperature=0.3
        )
        
        try:
            response = await service.call_llm_with_fallback(
                request,
                complexity=ClaimComplexity.SIMPLE,
                evidence_quality=0.85
            )
            print(f"   ✅ Model used: {response.model_used}")
            print(f"   - Confidence: {response.confidence}")
            print(f"   - Evidence quality affected routing: {response.metadata.get('confidence_adjusted', False)}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: Low quality evidence (should escalate to better model)
        print("\n2. Testing with low quality evidence (0.45)...")
        request = LLMRequest(
            prompt="What are the long-term effects of a new experimental treatment?",
            max_tokens=100,
            temperature=0.3
        )
        
        try:
            response = await service.call_llm_with_fallback(
                request,
                complexity=ClaimComplexity.MODERATE,
                evidence_quality=0.45,
                requires_escalation=True
            )
            print(f"   ✅ Model used: {response.model_used}")
            print(f"   - Models tried: {response.metadata.get('models_tried', [])}")
            print(f"   - Escalation applied: Yes")
        except Exception as e:
            print(f"   ❌ Error: {e}")

print("\n=== Testing Complete Verification Pipeline ===")

async def test_verification_pipeline():
    from src.agents.enhanced_agent import EnhancedAgent
    
    agent = EnhancedAgent()
    
    test_claims = [
        ("The Earth is flat", "simple", "Should be FALSE with high confidence"),
        ("COVID-19 vaccines modify DNA", "health", "Should be FALSE with academic sources"),
        ("Python is a programming language", "tech", "Should be TRUE with high confidence")
    ]
    
    for claim, domain, expected in test_claims:
        print(f"\nTesting: '{claim}'")
        print(f"Domain: {domain}, Expected: {expected}")
        
        try:
            result = await agent.verify(claim)
            print(f"✅ Verdict: {result.verdict}")
            print(f"   - Confidence: {result.confidence:.2f}")
            print(f"   - Evidence quality: {result.metadata.get('evidence_quality', 'N/A')}")
            print(f"   - Sources: {result.metadata.get('sources_consulted', [])}")
            print(f"   - LLM model: {result.metadata.get('llm_model', 'N/A')}")
            print(f"   - Reasoning preview: {result.reasoning[:100]}...")
        except Exception as e:
            print(f"❌ Error: {e}")

# Run all tests
async def main():
    await test_evidence_sources()
    await test_llm_service()
    await test_verification_pipeline()
    
    print("\n=== Testing Complete ===")
    print("\nTo see the adaptive credibility in action, run multiple verifications")
    print("and monitor the source statistics at: http://localhost:8000/api/sources/stats")

if __name__ == "__main__":
    asyncio.run(main())