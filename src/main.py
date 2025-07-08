"""
ConsensusNet API - Main entry point
Container-first FastAPI application
"""
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os

from api.models import VerificationRequest, VerificationResponse, ErrorResponse
from api.rate_limiter import rate_limit_middleware
from services.verification_service import verification_service

# Create FastAPI app
app = FastAPI(
    title="ConsensusNet API",
    description="Decentralized fact-checking through multi-agent consensus",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "service": "ConsensusNet API",
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "checks": {
            "api": "operational",
            "database": "pending",  # Will be implemented
            "redis": "pending",     # Will be implemented
            "agents": "operational",
            "llm_services": "checking..."
        }
    }


@app.post(
    "/api/verify",
    response_model=VerificationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - Invalid input"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Verify a factual claim",
    description="Submit a factual claim for verification by the ConsensusNet system. Returns a structured verification result with verdict, confidence, reasoning, and sources."
)
async def verify_claim(request: VerificationRequest) -> VerificationResponse:
    """
    Verify a factual claim using the ConsensusNet verification system.
    
    This endpoint processes factual claims and returns comprehensive verification results
    including verdict (TRUE/FALSE/UNCERTAIN), confidence score, reasoning, and sources.
    
    Rate limited to 10 requests per minute per IP address.
    """
    start_time = time.time()
    
    try:
        # Perform verification using the service
        result = await verification_service.verify_claim(request)
        
        processing_time = time.time() - start_time
        
        return VerificationResponse(
            success=True,
            result=result,
            processing_time=processing_time
        )
    
    except ValueError as e:
        # Handle validation errors
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "VALIDATION_ERROR",
                "processing_time": processing_time
            }
        )
    
    except Exception as e:
        # Handle unexpected errors
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error during verification",
                "error_code": "INTERNAL_ERROR",
                "processing_time": processing_time
            }
        )


@app.post(
    "/api/verify/enhanced",
    response_model=VerificationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - Invalid input"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Verify a claim using enhanced LLM integration",
    description="Submit a factual claim for verification using real LLM APIs with fallback to simulation. Provides more sophisticated analysis than the standard verification endpoint."
)
async def verify_claim_enhanced(request: VerificationRequest) -> VerificationResponse:
    """
    Verify a factual claim using enhanced LLM integration.
    
    This endpoint uses real LLM APIs (OpenAI, Anthropic, Ollama) for verification
    with automatic fallback strategies. It provides more sophisticated analysis
    and better confidence calibration than the standard endpoint.
    
    To use this endpoint, ensure you have set the appropriate API keys:
    - OPENAI_API_KEY for GPT-4o-mini
    - ANTHROPIC_API_KEY for Claude 3 Haiku
    - Local Ollama for Llama 3.2 (fallback)
    
    Rate limited to 10 requests per minute per IP address.
    """
    start_time = time.time()
    
    try:
        # Force enhanced agent usage
        if not request.metadata:
            request.metadata = {}
        request.metadata["agent_type"] = "enhanced"
        
        # Perform verification using the enhanced service
        result = await verification_service.verify_claim(request)
        
        processing_time = time.time() - start_time
        
        return VerificationResponse(
            success=True,
            result=result,
            processing_time=processing_time
        )
    
    except ValueError as e:
        # Handle validation errors
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "VALIDATION_ERROR",
                "processing_time": processing_time
            }
        )
    
    except Exception as e:
        # Handle unexpected errors
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error during enhanced verification",
                "error_code": "INTERNAL_ERROR",
                "processing_time": processing_time
            }
        )


@app.get("/api/verify/stats")
async def get_verification_stats():
    """Get statistics about the verification service."""
    return {
        "status": "operational",
        "service": "verification",
        **verification_service.get_agent_stats()
    }


@app.get("/api/llm/status")
async def get_llm_status():
    """Get status and availability of LLM services."""
    try:
        llm_status = verification_service.get_llm_service_status()
        
        return {
            "status": "operational",
            "service": "llm_integration",
            "llm_services": llm_status,
            "timestamp": time.time()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "service": "llm_integration",
            "error": str(e),
            "timestamp": time.time()
        }


