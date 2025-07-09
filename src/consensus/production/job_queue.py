"""
Job Queue Manager - Async Task Processing

Implements robust job queue system for:
- Heavy verification tasks
- Background processing
- Distributed task execution
- Priority-based scheduling
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class JobPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Job:
    """Job definition for queue processing"""
    id: str
    task_name: str
    payload: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    timeout: float = 300.0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: JobStatus = JobStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class JobQueueManager:
    """Production-grade job queue with Redis backend"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.task_handlers: Dict[str, Callable] = {}
        self.workers: List[asyncio.Task] = []
        self.is_running = False
        self.worker_count = 4
        self.stats = {
            "jobs_processed": 0,
            "jobs_failed": 0,
            "jobs_retried": 0,
            "average_processing_time": 0.0,
            "queue_size": 0
        }
        
    async def initialize(self, worker_count: int = 4):
        """Initialize job queue with Redis connection"""
        self.worker_count = worker_count
        
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Job queue connected to Redis")
        except Exception as e:
            logger.warning(f"Redis unavailable, using in-memory queue: {e}")
            self.redis_client = InMemoryQueue()
            
        # Register built-in task handlers
        self._register_builtin_tasks()
        
    def register_task(self, task_name: str, handler: Callable):
        """Register a task handler"""
        self.task_handlers[task_name] = handler
        logger.info(f"✅ Registered task handler: {task_name}")
        
    def _register_builtin_tasks(self):
        """Register built-in task handlers"""
        self.register_task("verification", self._handle_verification_task)
        self.register_task("debate", self._handle_debate_task)
        self.register_task("reputation_update", self._handle_reputation_task)
        self.register_task("cache_warmup", self._handle_cache_warmup_task)
        
    async def enqueue_job(self, task_name: str, payload: Dict[str, Any],
                         priority: JobPriority = JobPriority.NORMAL,
                         timeout: float = 300.0, max_retries: int = 3) -> str:
        """Add job to queue"""
        job_id = str(uuid.uuid4())
        
        job = Job(
            id=job_id,
            task_name=task_name,
            payload=payload,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Add to Redis queue
        queue_key = f"job_queue:{priority.name.lower()}"
        job_data = json.dumps(asdict(job), default=str)
        
        if hasattr(self.redis_client, 'lpush'):
            await self.redis_client.lpush(queue_key, job_data)
        else:
            await self.redis_client.enqueue(queue_key, job_data)
            
        # Store job details
        job_key = f"job:{job_id}"
        if hasattr(self.redis_client, 'hset'):
            await self.redis_client.hset(job_key, mapping=asdict(job))
        else:
            await self.redis_client.set_job(job_key, asdict(job))
        
        logger.info(f"📝 Enqueued job {job_id}: {task_name}")
        return job_id
    
    async def start_workers(self):
        """Start background worker processes"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start worker tasks
        for i in range(self.worker_count):
            worker_task = asyncio.create_task(
                self._worker_loop(f"worker_{i}")
            )
            self.workers.append(worker_task)
            
        logger.info(f"🚀 Started {self.worker_count} job queue workers")
        
    async def stop_workers(self):
        """Stop all workers gracefully"""
        self.is_running = False
        
        # Cancel all worker tasks
        for worker in self.workers:
            worker.cancel()
            
        # Wait for workers to finish current jobs
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
            
        self.workers.clear()
        logger.info("🛑 All job queue workers stopped")
        
    async def _worker_loop(self, worker_name: str):
        """Main worker loop for processing jobs"""
        logger.info(f"👷 Worker {worker_name} started")
        
        while self.is_running:
            try:
                # Get next job from priority queues
                job = await self._get_next_job()
                
                if job:
                    await self._process_job(job, worker_name)
                else:
                    # No jobs available, wait a bit
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(5)
                
        logger.info(f"👷 Worker {worker_name} stopped")
        
    async def _get_next_job(self) -> Optional[Job]:
        """Get next job from priority queues"""
        # Check queues in priority order
        for priority in [JobPriority.URGENT, JobPriority.HIGH, 
                        JobPriority.NORMAL, JobPriority.LOW]:
            queue_key = f"job_queue:{priority.name.lower()}"
            
            try:
                if hasattr(self.redis_client, 'brpop'):
                    # Redis blocking pop with timeout
                    result = await self.redis_client.brpop(queue_key, timeout=1)
                    if result:
                        job_data = result[1]
                        job_dict = json.loads(job_data)
                        return Job(**job_dict)
                else:
                    # In-memory queue
                    job_data = await self.redis_client.dequeue(queue_key)
                    if job_data:
                        job_dict = json.loads(job_data)
                        return Job(**job_dict)
                        
            except Exception as e:
                logger.error(f"Error getting job from queue {queue_key}: {e}")
                
        return None
        
    async def _process_job(self, job: Job, worker_name: str):
        """Process a single job"""
        start_time = time.time()
        
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            await self._update_job_status(job)
            
            logger.info(f"🔄 Worker {worker_name} processing job {job.id}: {job.task_name}")
            
            # Get task handler
            if job.task_name not in self.task_handlers:
                raise ValueError(f"Unknown task: {job.task_name}")
                
            handler = self.task_handlers[job.task_name]
            
            # Execute task with timeout
            try:
                result = await asyncio.wait_for(
                    handler(job.payload),
                    timeout=job.timeout
                )
                
                # Job completed successfully
                job.status = JobStatus.COMPLETED
                job.result = result
                job.completed_at = datetime.now()
                
                processing_time = time.time() - start_time
                self.stats["jobs_processed"] += 1
                self._update_average_processing_time(processing_time)
                
                logger.info(f"✅ Job {job.id} completed in {processing_time:.2f}s")
                
            except asyncio.TimeoutError:
                raise Exception(f"Job timeout after {job.timeout}s")
                
        except Exception as e:
            # Job failed
            job.error = str(e)
            job.retry_count += 1
            
            if job.retry_count <= job.max_retries:
                # Retry job
                job.status = JobStatus.RETRYING
                delay = min(2 ** job.retry_count, 60)  # Exponential backoff
                
                logger.warning(f"🔄 Job {job.id} failed, retrying in {delay}s (attempt {job.retry_count}/{job.max_retries})")
                
                # Re-queue job after delay
                asyncio.create_task(self._requeue_job_after_delay(job, delay))
                self.stats["jobs_retried"] += 1
                
            else:
                # Max retries exceeded
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
                
                logger.error(f"❌ Job {job.id} failed permanently: {e}")
                self.stats["jobs_failed"] += 1
        
        finally:
            # Update job status in storage
            await self._update_job_status(job)
            
    async def _requeue_job_after_delay(self, job: Job, delay: float):
        """Re-queue job after delay for retry"""
        await asyncio.sleep(delay)
        
        # Reset job status
        job.status = JobStatus.PENDING
        job.started_at = None
        
        # Add back to queue
        queue_key = f"job_queue:{job.priority.name.lower()}"
        job_data = json.dumps(asdict(job), default=str)
        
        if hasattr(self.redis_client, 'lpush'):
            await self.redis_client.lpush(queue_key, job_data)
        else:
            await self.redis_client.enqueue(queue_key, job_data)
            
    async def _update_job_status(self, job: Job):
        """Update job status in storage"""
        job_key = f"job:{job.id}"
        
        try:
            if hasattr(self.redis_client, 'hset'):
                await self.redis_client.hset(job_key, mapping=asdict(job))
            else:
                await self.redis_client.set_job(job_key, asdict(job))
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            
    def _update_average_processing_time(self, processing_time: float):
        """Update average processing time statistics"""
        current_avg = self.stats["average_processing_time"]
        processed_count = self.stats["jobs_processed"]
        
        # Calculate running average
        new_avg = ((current_avg * (processed_count - 1)) + processing_time) / processed_count
        self.stats["average_processing_time"] = new_avg
        
    async def get_job_status(self, job_id: str) -> Optional[Job]:
        """Get current status of a job"""
        job_key = f"job:{job_id}"
        
        try:
            if hasattr(self.redis_client, 'hgetall'):
                job_data = await self.redis_client.hgetall(job_key)
                if job_data:
                    return Job(**job_data)
            else:
                job_data = await self.redis_client.get_job(job_key)
                if job_data:
                    return Job(**job_data)
                    
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            
        return None
        
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job"""
        job = await self.get_job_status(job_id)
        
        if job and job.status == JobStatus.PENDING:
            job.status = JobStatus.CANCELLED
            await self._update_job_status(job)
            logger.info(f"🚫 Cancelled job {job_id}")
            return True
            
        return False
        
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        queue_sizes = {}
        
        for priority in JobPriority:
            queue_key = f"job_queue:{priority.name.lower()}"
            try:
                if hasattr(self.redis_client, 'llen'):
                    size = await self.redis_client.llen(queue_key)
                else:
                    size = await self.redis_client.queue_size(queue_key)
                queue_sizes[priority.name] = size
            except Exception:
                queue_sizes[priority.name] = 0
                
        total_queue_size = sum(queue_sizes.values())
        self.stats["queue_size"] = total_queue_size
        
        return {
            "queue_sizes": queue_sizes,
            "total_queue_size": total_queue_size,
            "workers_active": len(self.workers),
            "jobs_processed": self.stats["jobs_processed"],
            "jobs_failed": self.stats["jobs_failed"],
            "jobs_retried": self.stats["jobs_retried"],
            "average_processing_time": round(self.stats["average_processing_time"], 2),
            "is_running": self.is_running
        }
        
    # Built-in task handlers
    async def _handle_verification_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle verification task"""
        claim = payload.get("claim")
        agents = payload.get("agents", [])
        
        # Simulate heavy verification process
        await asyncio.sleep(2)  # Simulate processing time
        
        return {
            "claim": claim,
            "verdict": "TRUE",
            "confidence": 0.85,
            "agents_used": agents,
            "processing_time": 2.0
        }
        
    async def _handle_debate_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle adversarial debate task"""
        claim = payload.get("claim")
        rounds = payload.get("rounds", 3)
        
        # Simulate debate process
        await asyncio.sleep(rounds * 1.5)
        
        return {
            "claim": claim,
            "debate_rounds": rounds,
            "final_verdict": "TRUE",
            "confidence_adjustment": 0.15
        }
        
    async def _handle_reputation_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reputation update task"""
        agent_id = payload.get("agent_id")
        performance_data = payload.get("performance_data", {})
        
        # Simulate reputation calculation
        await asyncio.sleep(0.5)
        
        return {
            "agent_id": agent_id,
            "new_reputation": 0.87,
            "reputation_change": 0.02
        }
        
    async def _handle_cache_warmup_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cache warmup task"""
        cache_keys = payload.get("cache_keys", [])
        
        # Simulate cache warming
        await asyncio.sleep(len(cache_keys) * 0.1)
        
        return {
            "warmed_keys": len(cache_keys),
            "cache_hit_improvement": "15%"
        }

class InMemoryQueue:
    """Fallback in-memory queue when Redis is not available"""
    
    def __init__(self):
        self.queues: Dict[str, List[str]] = {}
        self.jobs: Dict[str, Dict[str, Any]] = {}
        
    async def enqueue(self, queue_key: str, job_data: str):
        if queue_key not in self.queues:
            self.queues[queue_key] = []
        self.queues[queue_key].insert(0, job_data)
        
    async def dequeue(self, queue_key: str) -> Optional[str]:
        if queue_key in self.queues and self.queues[queue_key]:
            return self.queues[queue_key].pop()
        return None
        
    async def queue_size(self, queue_key: str) -> int:
        return len(self.queues.get(queue_key, []))
        
    async def set_job(self, job_key: str, job_data: Dict[str, Any]):
        self.jobs[job_key] = job_data
        
    async def get_job(self, job_key: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_key)

# Global job queue manager
job_queue = JobQueueManager()

# Convenience functions
async def enqueue_verification(claim: str, agents: List[str] = None,
                             priority: JobPriority = JobPriority.NORMAL) -> str:
    """Enqueue verification job"""
    return await job_queue.enqueue_job(
        "verification",
        {"claim": claim, "agents": agents or []},
        priority=priority
    )

async def enqueue_debate(claim: str, rounds: int = 3,
                        priority: JobPriority = JobPriority.HIGH) -> str:
    """Enqueue adversarial debate job"""
    return await job_queue.enqueue_job(
        "debate",
        {"claim": claim, "rounds": rounds},
        priority=priority
    )