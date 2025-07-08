"""
Specialized Verification Agents

Domain-specific agents that provide specialized verification capabilities:
- ScienceAgent: Scientific claims and research papers
- NewsAgent: Current events with recency bias
- TechAgent: Technical documentation and specifications
"""

import asyncio
import time
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from agents.enhanced_agent import EnhancedAgent
from agents.verification_result import VerificationResult
from agents.agent_models import ProcessedClaim, Evidence, EvidenceBundle
from services.evidence_service import EvidenceService

from consensus.communication.message_passing import (
    AgentMessage, MessageType, message_bus, create_verification_result
)
from consensus.communication.agent_discovery import (
    AgentProfile, AgentType, CapabilityType, AgentCapability
)


class SpecializedAgent(EnhancedAgent):
    """
    Base class for specialized verification agents.
    
    Extends EnhancedAgent with domain-specific capabilities and
    integration with the multi-agent communication system.
    """
    
    def __init__(self, agent_id: str, agent_type: AgentType, domain_specialization: str):
        """Initialize specialized agent."""
        super().__init__(agent_id)
        
        self.agent_type = agent_type
        self.domain_specialization = domain_specialization
        self.specialization_confidence = 0.8
        
        # Multi-agent communication
        self.message_bus = message_bus
        self.received_messages: List[AgentMessage] = []
        
        # Performance tracking
        self.specialization_stats = {
            "domain_requests": 0,
            "successful_verifications": 0,
            "collaboration_requests": 0,
            "evidence_shared": 0
        }
        
        # Register message handler
        self.message_bus.register_agent(self.agent_id, self.handle_message)
    
    async def handle_message(self, message: AgentMessage) -> None:
        """Handle incoming messages from other agents."""
        try:
            self.received_messages.append(message)
            
            if message.message_type == MessageType.VERIFICATION_REQUEST:
                await self._handle_verification_request(message)
            elif message.message_type == MessageType.HELP_REQUEST:
                await self._handle_help_request(message)
            elif message.message_type == MessageType.EVIDENCE_REQUEST:
                await self._handle_evidence_request(message)
                
        except Exception as e:
            print(f"Error handling message in {self.agent_id}: {e}")
    
    async def _handle_verification_request(self, message: AgentMessage) -> None:
        """Handle verification request from AgentPoolManager."""
        try:
            claim = message.payload.get("claim", "")
            if not claim:
                return
            
            print(f"{self.agent_id} received verification request: {claim[:50]}...")
            
            # Perform verification
            result = await self.verify_async(claim)
            
            # Send result back
            response = create_verification_result(
                sender_id=self.agent_id,
                result=result,
                conversation_id=message.conversation_id,
                recipient_id=message.sender_id
            )
            
            await self.message_bus.send_message(response)
            
            # Update stats
            self.specialization_stats["domain_requests"] += 1
            if result.verdict != "ERROR":
                self.specialization_stats["successful_verifications"] += 1
                
        except Exception as e:
            print(f"Error processing verification request in {self.agent_id}: {e}")
    
    async def _handle_help_request(self, message: AgentMessage) -> None:
        """Handle help request from another agent."""
        self.specialization_stats["collaboration_requests"] += 1
        # Implementation depends on specific help type
        pass
    
    async def _handle_evidence_request(self, message: AgentMessage) -> None:
        """Handle evidence sharing request."""
        self.specialization_stats["evidence_shared"] += 1
        # Implementation depends on evidence type
        pass
    
    @abstractmethod
    async def get_specialized_evidence(self, claim: ProcessedClaim) -> EvidenceBundle:
        """Get domain-specific evidence for a claim."""
        pass
    
    def get_agent_profile(self) -> AgentProfile:
        """Get agent profile for registration."""
        profile = AgentProfile(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            display_name=f"{self.agent_type.value.title()} Agent",
            description=f"Specialized agent for {self.domain_specialization}"
        )
        
        # Add domain expertise
        profile.domain_expertise[self.domain_specialization] = self.specialization_confidence
        
        # Add specialized capabilities
        self._add_specialized_capabilities(profile)
        
        return profile
    
    @abstractmethod
    def _add_specialized_capabilities(self, profile: AgentProfile) -> None:
        """Add agent-specific capabilities to profile."""
        pass
    
    def get_specialization_stats(self) -> Dict[str, Any]:
        """Get specialization-specific statistics."""
        return {
            **self.specialization_stats,
            "domain": self.domain_specialization,
            "confidence": self.specialization_confidence,
            "message_count": len(self.received_messages)
        }


