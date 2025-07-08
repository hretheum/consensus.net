"""
Debate Engine for Adversarial Verification

Orchestrates adversarial debates between prosecutor and defender agents,
with moderation to reach improved verification conclusions.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from ...agents.verification_result import VerificationResult
from .prosecutor_agent import ProsecutorAgent
from .defender_agent import DefenderAgent
from .moderator_agent import ModeratorAgent, DebateAnalysis
from .challenge_system import Challenge, ChallengeResponse


class DebateStatus(Enum):
    """Status of an adversarial debate."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class DebateRound:
    """Represents a single round of adversarial debate."""
    
    round_number: int = 1
    challenges: List[Challenge] = field(default_factory=list)
    responses: List[ChallengeResponse] = field(default_factory=list)
    round_start: datetime = field(default_factory=datetime.now)
    round_end: Optional[datetime] = None
    round_quality: float = 0.0


@dataclass
class DebateResult:
    """Complete result of an adversarial debate."""
    
    original_result: VerificationResult
    improved_result: VerificationResult
    debate_analysis: DebateAnalysis
    
    # Debate metadata
    debate_id: str = field(default_factory=lambda: f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    status: DebateStatus = DebateStatus.PENDING
    rounds: List[DebateRound] = field(default_factory=list)
    
    # Participants
    prosecutor_id: str = ""
    defender_id: str = ""
    moderator_id: str = ""
    
    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Quality metrics
    overall_improvement: float = 0.0     # How much the debate improved the result
    accuracy_gain: float = 0.0           # Estimated accuracy improvement
    confidence_adjustment: float = 0.0   # Confidence change
    
    # Summary
    debate_summary: str = ""
    key_insights: List[str] = field(default_factory=list)


class DebateEngine:
    """
    Engine for conducting adversarial verification debates.
    
    Orchestrates debates between prosecutor and defender agents,
    with moderator oversight to synthesize improved results.
    """
    
    def __init__(self):
        """Initialize the debate engine."""
        self.prosecutor = ProsecutorAgent()
        self.defender = DefenderAgent()
        self.moderator = ModeratorAgent()
        
        # Debate configuration
        self.max_rounds = 3
        self.round_timeout = 30  # seconds per round
        self.total_timeout = 120  # seconds total
        self.min_improvement_threshold = 0.05  # Minimum improvement to continue
        
        # Debate statistics
        self.stats = {
            "total_debates": 0,
            "successful_debates": 0,
            "failed_debates": 0,
            "average_rounds": 0.0,
            "average_improvement": 0.0,
            "average_duration": 0.0,
            "timeouts": 0
        }
        
        # Active debates
        self.active_debates: Dict[str, DebateResult] = {}
        self.completed_debates: List[DebateResult] = []
    
    async def conduct_debate(
        self, 
        verification_result: VerificationResult,
        max_rounds: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> DebateResult:
        """
        Conduct a complete adversarial debate on a verification result.
        
        Args:
            verification_result: The result to debate
            max_rounds: Maximum rounds (default: engine setting)
            timeout: Total timeout in seconds (default: engine setting)
            
        Returns:
            Complete debate result with improved verification
        """
        max_rounds = max_rounds or self.max_rounds
        timeout = timeout or self.total_timeout
        
        print(f"🏛️ Starting adversarial debate for: {verification_result.claim[:50]}...")
        
        # Initialize debate result
        debate_result = DebateResult(
            original_result=verification_result,
            improved_result=verification_result,  # Will be updated
            debate_analysis=DebateAnalysis(original_result=verification_result),
            prosecutor_id=self.prosecutor.agent_id,
            defender_id=self.defender.agent_id,
            moderator_id=self.moderator.agent_id
        )
        
        # Track active debate
        self.active_debates[debate_result.debate_id] = debate_result
        
        try:
            # Set timeout
            debate_result.status = DebateStatus.IN_PROGRESS
            
            async with asyncio.timeout(timeout):
                # Conduct rounds of debate
                for round_num in range(1, max_rounds + 1):
                    print(f"🥊 Round {round_num}/{max_rounds}")
                    
                    round_result = await self._conduct_round(
                        debate_result, round_num
                    )
                    
                    debate_result.rounds.append(round_result)
                    
                    # Check if we should continue
                    if not self._should_continue_debate(debate_result, round_num, max_rounds):
                        print(f"🏁 Debate concluded after {round_num} rounds")
                        break
                
                # Final moderation and synthesis
                await self._finalize_debate(debate_result)
                
                debate_result.status = DebateStatus.COMPLETED
                print(f"✅ Debate completed successfully")
        
        except asyncio.TimeoutError:
            debate_result.status = DebateStatus.TIMEOUT
            self.stats["timeouts"] += 1
            print(f"⏰ Debate timed out after {timeout}s")
            
            # Still try to finalize with partial results
            await self._finalize_debate(debate_result)
        
        except Exception as e:
            debate_result.status = DebateStatus.FAILED
            print(f"💥 Debate failed: {e}")
            
            # Use original result as fallback
            debate_result.improved_result = verification_result
        
        finally:
            # Complete timing and cleanup
            debate_result.end_time = datetime.now()
            debate_result.duration_seconds = (
                debate_result.end_time - debate_result.start_time
            ).total_seconds()
            
            # Move to completed debates
            if debate_result.debate_id in self.active_debates:
                del self.active_debates[debate_result.debate_id]
            self.completed_debates.append(debate_result)
            
            # Update statistics
            self._update_stats(debate_result)
        
        return debate_result
    
    async def _conduct_round(
        self, 
        debate_result: DebateResult, 
        round_num: int
    ) -> DebateRound:
        """Conduct a single round of debate."""
        
        round_start = datetime.now()
        
        # Get current result to challenge (from previous round or original)
        if round_num == 1:
            current_result = debate_result.original_result
        else:
            current_result = debate_result.improved_result
        
        try:
            # Phase 1: Prosecutor challenges
            print(f"🚨 Phase 1: Prosecutor challenges")
            challenges = await asyncio.wait_for(
                self.prosecutor.challenge_result_async(current_result),
                timeout=self.round_timeout / 2
            )
            
            # Phase 2: Defender responds
            print(f"🛡️ Phase 2: Defender responds")
            responses = await asyncio.wait_for(
                self.defender.defend_against_challenges_async(current_result, challenges),
                timeout=self.round_timeout / 2
            )
            
            # Create round result
            round_result = DebateRound(
                round_number=round_num,
                challenges=challenges,
                responses=responses,
                round_start=round_start,
                round_end=datetime.now()
            )
            
            # Calculate round quality
            round_result.round_quality = self._calculate_round_quality(round_result)
            
            print(f"📊 Round {round_num} quality: {round_result.round_quality:.2f}")
            return round_result
        
        except asyncio.TimeoutError:
            print(f"⏰ Round {round_num} timed out")
            return DebateRound(
                round_number=round_num,
                round_start=round_start,
                round_end=datetime.now()
            )
    
    def _should_continue_debate(
        self, 
        debate_result: DebateResult, 
        current_round: int, 
        max_rounds: int
    ) -> bool:
        """Determine if debate should continue to next round."""
        
        # Always continue if we haven't reached max rounds and have active challenges
        if current_round < max_rounds:
            latest_round = debate_result.rounds[-1] if debate_result.rounds else None
            
            if latest_round and latest_round.challenges:
                # Continue if there are unresolved challenges
                unresolved = len([c for c in latest_round.challenges 
                                if not any(r.challenge_id == c.challenge_id and r.adequacy_score >= 0.7 
                                          for r in latest_round.responses)])
                
                if unresolved > 0:
                    print(f"🔄 Continuing - {unresolved} unresolved challenges")
                    return True
            
            # Continue if round quality is high (productive debate)
            if latest_round and latest_round.round_quality >= 0.6:
                print(f"🔄 Continuing - high quality round ({latest_round.round_quality:.2f})")
                return True
        
        return False
    
    async def _finalize_debate(self, debate_result: DebateResult) -> None:
        """Finalize debate with moderation and synthesis."""
        
        print(f"⚖️ Final moderation and synthesis")
        
        # Gather all challenges and responses
        all_challenges = []
        all_responses = []
        
        for round_result in debate_result.rounds:
            all_challenges.extend(round_result.challenges)
            all_responses.extend(round_result.responses)
        
        # Moderate the complete debate
        debate_result.debate_analysis = await self.moderator.moderate_debate_async(
            debate_result.original_result,
            all_challenges,
            all_responses
        )
        
        # Create improved result
        debate_result.improved_result = self.moderator.synthesize_improved_result(
            debate_result.original_result,
            debate_result.debate_analysis
        )
        
        # Calculate improvement metrics
        debate_result.confidence_adjustment = (
            debate_result.improved_result.confidence - 
            debate_result.original_result.confidence
        )
        
        debate_result.overall_improvement = abs(debate_result.confidence_adjustment)
        
        # Create summary
        debate_result.debate_summary = self._create_debate_summary(debate_result)
        debate_result.key_insights = self._extract_key_insights(debate_result)
        
        print(f"📈 Improvement: {debate_result.overall_improvement:.3f}")
    
    def _calculate_round_quality(self, round_result: DebateRound) -> float:
        """Calculate quality score for a debate round."""
        
        if not round_result.challenges:
            return 0.0
        
        # Challenge quality
        challenge_quality = sum(c.get_priority_score() for c in round_result.challenges) / len(round_result.challenges)
        
        # Response quality
        response_quality = 0.0
        if round_result.responses:
            response_quality = sum(r.adequacy_score for r in round_result.responses) / len(round_result.responses)
        
        # Coverage (how many challenges were addressed)
        coverage = 0.0
        if round_result.challenges:
            addressed = len([c for c in round_result.challenges 
                           if any(r.challenge_id == c.challenge_id for r in round_result.responses)])
            coverage = addressed / len(round_result.challenges)
        
        # Weighted combination
        return (challenge_quality * 0.4 + response_quality * 0.4 + coverage * 0.2)
    
    def _create_debate_summary(self, debate_result: DebateResult) -> str:
        """Create a summary of the debate."""
        
        total_challenges = sum(len(r.challenges) for r in debate_result.rounds)
        total_responses = sum(len(r.responses) for r in debate_result.rounds)
        
        summary_parts = [
            f"Adversarial debate with {len(debate_result.rounds)} rounds",
            f"{total_challenges} challenges raised by prosecutor",
            f"{total_responses} responses from defender",
            f"Final confidence adjustment: {debate_result.confidence_adjustment:+.3f}",
            f"Debate quality: {debate_result.debate_analysis.debate_quality_score:.2f}"
        ]
        
        if debate_result.debate_analysis.requires_further_investigation:
            summary_parts.append("Further investigation recommended")
        
        return ". ".join(summary_parts) + "."
    
    def _extract_key_insights(self, debate_result: DebateResult) -> List[str]:
        """Extract key insights from the debate."""
        
        insights = []
        
        # Add insights from debate analysis
        insights.extend(debate_result.debate_analysis.key_findings)
        
        # Add high-impact challenge insights
        for round_result in debate_result.rounds:
            for challenge in round_result.challenges:
                if challenge.impact_score >= 0.8:
                    insights.append(f"High-impact challenge: {challenge.description}")
        
        # Add successful defense insights
        for round_result in debate_result.rounds:
            for response in round_result.responses:
                if response.adequacy_score >= 0.9:
                    insights.append(f"Strong defense: {response.explanation[:100]}...")
        
        return insights[:5]  # Limit to top 5 insights
    
    def _update_stats(self, debate_result: DebateResult) -> None:
        """Update debate engine statistics."""
        
        self.stats["total_debates"] += 1
        
        if debate_result.status == DebateStatus.COMPLETED:
            self.stats["successful_debates"] += 1
        else:
            self.stats["failed_debates"] += 1
        
        # Update averages
        total_debates = self.stats["total_debates"]
        
        # Average rounds
        old_avg_rounds = self.stats["average_rounds"]
        new_rounds = len(debate_result.rounds)
        self.stats["average_rounds"] = (
            (old_avg_rounds * (total_debates - 1) + new_rounds) / total_debates
        )
        
        # Average improvement
        old_avg_improvement = self.stats["average_improvement"]
        new_improvement = debate_result.overall_improvement
        self.stats["average_improvement"] = (
            (old_avg_improvement * (total_debates - 1) + new_improvement) / total_debates
        )
        
        # Average duration
        old_avg_duration = self.stats["average_duration"]
        new_duration = debate_result.duration_seconds
        self.stats["average_duration"] = (
            (old_avg_duration * (total_debates - 1) + new_duration) / total_debates
        )
    
    def get_debate_stats(self) -> Dict[str, Any]:
        """Get comprehensive debate engine statistics."""
        
        total_debates = self.stats["total_debates"]
        success_rate = 0.0
        
        if total_debates > 0:
            success_rate = self.stats["successful_debates"] / total_debates
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "timeout_rate": self.stats["timeouts"] / max(1, total_debates),
            "active_debates": len(self.active_debates),
            "completed_debates": len(self.completed_debates),
            "prosecutor_stats": self.prosecutor.get_prosecutor_stats(),
            "defender_stats": self.defender.get_defender_stats(),
            "moderator_stats": self.moderator.get_moderator_stats()
        }
    
    def get_debate_by_id(self, debate_id: str) -> Optional[DebateResult]:
        """Get a specific debate result by ID."""
        
        # Check active debates
        if debate_id in self.active_debates:
            return self.active_debates[debate_id]
        
        # Check completed debates
        for debate in self.completed_debates:
            if debate.debate_id == debate_id:
                return debate
        
        return None
    
    def get_recent_debates(self, limit: int = 10) -> List[DebateResult]:
        """Get most recent completed debates."""
        
        return sorted(
            self.completed_debates,
            key=lambda d: d.start_time,
            reverse=True
        )[:limit]
    
    async def shutdown(self) -> None:
        """Shutdown the debate engine gracefully."""
        
        print("🏛️ Shutting down debate engine...")
        
        # Wait for active debates to complete (with timeout)
        if self.active_debates:
            print(f"⏳ Waiting for {len(self.active_debates)} active debates to complete...")
            
            try:
                await asyncio.wait_for(
                    asyncio.gather(*[
                        self._wait_for_debate_completion(debate_id)
                        for debate_id in list(self.active_debates.keys())
                    ]),
                    timeout=30
                )
            except asyncio.TimeoutError:
                print("⏰ Some debates did not complete in time")
        
        print("🏛️ Debate engine shutdown complete")
    
    async def _wait_for_debate_completion(self, debate_id: str) -> None:
        """Wait for a specific debate to complete."""
        
        while debate_id in self.active_debates:
            await asyncio.sleep(0.1)


# Global debate engine instance
debate_engine = DebateEngine()