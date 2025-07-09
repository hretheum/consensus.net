"""
Agent Pool Manager for Multi-Agent Orchestration

Manages the lifecycle and coordination of multiple verification agents,
handling task distribution, load balancing, and result aggregation.
"""

import asyncio
import uuid
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from collections import defaultdict

from ...agents.base_agent import BaseAgent
from ...agents.simple_agent import SimpleAgent
from ...agents.enhanced_agent import EnhancedAgent
from ...agents.verification_result import VerificationResult
from ...agents.agent_models import ProcessedClaim, ClaimComplexity

from src.consensus.communication.message_passing import (
    AgentMessage, MessageType, MessagePriority, message_bus,
    create_verification_request, create_verification_result
)
from src.consensus.communication.agent_discovery import (
    AgentRegistry, AgentProfile, AgentType, CapabilityType, 
    AgentCapability, agent_registry
)


class PoolStatus(Enum):
    """Status of the agent pool."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEGRADED = "degraded"  # Some agents down
    MAINTENANCE = "maintenance"
    SHUTDOWN = "shutdown"


class TaskStatus(Enum):
    """Status of verification tasks."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class VerificationTask:
    """Represents a verification task in the multi-agent system."""
    
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    claim: str = ""
    processed_claim: Optional[ProcessedClaim] = None
    
    # Task management
    status: TaskStatus = TaskStatus.PENDING
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    timeout_seconds: int = 60
    
    # Agent assignment
    assigned_agents: List[str] = field(default_factory=list)
    required_capabilities: List[CapabilityType] = field(default_factory=list)
    target_agent_count: int = 1
    
    # Results
    agent_results: Dict[str, VerificationResult] = field(default_factory=dict)
    aggregated_result: Optional[VerificationResult] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    conversation_id: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if task has exceeded timeout."""
        age = datetime.now() - self.created_at
        return age.total_seconds() > self.timeout_seconds
    
    def is_complete(self) -> bool:
        """Check if task has enough results to be considered complete."""
        return len(self.agent_results) >= self.target_agent_count
    
    def add_result(self, agent_id: str, result: VerificationResult) -> None:
        """Add a verification result from an agent."""
        self.agent_results[agent_id] = result
        
        if self.is_complete() and self.status != TaskStatus.COMPLETED:
            self.status = TaskStatus.COMPLETED


class AgentPoolManager:
    """
    Central manager for the multi-agent verification system.
    
    Coordinates multiple agents, distributes tasks, manages load balancing,
    and aggregates results for consensus building.
    """
    
    def __init__(self):
        """Initialize the agent pool manager."""
        self.status = PoolStatus.INITIALIZING
        
        # Agent management
        self.active_agents: Dict[str, BaseAgent] = {}
        self.agent_profiles: Dict[str, AgentProfile] = {}
        
        # Task management
        self.active_tasks: Dict[str, VerificationTask] = {}
        self.task_queue: List[VerificationTask] = []
        self.completed_tasks: List[VerificationTask] = []
        
        # Performance tracking
        self.pool_stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "avg_response_time": 0.0,
            "total_agents": 0,
            "active_agents": 0
        }
        
        # Configuration
        self.max_concurrent_tasks = 10
        self.default_timeout = 60
        self.cleanup_interval = 300  # 5 minutes
        
        # Initialize components
        self.message_bus = message_bus
        self.agent_registry = agent_registry
        
        # Setup message handlers
        self._setup_message_handlers()
        
        # Task processing
        self._task_processor = None
        self._cleanup_task = None
    
    async def initialize(self) -> None:
        """Initialize the agent pool manager."""
        # Start the default agents
        await self._create_default_agents()
        
        # Start background tasks
        await self._start_background_tasks()
        
        self.status = PoolStatus.ACTIVE
        print(f"AgentPoolManager initialized with {len(self.active_agents)} agents")
    
    async def shutdown(self) -> None:
        """Shutdown the agent pool manager."""
        self.status = PoolStatus.SHUTDOWN
        
        # Cancel background tasks
        if self._task_processor:
            self._task_processor.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Unregister all agents
        for agent_id in list(self.active_agents.keys()):
            await self.remove_agent(agent_id)
        
        print("AgentPoolManager shutdown complete")
    
    async def verify_claim(
        self, 
        claim: str,
        agent_count: int = 3,
        timeout: int = 60,
        required_capabilities: Optional[List[CapabilityType]] = None
    ) -> VerificationResult:
        """
        Verify a claim using multiple agents and consensus.
        
        Args:
            claim: The claim to verify
            agent_count: Number of agents to use
            timeout: Timeout in seconds
            required_capabilities: Specific capabilities needed
            
        Returns:
            Aggregated verification result from multiple agents
        """
        # Ensure we're initialized
        if self.status == PoolStatus.INITIALIZING:
            print("🔄 Pool not initialized, initializing now...")
            await self.initialize()
        
        # Create verification task
        task = VerificationTask(
            claim=claim,
            target_agent_count=agent_count,
            timeout_seconds=timeout,
            required_capabilities=required_capabilities or []
        )
        
        print(f"🎯 Starting multi-agent verification for: {claim[:50]}...")
        
        # Process the claim
        task.processed_claim = self._process_claim(claim)
        print(f"📝 Processed claim - domain: {task.processed_claim.domain}, complexity: {task.processed_claim.complexity.value}")
        
        # Add task to active tasks  
        self.active_tasks[task.task_id] = task
        self.pool_stats["total_tasks"] += 1
        
        # Instead of using queue, assign agents directly for immediate processing
        await self._assign_agents_to_task(task)
        
        # Wait for completion
        return await self._wait_for_task_completion(task)
    
    async def add_agent(self, agent: BaseAgent, profile: Optional[AgentProfile] = None) -> bool:
        """
        Add an agent to the pool.
        
        Args:
            agent: The agent instance to add
            profile: Optional agent profile (will be created if not provided)
            
        Returns:
            True if agent was added successfully
        """
        try:
            agent_id = agent.agent_id
            
            # Create profile if not provided
            if profile is None:
                profile = self._create_agent_profile(agent)
            
            # Register with message bus
            self.message_bus.register_agent(agent_id, self._handle_agent_message)
            
            # Register with agent registry
            self.agent_registry.register_agent(profile)
            
            # Store locally
            self.active_agents[agent_id] = agent
            self.agent_profiles[agent_id] = profile
            
            # Update stats
            self.pool_stats["total_agents"] += 1
            self.pool_stats["active_agents"] = len(self.active_agents)
            
            print(f"Added agent {agent_id} to pool ({profile.agent_type.value})")
            return True
            
        except Exception as e:
            print(f"Failed to add agent {agent.agent_id}: {e}")
            return False
    
    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the pool."""
        try:
            if agent_id not in self.active_agents:
                return False
            
            # Unregister from systems
            self.message_bus.unregister_agent(agent_id)
            self.agent_registry.unregister_agent(agent_id)
            
            # Remove locally
            del self.active_agents[agent_id]
            del self.agent_profiles[agent_id]
            
            # Update stats
            self.pool_stats["active_agents"] = len(self.active_agents)
            
            print(f"Removed agent {agent_id} from pool")
            return True
            
        except Exception as e:
            print(f"Failed to remove agent {agent_id}: {e}")
            return False
    
    async def _create_default_agents(self) -> None:
        """Create default agents for the pool."""
        # Create a simple agent
        simple_agent = SimpleAgent("simple_default")
        simple_profile = AgentProfile(
            agent_id="simple_default",
            agent_type=AgentType.GENERALIST,
            display_name="Default Simple Agent",
            description="Basic verification agent with simulation capabilities"
        )
        simple_profile.add_capability(AgentCapability(
            capability_type=CapabilityType.FACT_EXTRACTION,
            confidence_level=0.7,
            cost_estimate=1.0,
            avg_response_time=1.0
        ))
        
        await self.add_agent(simple_agent, simple_profile)
        
        # Create an enhanced agent
        enhanced_agent = EnhancedAgent("enhanced_default")
        enhanced_profile = AgentProfile(
            agent_id="enhanced_default", 
            agent_type=AgentType.GENERALIST,
            display_name="Default Enhanced Agent",
            description="Advanced verification agent with real API integration"
        )
        enhanced_profile.add_capability(AgentCapability(
            capability_type=CapabilityType.WIKIPEDIA_SEARCH,
            confidence_level=0.9,
            cost_estimate=2.0,
            avg_response_time=2.0
        ))
        enhanced_profile.add_capability(AgentCapability(
            capability_type=CapabilityType.EVIDENCE_SYNTHESIS,
            confidence_level=0.8,
            cost_estimate=3.0,
            avg_response_time=1.5
        ))
        
        await self.add_agent(enhanced_agent, enhanced_profile)
    
    def _create_agent_profile(self, agent: BaseAgent) -> AgentProfile:
        """Create a basic agent profile for an agent."""
        # Determine agent type based on class
        agent_type = AgentType.GENERALIST
        if "enhanced" in agent.__class__.__name__.lower():
            agent_type = AgentType.GENERALIST
        elif "science" in agent.__class__.__name__.lower():
            agent_type = AgentType.SCIENCE
        elif "news" in agent.__class__.__name__.lower():
            agent_type = AgentType.NEWS
        elif "tech" in agent.__class__.__name__.lower():
            agent_type = AgentType.TECH
        
        profile = AgentProfile(
            agent_id=agent.agent_id,
            agent_type=agent_type,
            display_name=f"Agent {agent.agent_id}",
            description=f"Auto-generated profile for {agent.__class__.__name__}"
        )
        
        # Add basic capabilities
        profile.add_capability(AgentCapability(
            capability_type=CapabilityType.FACT_EXTRACTION,
            confidence_level=0.6,
            cost_estimate=1.0,
            avg_response_time=1.0
        ))
        
        return profile
    
    def _process_claim(self, claim: str) -> ProcessedClaim:
        """Process claim into structured format."""
        # Simple processing - in production this would be more sophisticated
        domain = "general"
        complexity = ClaimComplexity.MODERATE
        
        if any(word in claim.lower() for word in ["research", "study", "science", "data"]):
            domain = "science"
        elif any(word in claim.lower() for word in ["news", "breaking", "today", "recent"]):
            domain = "news"
        elif any(word in claim.lower() for word in ["technology", "software", "api", "code"]):
            domain = "tech"
        
        word_count = len(claim.split())
        if word_count < 8:
            complexity = ClaimComplexity.SIMPLE
        elif word_count > 20:
            complexity = ClaimComplexity.COMPLEX
        
        return ProcessedClaim(
            original_text=claim,
            normalized_text=claim.lower().strip(),
            domain=domain,
            complexity=complexity,
            context={"word_count": word_count},
            preprocessing_metadata={"processed_by": "AgentPoolManager"}
        )
    
    async def _enqueue_task(self, task: VerificationTask) -> None:
        """Add task to processing queue."""
        self.task_queue.append(task)
        self.active_tasks[task.task_id] = task
        self.pool_stats["total_tasks"] += 1
        
        print(f"Enqueued task {task.task_id} for claim: {task.claim[:50]}...")
    
    async def _wait_for_task_completion(self, task: VerificationTask) -> VerificationResult:
        """Wait for a task to complete and return aggregated result."""
        timeout_time = datetime.now() + timedelta(seconds=task.timeout_seconds)
        
        print(f"⏳ Waiting for task {task.task_id} completion (timeout: {task.timeout_seconds}s)")
        
        check_count = 0
        while datetime.now() < timeout_time:
            check_count += 1
            
            if check_count % 50 == 0:  # Log every 5 seconds
                print(f"📊 Task {task.task_id} status: {task.status.value}, results: {len(task.agent_results)}/{task.target_agent_count}")
            
            if task.status == TaskStatus.COMPLETED:
                print(f"🎉 Task {task.task_id} completed! Aggregating results...")
                # Aggregate results
                if not task.aggregated_result:
                    task.aggregated_result = self._aggregate_results(task)
                return task.aggregated_result
            elif task.status == TaskStatus.FAILED:
                print(f"❌ Task {task.task_id} failed")
                raise RuntimeError(f"Task {task.task_id} failed")
            
            await asyncio.sleep(0.1)  # Check every 100ms
        
        # Timeout occurred
        print(f"⏰ Task {task.task_id} timed out after {task.timeout_seconds}s")
        task.status = TaskStatus.TIMEOUT
        self.pool_stats["failed_tasks"] += 1
        
        # Return partial results if any
        if task.agent_results:
            print(f"🔄 Returning partial results ({len(task.agent_results)} results)")
            task.aggregated_result = self._aggregate_results(task)
            return task.aggregated_result
        
        # No results at all
        print(f"💥 Task {task.task_id} timed out with no results")
        raise TimeoutError(f"Task {task.task_id} timed out with no results")
    
    def _aggregate_results(self, task: VerificationTask) -> VerificationResult:
        """Aggregate multiple agent results into a single result."""
        if not task.agent_results:
            raise ValueError("No results to aggregate")
        
        results = list(task.agent_results.values())
        
        # Simple aggregation strategy (will be enhanced with consensus engine)
        verdicts = [r.verdict for r in results]
        confidences = [r.confidence for r in results]
        
        # Majority vote for verdict
        verdict_counts = {}
        for verdict in verdicts:
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        
        final_verdict = max(verdict_counts.keys(), key=lambda k: verdict_counts[k])
        
        # Weighted average confidence
        final_confidence = sum(confidences) / len(confidences)
        
        # Combine reasoning
        reasoning_parts = [f"Agent {agent_id}: {result.reasoning[:100]}..." 
                          for agent_id, result in task.agent_results.items()]
        final_reasoning = " | ".join(reasoning_parts)
        
        # Combine sources
        all_sources = []
        for result in results:
            all_sources.extend(result.sources)
        unique_sources = list(set(all_sources))
        
        # Combine evidence
        all_evidence = []
        for result in results:
            all_evidence.extend(result.evidence)
        
        return VerificationResult(
            claim=task.claim,
            verdict=final_verdict,
            confidence=final_confidence,
            reasoning=final_reasoning,
            sources=unique_sources,
            evidence=all_evidence,
            metadata={
                "aggregation_method": "simple_majority",
                "agent_count": len(results),
                "task_id": task.task_id,
                "individual_verdicts": verdicts,
                "individual_confidences": confidences,
                "consensus_agreement": verdict_counts[final_verdict] / len(verdicts)
            },
            agent_id="multi_agent_pool"
        )
    
    async def _start_background_tasks(self) -> None:
        """Start background processing tasks."""
        self._task_processor = asyncio.create_task(self._process_task_queue())
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _process_task_queue(self) -> None:
        """Background task to process the task queue."""
        while self.status in [PoolStatus.ACTIVE, PoolStatus.DEGRADED]:
            try:
                # Process pending tasks
                tasks_to_process = [t for t in self.task_queue if t.status == TaskStatus.PENDING]
                
                for task in tasks_to_process[:self.max_concurrent_tasks]:
                    await self._assign_agents_to_task(task)
                
                # Remove processed tasks from queue
                self.task_queue = [t for t in self.task_queue if t.status == TaskStatus.PENDING]
                
                await asyncio.sleep(1)  # Process every second
                
            except Exception as e:
                print(f"Error in task processor: {e}")
                await asyncio.sleep(5)
    
    async def _assign_agents_to_task(self, task: VerificationTask) -> None:
        """Assign agents to a verification task."""
        try:
            print(f"🔍 Assigning agents to task {task.task_id}, target: {task.target_agent_count}")
            
            # Find suitable agents
            suitable_agents = self._find_suitable_agents(task)
            print(f"📋 Found {len(suitable_agents)} suitable agents: {[a.agent_id for a in suitable_agents]}")
            
            if not suitable_agents:
                task.status = TaskStatus.FAILED
                self.pool_stats["failed_tasks"] += 1
                print(f"❌ No suitable agents found for task {task.task_id}")
                return
            
            # Assign agents (up to target count)
            assigned_count = 0
            for agent_profile in suitable_agents:
                if assigned_count >= task.target_agent_count:
                    break
                
                agent_id = agent_profile.agent_id
                print(f"🤖 Checking agent {agent_id}, active: {agent_id in self.active_agents}")
                
                if agent_id in self.active_agents:
                    task.assigned_agents.append(agent_id)
                    assigned_count += 1
                    
                    # Send verification request
                    print(f"📤 Sending verification request to {agent_id}")
                    await self._send_verification_request(task, agent_id)
            
            if assigned_count > 0:
                task.status = TaskStatus.ASSIGNED
                print(f"✅ Assigned {assigned_count} agents to task {task.task_id}: {task.assigned_agents}")
            else:
                task.status = TaskStatus.FAILED
                self.pool_stats["failed_tasks"] += 1
                print(f"❌ Failed to assign any agents to task {task.task_id}")
                
        except Exception as e:
            print(f"💥 Error assigning agents to task {task.task_id}: {e}")
            task.status = TaskStatus.FAILED
            self.pool_stats["failed_tasks"] += 1
    
    def _find_suitable_agents(self, task: VerificationTask) -> List[AgentProfile]:
        """Find agents suitable for a task."""
        if not task.processed_claim:
            # Fallback if no processed claim
            available_agents = list(self.agent_profiles.values())
            return available_agents[:task.target_agent_count]
        
        # Use agent registry to find suitable agents
        suitable_agents = self.agent_registry.find_best_agent_for_claim(
            task.claim,
            task.processed_claim.domain,
            task.processed_claim.complexity.value,
            task.required_capabilities
        )
        
        if suitable_agents:
            # Add more agents if available
            all_suitable = [suitable_agents]
            remaining_needed = task.target_agent_count - 1
            
            if remaining_needed > 0:
                # Get additional agents of same or different types
                additional = self.agent_registry.find_agents_by_type(AgentType.GENERALIST, limit=remaining_needed)
                all_suitable.extend(additional)
            
            return all_suitable[:task.target_agent_count]
        
        # Fallback: get any available agents
        available_agents = list(self.agent_profiles.values())
        return available_agents[:task.target_agent_count]
    
    async def _send_verification_request(self, task: VerificationTask, agent_id: str) -> None:
        """Send verification request to specific agent."""
        message = create_verification_request(
            sender_id="agent_pool_manager",
            claim=task.claim,
            recipient_id=agent_id,
            priority=task.priority
        )
        
        message.conversation_id = task.task_id
        message.metadata = {
            "task_id": task.task_id,
            "processed_claim": task.processed_claim.model_dump() if task.processed_claim else None
        }
        
        await self.message_bus.send_message(message)
        print(f"Sent verification request to agent {agent_id} for task {task.task_id}")
    
    async def _handle_agent_message(self, message: AgentMessage) -> None:
        """Handle incoming messages from agents."""
        try:
            if message.message_type == MessageType.VERIFICATION_RESULT:
                await self._handle_verification_result(message)
            elif message.message_type == MessageType.AGENT_HEARTBEAT:
                await self._handle_agent_heartbeat(message)
            
        except Exception as e:
            print(f"Error handling agent message: {e}")
    
    async def _handle_verification_result(self, message: AgentMessage) -> None:
        """Handle verification result from agent."""
        task_id = message.conversation_id
        agent_id = message.sender_id
        
        print(f"📨 Received verification result from {agent_id} for task {task_id}")
        
        if not task_id or task_id not in self.active_tasks:
            print(f"⚠️ Task {task_id} not found in active tasks")
            return
        
        task = self.active_tasks[task_id]
        
        # Extract verification result
        result_data = message.payload.get("verification_result")
        if result_data:
            try:
                result = VerificationResult.model_validate(result_data)
                task.add_result(agent_id, result)
                
                print(f"✅ Added result from {agent_id}: {result.verdict} (confidence: {result.confidence:.2f})")
                print(f"📊 Task {task_id} now has {len(task.agent_results)}/{task.target_agent_count} results")
                
                # Update agent performance
                if agent_id in self.agent_profiles:
                    profile = self.agent_profiles[agent_id]
                    response_time = (datetime.now() - task.created_at).total_seconds()
                    profile.update_performance(response_time, True)
                    
            except Exception as e:
                print(f"💥 Error processing result from {agent_id}: {e}")
        else:
            print(f"⚠️ No verification_result in payload from {agent_id}")
    
    async def _handle_agent_heartbeat(self, message: AgentMessage) -> None:
        """Handle heartbeat from agent."""
        agent_id = message.sender_id
        if agent_id in self.agent_profiles:
            self.agent_profiles[agent_id].last_heartbeat = datetime.now()
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired tasks and inactive agents."""
        while self.status in [PoolStatus.ACTIVE, PoolStatus.DEGRADED]:
            try:
                # Clean up expired tasks
                expired_tasks = [
                    task_id for task_id, task in self.active_tasks.items()
                    if task.is_expired() and task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]
                ]
                
                for task_id in expired_tasks:
                    task = self.active_tasks[task_id]
                    task.status = TaskStatus.TIMEOUT
                    self.completed_tasks.append(task)
                    del self.active_tasks[task_id]
                
                # Clean up completed tasks (keep only last 100)
                if len(self.completed_tasks) > 100:
                    self.completed_tasks = self.completed_tasks[-100:]
                
                # Clean up inactive agents from registry
                self.agent_registry.cleanup_inactive_agents()
                
                await asyncio.sleep(self.cleanup_interval)
                
            except Exception as e:
                print(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(60)
    
    def _setup_message_handlers(self) -> None:
        """Setup message handlers for the pool manager."""
        # Subscribe to relevant message types
        self.message_bus.subscribe(
            MessageType.VERIFICATION_RESULT.value,
            self._handle_agent_message
        )
        self.message_bus.subscribe(
            MessageType.AGENT_HEARTBEAT.value, 
            self._handle_agent_message
        )
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get comprehensive pool statistics."""
        active_task_count = len([t for t in self.active_tasks.values() 
                                if t.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]])
        
        return {
            **self.pool_stats,
            "status": self.status.value,
            "active_tasks": active_task_count,
            "queued_tasks": len(self.task_queue),
            "completed_tasks_session": len(self.completed_tasks),
            "agent_profiles": len(self.agent_profiles),
            "message_bus_stats": self.message_bus.get_stats(),
            "registry_stats": self.agent_registry.get_registry_stats()
        }


# Global agent pool manager instance
agent_pool_manager = AgentPoolManager()