class ScienceAgent(SpecializedAgent):
    """
    Agent specialized in scientific claims and research papers.
    
    Capabilities:
    - PubMed search for peer-reviewed papers
    - ArXiv search for preprints
    - Scientific methodology analysis
    - Statistical significance checking
    """
    
    def __init__(self, agent_id: str = "science_agent"):
        """Initialize science agent."""
        super().__init__(agent_id, AgentType.SCIENCE, "science")
        
        # Science-specific configuration
        self.pubmed_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.arxiv_base_url = "http://export.arxiv.org/api/query"
        self.max_papers_per_search = 5
        
        # Science keywords for detection
        self.science_keywords = [
            "study", "research", "experiment", "data", "analysis",
            "peer-reviewed", "journal", "publication", "findings",
            "hypothesis", "methodology", "results", "conclusion",
            "p-value", "significance", "correlation", "causation"
        ]
    
    async def get_specialized_evidence(self, claim: ProcessedClaim) -> EvidenceBundle:
        """Get scientific evidence from PubMed and ArXiv."""
        try:
            all_evidence = []
            
            # Search PubMed for peer-reviewed papers
            pubmed_evidence = await self._search_pubmed(claim.original_text)
            all_evidence.extend(pubmed_evidence)
            
            # Search ArXiv for preprints
            arxiv_evidence = await self._search_arxiv(claim.original_text)
            all_evidence.extend(arxiv_evidence)
            
            # Categorize evidence
            supporting = []
            contradicting = []
            neutral = []
            
            for evidence in all_evidence:
                # Simple categorization based on keywords
                if self._supports_claim(evidence.content, claim.original_text):
                    supporting.append(evidence)
                elif self._contradicts_claim(evidence.content, claim.original_text):
                    contradicting.append(evidence)
                else:
                    neutral.append(evidence)
            
            return EvidenceBundle(
                supporting_evidence=supporting,
                contradicting_evidence=contradicting,
                neutral_evidence=neutral,
                overall_quality=0.9  # High quality for scientific sources
            )
            
        except Exception as e:
            print(f"Error gathering scientific evidence: {e}")
            return EvidenceBundle(
                supporting_evidence=[],
                contradicting_evidence=[],
                neutral_evidence=[],
                overall_quality=0.0
            )
    
    async def _search_pubmed(self, query: str) -> List[Evidence]:
        """Search PubMed for relevant scientific papers."""
        evidence_list = []
        
        try:
            # Simulate PubMed search (in production, use actual API)
            simulated_papers = [
                {
                    "title": f"Scientific study on: {query}",
                    "abstract": f"Research findings related to {query}. This study provides peer-reviewed evidence.",
                    "journal": "Journal of Science",
                    "pmid": "12345678"
                },
                {
                    "title": f"Meta-analysis of {query}",
                    "abstract": f"Comprehensive meta-analysis examining {query} across multiple studies.",
                    "journal": "Nature Reviews",
                    "pmid": "87654321"
                }
            ]
            
            for paper in simulated_papers:
                evidence = Evidence(
                    content=f"{paper['title']}. {paper['abstract']}",
                    source="pubmed.ncbi.nlm.nih.gov",
                    credibility_score=0.95,  # High credibility for peer-reviewed
                    relevance_score=0.8,
                    timestamp=datetime.now(),
                    metadata={
                        "pmid": paper["pmid"],
                        "journal": paper["journal"],
                        "source_type": "peer_reviewed"
                    }
                )
                evidence_list.append(evidence)
                
        except Exception as e:
            print(f"PubMed search error: {e}")
        
        return evidence_list
    
    async def _search_arxiv(self, query: str) -> List[Evidence]:
        """Search ArXiv for relevant preprints."""
        evidence_list = []
        
        try:
            # Simulate ArXiv search (in production, use actual API)
            simulated_preprints = [
                {
                    "title": f"Preprint on {query}",
                    "abstract": f"Recent preprint examining {query}. Not yet peer-reviewed.",
                    "authors": "Smith et al.",
                    "arxiv_id": "2024.01234"
                }
            ]
            
            for preprint in simulated_preprints:
                evidence = Evidence(
                    content=f"{preprint['title']}. {preprint['abstract']}",
                    source="arxiv.org",
                    credibility_score=0.7,  # Lower credibility for preprints
                    relevance_score=0.85,
                    timestamp=datetime.now(),
                    metadata={
                        "arxiv_id": preprint["arxiv_id"],
                        "authors": preprint["authors"],
                        "source_type": "preprint"
                    }
                )
                evidence_list.append(evidence)
                
        except Exception as e:
            print(f"ArXiv search error: {e}")
        
        return evidence_list
    
    def _supports_claim(self, evidence_text: str, claim: str) -> bool:
        """Check if evidence supports the claim."""
        support_words = ["confirms", "supports", "demonstrates", "proves", "shows", "validates"]
        return any(word in evidence_text.lower() for word in support_words)
    
    def _contradicts_claim(self, evidence_text: str, claim: str) -> bool:
        """Check if evidence contradicts the claim."""
        contradict_words = ["contradicts", "disputes", "refutes", "disproves", "challenges"]
        return any(word in evidence_text.lower() for word in contradict_words)
    
    def _add_specialized_capabilities(self, profile: AgentProfile) -> None:
        """Add science-specific capabilities."""
        profile.add_capability(AgentCapability(
            capability_type=CapabilityType.PUBMED_SEARCH,
            confidence_level=0.9,
            cost_estimate=2.0,
            avg_response_time=3.0
        ))
        
        profile.add_capability(AgentCapability(
            capability_type=CapabilityType.ARXIV_SEARCH,
            confidence_level=0.85,
            cost_estimate=1.5,
            avg_response_time=2.0
        ))
        
        profile.add_capability(AgentCapability(
            capability_type=CapabilityType.SCIENTIFIC_ANALYSIS,
            confidence_level=0.9,
            cost_estimate=3.0,
            avg_response_time=4.0
        ))
        
        profile.add_capability(AgentCapability(
            capability_type=CapabilityType.STATISTICAL_ANALYSIS,
            confidence_level=0.8,
            cost_estimate=2.5,
            avg_response_time=3.0
        ))