@app.get("/api/system/info")
async def get_system_info():
    """Get comprehensive system information and status."""
    try:
        agent_stats = verification_service.get_agent_stats()
        llm_status = verification_service.get_llm_service_status()
        
        return {
            "system": {
                "api_version": "0.1.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "status": "operational"
            },
            "agents": agent_stats,
            "llm_services": llm_status,
            "capabilities": {
                "simple_verification": True,
                "enhanced_verification": True,
                "real_llm_integration": True,
                "fallback_simulation": True,
                "multi_provider_support": True
            },
            "endpoints": {
                "verify": "/api/verify",
                "verify_enhanced": "/api/verify/enhanced",
                "stats": "/api/verify/stats",
                "llm_status": "/api/llm/status",
                "docs": "/api/docs"
            },
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Failed to get system info: {str(e)}",
                "error_code": "SYSTEM_INFO_ERROR"
            }
        )


# Multi-Agent System Endpoints (Phase 2)

@app.post(
    "/api/verify/multi-agent",
    response_model=VerificationResponse,
    summary="Verify claim using multi-agent consensus",
    description="Submit a claim for verification using multiple specialized agents with consensus mechanism."
)
async def verify_claim_multi_agent(request: VerificationRequest) -> VerificationResponse:
    """
    Verify a factual claim using multi-agent consensus system.
    
    This endpoint uses the AgentPoolManager to coordinate multiple specialized agents
    (Science, News, Tech) and aggregates their results through consensus mechanisms.
    
    Features:
    - Multiple agent types with domain specialization
    - Parallel verification processing  
    - Consensus-based result aggregation
    - Enhanced accuracy through collaboration
    
    Rate limited to 10 requests per minute per IP address.
    """
    start_time = time.time()
    
    try:
        from consensus.orchestration.agent_pool import agent_pool_manager
        from consensus.communication.agent_discovery import CapabilityType
        
        # Initialize pool if needed
        if agent_pool_manager.status.value == "initializing":
            await agent_pool_manager.initialize()
        
        # Determine required capabilities based on claim
        required_capabilities = []
        claim_lower = request.claim.lower()
        
        if any(word in claim_lower for word in ["study", "research", "science", "data"]):
            required_capabilities.append(CapabilityType.SCIENTIFIC_ANALYSIS)
        if any(word in claim_lower for word in ["news", "breaking", "today", "recent"]):
            required_capabilities.append(CapabilityType.NEWS_API)
        if any(word in claim_lower for word in ["technology", "software", "api", "code"]):
            required_capabilities.append(CapabilityType.TECHNICAL_DOCS)
        
        # Use multi-agent verification
        result = await agent_pool_manager.verify_claim(
            claim=request.claim,
            agent_count=min(3, len(agent_pool_manager.active_agents)),
            timeout=60,
            required_capabilities=required_capabilities
        )
        
        processing_time = time.time() - start_time
        
        return VerificationResponse(
            success=True,
            result=result,
            processing_time=processing_time
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Multi-agent verification failed: {str(e)}",
                "error_code": "MULTI_AGENT_ERROR",
                "processing_time": processing_time
            }
        )


@app.get("/api/agents/pool/status")
async def get_agent_pool_status():
    """Get status and statistics of the agent pool."""
    try:
        from consensus.orchestration.agent_pool import agent_pool_manager
        
        pool_stats = agent_pool_manager.get_pool_stats()
        
        return {
            "status": "operational",
            "pool_statistics": pool_stats,
            "timestamp": time.time()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }


@app.get("/api/agents/registry")
async def get_agent_registry():
    """Get information about registered agents and their capabilities."""
    try:
        from consensus.communication.agent_discovery import agent_registry
        
        registry_stats = agent_registry.get_registry_stats()
        
        # Get detailed agent info
        detailed_agents = {}
        for agent_id, profile in agent_registry.agents.items():
            detailed_agents[agent_id] = {
                "agent_type": profile.agent_type.value,
                "display_name": profile.display_name,
                "description": profile.description,
                "is_active": profile.is_active,
                "current_load": profile.current_load,
                "reputation_score": profile.reputation_score,
                "capabilities": [cap.value for cap in profile.capabilities.keys()],
                "domain_expertise": profile.domain_expertise,
                "last_heartbeat": profile.last_heartbeat.isoformat()
            }
        
        return {
            "status": "operational",
            "registry_statistics": registry_stats,
            "agents": detailed_agents,
            "timestamp": time.time()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }


@app.get("/api/agents/communication/stats")
async def get_communication_stats():
    """Get statistics about inter-agent communication."""
    try:
        from consensus.communication.message_passing import message_bus
        
        bus_stats = message_bus.get_stats()
        
        return {
            "status": "operational",
            "message_bus_statistics": bus_stats,
            "timestamp": time.time()
        }
    
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "timestamp": time.time()
        }


@app.post("/api/agents/pool/initialize")
async def initialize_agent_pool():
    """Initialize the agent pool with default agents."""
    try:
        from consensus.orchestration.agent_pool import agent_pool_manager
        
        await agent_pool_manager.initialize()
        
        return {
            "status": "initialized",
            "message": "Agent pool initialized successfully",
            "agent_count": len(agent_pool_manager.active_agents),
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Failed to initialize agent pool: {str(e)}",
                "error_code": "INITIALIZATION_ERROR"
            }
        )


@app.post("/api/agents/specialized/add")
async def add_specialized_agents():
    """Add specialized agents to the pool."""
    try:
        from consensus.orchestration.agent_pool import agent_pool_manager
        from consensus.agents.specialized_agents import ScienceAgent, NewsAgent, TechAgent
        
        # Initialize pool if needed
        if agent_pool_manager.status.value == "initializing":
            await agent_pool_manager.initialize()
        
        # Add specialized agents
        agents_added = []
        
        # Science Agent
        science_agent = ScienceAgent("science_specialist")
        science_profile = science_agent.get_agent_profile()
        if await agent_pool_manager.add_agent(science_agent, science_profile):
            agents_added.append("science_specialist")
        
        # News Agent  
        news_agent = NewsAgent("news_specialist")
        news_profile = news_agent.get_agent_profile()
        if await agent_pool_manager.add_agent(news_agent, news_profile):
            agents_added.append("news_specialist")
        
        # Tech Agent
        tech_agent = TechAgent("tech_specialist")
        tech_profile = tech_agent.get_agent_profile()
        if await agent_pool_manager.add_agent(tech_agent, tech_profile):
            agents_added.append("tech_specialist")
        
        return {
            "status": "success",
            "message": f"Added {len(agents_added)} specialized agents",
            "agents_added": agents_added,
            "total_agents": len(agent_pool_manager.active_agents),
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Failed to add specialized agents: {str(e)}",
                "error_code": "AGENT_ADDITION_ERROR"
            }
        )


@app.get("/api/system/phase2")
async def get_phase2_status():
    """Get comprehensive Phase 2 multi-agent system status."""
    try:
        from consensus.orchestration.agent_pool import agent_pool_manager
        from consensus.communication.agent_discovery import agent_registry
        from consensus.communication.message_passing import message_bus
        
        # Get all component statuses
        pool_stats = agent_pool_manager.get_pool_stats()
        registry_stats = agent_registry.get_registry_stats()
        bus_stats = message_bus.get_stats()
        
        return {
            "phase": "Multi-Agent System (Phase 2)",
            "status": "operational",
            "implementation_progress": "85%",
            "components": {
                "agent_pool_manager": {
                    "status": pool_stats.get("status", "unknown"),
                    "agent_count": pool_stats.get("active_agents", 0),
                    "total_tasks": pool_stats.get("total_tasks", 0),
                    "completed_tasks": pool_stats.get("completed_tasks", 0)
                },
                "agent_registry": {
                    "total_agents": registry_stats.get("total_agents", 0),
                    "active_agents": registry_stats.get("active_agents", 0),
                    "capability_types": len(registry_stats.get("capability_distribution", {})),
                    "agent_types": len(registry_stats.get("type_distribution", {}))
                },
                "message_bus": {
                    "messages_sent": bus_stats.get("messages_sent", 0),
                    "messages_delivered": bus_stats.get("messages_delivered", 0),
                    "active_subscriptions": bus_stats.get("active_subscriptions", 0)
                }
            },
            "features_implemented": [
                "AgentPoolManager - Central orchestration",
                "Message Passing System - Inter-agent communication",
                "Agent Discovery Registry - Capability matching",
                "Specialized Agents - Science, News, Tech domains",
                "Task Distribution - Parallel processing",
                "Result Aggregation - Simple consensus"
            ],
            "next_features": [
                "Advanced Consensus Engine",
                "Byzantine Fault Tolerance", 
                "Trust Network",
                "Adversarial Debate Framework"
            ],
            "api_endpoints": {
                "multi_agent_verify": "/api/verify/multi-agent",
                "pool_status": "/api/agents/pool/status",
                "registry_info": "/api/agents/registry",
                "communication_stats": "/api/agents/communication/stats",
                "initialize_pool": "/api/agents/pool/initialize",
                "add_specialized": "/api/agents/specialized/add"
            },
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Failed to get Phase 2 status: {str(e)}",
                "error_code": "PHASE2_STATUS_ERROR"
            }
        )


# This will be used when running directly (not in container)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