class NewsAgent(SpecializedAgent):
    """
    Agent specialized in current events and breaking news.
    
    Capabilities:
    - News API integration
    - Recency bias for time-sensitive claims
    - Breaking news detection
    - Source credibility analysis
    """
    
    def __init__(self, agent_id: str = "news_agent"):
        """Initialize news agent."""
        super().__init__(agent_id, AgentType.NEWS, "news")
        
        # News-specific configuration
        self.recency_weight = 0.8  # Higher weight for recent news
        self.max_hours_recent = 48  # News is "recent" for 48 hours
        
        # Trusted news sources with credibility scores
        self.news_sources = {
            "reuters.com": 0.95,
            "bbc.com": 0.92,
            "apnews.com": 0.94,
            "npr.org": 0.90,
            "cnn.com": 0.85,
            "foxnews.com": 0.75,
            "theguardian.com": 0.88
        }
    
    async def get_specialized_evidence(self, claim: ProcessedClaim) -> EvidenceBundle:
        """Get news evidence with recency bias."""
        try:
            # Search for recent news
            recent_news = await self._search_recent_news(claim.original_text)
            
            # Apply recency scoring
            weighted_evidence = self._apply_recency_weighting(recent_news)
            
            # Categorize by stance
            supporting = []
            contradicting = []
            neutral = []
            
            for evidence in weighted_evidence:
                stance = self._analyze_news_stance(evidence.content, claim.original_text)
                if stance == "supporting":
                    supporting.append(evidence)
                elif stance == "contradicting":
                    contradicting.append(evidence)
                else:
                    neutral.append(evidence)
            
            return EvidenceBundle(
                supporting_evidence=supporting,
                contradicting_evidence=contradicting,
                neutral_evidence=neutral,
                overall_quality=0.8  # Good quality for news sources
            )
            
        except Exception as e:
            print(f"Error gathering news evidence: {e}")
            return EvidenceBundle(
                supporting_evidence=[],
                contradicting_evidence=[],
                neutral_evidence=[],
                overall_quality=0.0
            )
    
    async def _search_recent_news(self, query: str) -> List[Evidence]:
        """Search for recent news articles."""
        evidence_list = []
        
        try:
            # Simulate news API search (in production, use actual News API)
            current_time = datetime.now()
            
            simulated_articles = [
                {
                    "title": f"Breaking: News about {query}",
                    "content": f"Recent developments regarding {query}. This story is developing.",
                    "source": "reuters.com",
                    "published_at": current_time - timedelta(hours=2)
                },
                {
                    "title": f"Update on {query}",
                    "content": f"Latest information about {query} from reliable sources.",
                    "source": "bbc.com",
                    "published_at": current_time - timedelta(hours=6)
                },
                {
                    "title": f"Analysis: {query} situation",
                    "content": f"Expert analysis of the {query} situation and its implications.",
                    "source": "npr.org",
                    "published_at": current_time - timedelta(days=1)
                }
            ]
            
            for article in simulated_articles:
                # Calculate recency score
                age_hours = (current_time - article["published_at"]).total_seconds() / 3600
                recency_score = max(0.1, 1.0 - (age_hours / self.max_hours_recent))
                
                evidence = Evidence(
                    content=f"{article['title']}. {article['content']}",
                    source=article["source"],
                    credibility_score=self.news_sources.get(article["source"], 0.7),
                    relevance_score=0.9 * recency_score,  # Apply recency bias
                    timestamp=article["published_at"],
                    metadata={
                        "source_type": "news",
                        "age_hours": age_hours,
                        "recency_score": recency_score
                    }
                )
                evidence_list.append(evidence)
                
        except Exception as e:
            print(f"News search error: {e}")
        
        return evidence_list
    
    def _apply_recency_weighting(self, evidence_list: List[Evidence]) -> List[Evidence]:
        """Apply recency weighting to evidence."""
        for evidence in evidence_list:
            age_hours = evidence.metadata.get("age_hours", 0)
            if age_hours <= self.max_hours_recent:
                # Boost credibility for recent news
                evidence.credibility_score *= (1.0 + self.recency_weight * 0.2)
                evidence.credibility_score = min(1.0, evidence.credibility_score)
        
        return evidence_list
    
    def _analyze_news_stance(self, content: str, claim: str) -> str:
        """Analyze news article stance toward claim."""
        content_lower = content.lower()
        claim_lower = claim.lower()
        
        # Simple stance detection
        if any(word in content_lower for word in ["confirms", "validates", "supports"]):
            return "supporting"
        elif any(word in content_lower for word in ["denies", "refutes", "contradicts"]):
            return "contradicting"
        else:
            return "neutral"
    
    def _add_specialized_capabilities(self, profile: AgentProfile) -> None:
        """Add news-specific capabilities."""
        profile.add_capability(AgentCapability(
            capability_type=CapabilityType.NEWS_API,
            confidence_level=0.9,
            cost_estimate=1.5,
            avg_response_time=2.0
        ))


class TechAgent(SpecializedAgent):
    """
    Agent specialized in technical documentation and specifications.
    
    Capabilities:
    - Technical documentation parsing
    - API specification analysis
    - Code snippet verification
    - Technical standard compliance
    """
    
    def __init__(self, agent_id: str = "tech_agent"):
        """Initialize tech agent."""
        super().__init__(agent_id, AgentType.TECH, "tech")
        
        # Tech-specific sources
        self.tech_sources = {
            "stackoverflow.com": 0.85,
            "github.com": 0.80,
            "docs.python.org": 0.95,
            "developer.mozilla.org": 0.92,
            "w3.org": 0.95,
            "ietf.org": 0.90
        }
        
        # Technical keywords
        self.tech_keywords = [
            "api", "documentation", "specification", "code", "function",
            "method", "class", "library", "framework", "protocol",
            "standard", "rfc", "w3c", "implementation"
        ]
    
    async def get_specialized_evidence(self, claim: ProcessedClaim) -> EvidenceBundle:
        """Get technical evidence from documentation sources."""
        try:
            # Search technical documentation
            tech_docs = await self._search_tech_docs(claim.original_text)
            
            # Categorize evidence
            supporting = []
            contradicting = []
            neutral = []
            
            for evidence in tech_docs:
                if self._is_technical_match(evidence.content, claim.original_text):
                    supporting.append(evidence)
                else:
                    neutral.append(evidence)
            
            return EvidenceBundle(
                supporting_evidence=supporting,
                contradicting_evidence=contradicting,
                neutral_evidence=neutral,
                overall_quality=0.85  # High quality for technical docs
            )
            
        except Exception as e:
            print(f"Error gathering technical evidence: {e}")
            return EvidenceBundle(
                supporting_evidence=[],
                contradicting_evidence=[],
                neutral_evidence=[],
                overall_quality=0.0
            )
    
    async def _search_tech_docs(self, query: str) -> List[Evidence]:
        """Search technical documentation."""
        evidence_list = []
        
        try:
            # Simulate technical documentation search
            simulated_docs = [
                {
                    "title": f"Technical documentation for {query}",
                    "content": f"Official documentation explaining {query} implementation and usage.",
                    "source": "docs.python.org",
                    "doc_type": "official_docs"
                },
                {
                    "title": f"Stack Overflow discussion on {query}",
                    "content": f"Community discussion and solutions related to {query}.",
                    "source": "stackoverflow.com",
                    "doc_type": "community"
                }
            ]
            
            for doc in simulated_docs:
                evidence = Evidence(
                    content=f"{doc['title']}. {doc['content']}",
                    source=doc["source"],
                    credibility_score=self.tech_sources.get(doc["source"], 0.7),
                    relevance_score=0.9,
                    timestamp=datetime.now(),
                    metadata={
                        "source_type": "technical",
                        "doc_type": doc["doc_type"]
                    }
                )
                evidence_list.append(evidence)
                
        except Exception as e:
            print(f"Technical docs search error: {e}")
        
        return evidence_list
    
    def _is_technical_match(self, content: str, claim: str) -> bool:
        """Check if technical content matches claim."""
        # Simple technical matching
        return any(keyword in content.lower() for keyword in self.tech_keywords)
    
    def _add_specialized_capabilities(self, profile: AgentProfile) -> None:
        """Add tech-specific capabilities."""
        profile.add_capability(AgentCapability(
            capability_type=CapabilityType.TECHNICAL_DOCS,
            confidence_level=0.9,
            cost_estimate=1.0,
            avg_response_time=1.5
        ))
        
        profile.add_capability(AgentCapability(
            capability_type=CapabilityType.FACT_EXTRACTION,
            confidence_level=0.8,
            cost_estimate=1.5,
            avg_response_time=2.0
        ))