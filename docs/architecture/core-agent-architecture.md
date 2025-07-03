# Core AI Agent Architecture

## Overview

This document describes the internal architecture of individual AI agents in the ConsensusNet system. While the [ECAMAN architecture](./ARCHITECTURE_RECOMMENDATION.md) covers the system-level multi-agent coordination, this document focuses on the core components and data flow within a single agent.

Each agent in ConsensusNet is designed as a modular, self-contained verification unit that can process claims, interact with LLMs, manage its internal state, and produce structured verification results.

## High-Level Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent Instance                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │  Input Processor │    │ State Manager   │                 │
│  │                 │    │                 │                 │
│  │ • Claim Parser  │    │ • Agent Memory  │                 │
│  │ • Context Ext.  │    │ • Session State │                 │
│  │ • Validation    │    │ • Config Cache  │                 │
│  └─────────┬───────┘    └─────────┬───────┘                 │
│            │                      │                         │
│            ▼                      ▼                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Core Reasoning Engine                       │ │
│  │                                                         │ │
│  │ ┌─────────────────┐  ┌─────────────────┐               │ │
│  │ │ LLM Interaction │  │ Evidence Engine │               │ │
│  │ │                 │  │                 │               │ │
│  │ │ • Prompt Mgmt   │  │ • Source Search │               │ │
│  │ │ • API Calls     │  │ • Data Retrieval│               │ │
│  │ │ • Response Parse│  │ • Quality Check │               │ │
│  │ └─────────────────┘  └─────────────────┘               │ │
│  │                                                         │ │
│  │ ┌─────────────────────────────────────────────────────┐ │ │
│  │ │            Verification Logic                       │ │ │
│  │ │                                                     │ │ │
│  │ │ • Claim Analysis      • Confidence Calculation     │ │ │
│  │ │ • Cross-referencing   • Bias Detection             │ │ │
│  │ │ • Logical Reasoning   • Uncertainty Quantification │ │ │
│  │ └─────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────┬───────────────────────┘ │
│                                    │                         │
│                                    ▼                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │               Output Generator                           │ │
│  │                                                         │ │
│  │ • Result Formatting    • Evidence Compilation           │ │
│  │ • Confidence Scoring   • Reasoning Chains              │ │
│  │ • Error Handling       • Structured Response           │ │
│  └─────────────────────────┬───────────────────────────────┘ │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
               ┌─────────────────────────────┐
               │     VerificationResult      │
               │                             │
               │ • Verdict (TRUE/FALSE/...)  │
               │ • Confidence Score          │
               │ • Reasoning Chain           │
               │ • Evidence Sources          │
               │ • Metadata & Timestamps     │
               └─────────────────────────────┘
```

## Core Components

### 1. Input Processor

The Input Processor is responsible for receiving and preprocessing verification claims before they enter the reasoning pipeline.

**Key Responsibilities:**
- **Claim Parsing**: Extract and normalize the claim text
- **Context Extraction**: Identify domain, complexity, and verification requirements
- **Input Validation**: Ensure claim format and content are processable
- **Preprocessing**: Clean text, handle encoding, resolve ambiguities

**Data Structures:**
```python
@dataclass
class ProcessedClaim:
    original_text: str
    normalized_text: str
    domain: str
    complexity: ClaimComplexity
    context: Dict[str, Any]
    preprocessing_metadata: Dict[str, Any]
```

**Methods:**
```python
class InputProcessor:
    def parse_claim(self, raw_claim: str) -> ProcessedClaim
    def extract_context(self, claim: str) -> Dict[str, Any]
    def validate_input(self, claim: str) -> bool
    def normalize_text(self, text: str) -> str
```

### 2. State Manager

The State Manager maintains agent memory, session state, and configuration throughout the verification process.

**Key Responsibilities:**
- **Agent Memory**: Store past verifications and learned patterns
- **Session State**: Track current verification progress and intermediate results
- **Configuration Management**: Handle agent-specific settings and parameters
- **Context Preservation**: Maintain conversational and verification context

**Data Structures:**
```python
@dataclass
class AgentState:
    agent_id: str
    session_id: str
    current_claim: Optional[ProcessedClaim]
    verification_history: List[VerificationResult]
    intermediate_results: Dict[str, Any]
    confidence_calibration: float
    domain_expertise: Dict[str, float]
```

**Methods:**
```python
class StateManager:
    def initialize_session(self, claim: ProcessedClaim) -> str
    def update_state(self, key: str, value: Any) -> None
    def get_historical_context(self, claim_domain: str) -> List[VerificationResult]
    def store_verification(self, result: VerificationResult) -> None
    def cleanup_session(self, session_id: str) -> None
```

### 3. LLM Interaction Module

Handles all interactions with Large Language Models, managing prompts, API calls, and response processing.

**Key Responsibilities:**
- **Prompt Management**: Create, template, and optimize prompts for verification tasks
- **API Communication**: Handle LLM API calls with retry logic and error handling
- **Response Processing**: Parse and validate LLM responses
- **Model Selection**: Choose appropriate models based on task complexity

**Data Structures:**
```python
@dataclass
class LLMRequest:
    prompt: str
    model: str
    parameters: Dict[str, Any]
    context: Optional[str]
    expected_format: str

@dataclass
class LLMResponse:
    content: str
    metadata: Dict[str, Any]
    model_used: str
    tokens_used: int
    confidence: Optional[float]
```

**Methods:**
```python
class LLMInteraction:
    def generate_verification_prompt(self, claim: ProcessedClaim) -> str
    def call_llm(self, request: LLMRequest) -> LLMResponse
    def parse_llm_response(self, response: str) -> Dict[str, Any]
    def handle_api_errors(self, error: Exception) -> None
```

### 4. Evidence Engine

Manages external data sources, fact-checking databases, and evidence gathering for verification.

**Key Responsibilities:**
- **Source Discovery**: Find relevant information sources for the claim
- **Data Retrieval**: Fetch information from databases, APIs, and web sources
- **Quality Assessment**: Evaluate source credibility and information quality
- **Evidence Compilation**: Organize and structure gathered evidence

**Data Structures:**
```python
@dataclass
class Evidence:
    content: str
    source: str
    credibility_score: float
    relevance_score: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class EvidenceBundle:
    supporting_evidence: List[Evidence]
    contradicting_evidence: List[Evidence]
    neutral_evidence: List[Evidence]
    overall_quality: float
```

**Methods:**
```python
class EvidenceEngine:
    def search_sources(self, claim: ProcessedClaim) -> List[str]
    def retrieve_evidence(self, sources: List[str]) -> List[Evidence]
    def assess_credibility(self, source: str) -> float
    def compile_evidence_bundle(self, evidence: List[Evidence]) -> EvidenceBundle
```

### 5. Verification Logic

The core reasoning engine that analyzes claims, processes evidence, and determines verification outcomes.

**Key Responsibilities:**
- **Claim Analysis**: Break down complex claims into verifiable components
- **Cross-referencing**: Compare evidence across multiple sources
- **Logical Reasoning**: Apply logical frameworks to assess claim validity
- **Confidence Calculation**: Quantify uncertainty and reliability of verification
- **Bias Detection**: Identify potential biases in sources or reasoning

**Data Structures:**
```python
@dataclass
class VerificationStep:
    step_type: str
    input_data: Any
    output_data: Any
    confidence: float
    reasoning: str

@dataclass
class VerificationChain:
    steps: List[VerificationStep]
    overall_verdict: str
    final_confidence: float
    uncertainty_factors: List[str]
```

**Methods:**
```python
class VerificationLogic:
    def analyze_claim_structure(self, claim: ProcessedClaim) -> List[str]
    def cross_reference_sources(self, evidence: EvidenceBundle) -> float
    def calculate_confidence(self, verification_chain: VerificationChain) -> float
    def detect_bias(self, evidence: EvidenceBundle) -> List[str]
    def apply_logical_reasoning(self, claim: str, evidence: EvidenceBundle) -> str
```

### 6. Output Generator

Formats and structures the final verification result with comprehensive reasoning and evidence.

**Key Responsibilities:**
- **Result Formatting**: Create structured VerificationResult objects
- **Evidence Compilation**: Organize supporting/contradicting evidence
- **Reasoning Chains**: Document the complete verification process
- **Error Handling**: Manage and report verification failures
- **Quality Assurance**: Validate result completeness and consistency

**Methods:**
```python
class OutputGenerator:
    def format_result(self, verification_chain: VerificationChain) -> VerificationResult
    def compile_evidence_summary(self, evidence: EvidenceBundle) -> List[str]
    def generate_reasoning_chain(self, steps: List[VerificationStep]) -> str
    def handle_verification_errors(self, error: Exception) -> VerificationResult
    def validate_result_quality(self, result: VerificationResult) -> bool
```

## Data Flow

The following diagram illustrates how data flows through the agent components during verification:

```
Input Claim
     │
     ▼
┌────────────────┐     ┌──────────────┐
│ Input Processor│────▶│ State Manager│
└────────────────┘     └──────────────┘
     │                        │
     ▼                        ▼
┌─────────────────────────────────────┐
│        Core Reasoning Engine        │
│                                     │
│  ┌──────────────┐ ┌──────────────┐  │
│  │LLM Interaction│ │Evidence Engine│  │
│  └──────┬───────┘ └──────┬───────┘  │
│         │                │          │
│         ▼                ▼          │
│  ┌──────────────────────────────┐   │
│  │    Verification Logic        │   │
│  └──────────────┬───────────────┘   │
│                 │                   │
└─────────────────┼───────────────────┘
                  │
                  ▼
        ┌──────────────────┐
        │ Output Generator │
        └──────────────────┘
                  │
                  ▼
        ┌──────────────────┐
        │ VerificationResult│
        └──────────────────┘
```

### Step-by-Step Data Flow

1. **Input Reception** (`Input Processor`)
   - Raw claim text received
   - Text normalized and parsed
   - Context and domain extracted
   - Input validated for processing

2. **State Initialization** (`State Manager`)
   - New session created
   - Agent state loaded
   - Historical context retrieved
   - Configuration applied

3. **Evidence Gathering** (`Evidence Engine`)
   - Relevant sources identified
   - External data retrieved
   - Source credibility assessed
   - Evidence bundle compiled

4. **LLM Reasoning** (`LLM Interaction`)
   - Verification prompt generated
   - LLM API called with context
   - Response parsed and validated
   - Reasoning extracted

5. **Verification Analysis** (`Verification Logic`)
   - Claim components analyzed
   - Evidence cross-referenced
   - Logical reasoning applied
   - Confidence calculated
   - Bias detected and mitigated

6. **Result Generation** (`Output Generator`)
   - Verification chain compiled
   - Final verdict determined
   - Evidence summary created
   - Structured result formatted

7. **State Persistence** (`State Manager`)
   - Session state updated
   - Verification stored in history
   - Agent memory updated
   - Session cleaned up

## Configuration and Customization

### Agent Configuration

Each agent can be customized through configuration parameters:

```python
@dataclass
class AgentConfig:
    # Identity
    agent_id: str
    domain_expertise: List[str]
    
    # LLM Configuration
    primary_model: str = "gpt-4o-mini"
    fallback_model: str = "ollama/llama3.2"
    max_tokens: int = 2000
    temperature: float = 0.1
    
    # Verification Parameters
    confidence_threshold: float = 0.7
    evidence_sources: List[str] = field(default_factory=list)
    max_verification_time: int = 30  # seconds
    
    # Memory Settings
    max_history_items: int = 100
    memory_decay_factor: float = 0.95
    
    # Output Settings
    detailed_reasoning: bool = True
    include_uncertainty: bool = True
    evidence_limit: int = 10
```

### Specialization Examples

Different agent types can be created by customizing components:

```python
# Science-focused agent
science_agent = BaseAgent(
    config=AgentConfig(
        domain_expertise=["science", "research", "peer-review"],
        evidence_sources=["pubmed", "arxiv", "scientific_databases"],
        confidence_threshold=0.8  # Higher threshold for scientific claims
    )
)

# News verification agent
news_agent = BaseAgent(
    config=AgentConfig(
        domain_expertise=["current_events", "journalism", "fact_checking"],
        evidence_sources=["news_apis", "fact_check_sites", "primary_sources"],
        max_verification_time=15  # Faster for breaking news
    )
)
```

## Error Handling and Resilience

### Error Categories

1. **Input Errors**
   - Malformed claims
   - Unsupported formats
   - Empty or invalid input

2. **Processing Errors**
   - LLM API failures
   - Network timeouts
   - Memory limitations

3. **Verification Errors**
   - Insufficient evidence
   - Contradictory sources
   - Uncertain outcomes

4. **System Errors**
   - Database connectivity
   - Configuration issues
   - Resource exhaustion

### Resilience Strategies

```python
class ErrorHandler:
    def handle_input_error(self, error: InputError) -> VerificationResult:
        """Return error result with guidance for user"""
        return VerificationResult(
            verdict="ERROR",
            confidence=0.0,
            reasoning=f"Input error: {error.message}",
            metadata={"error_type": "INPUT_ERROR"}
        )
    
    def handle_llm_failure(self, claim: str) -> VerificationResult:
        """Fallback to simpler verification without LLM"""
        return self.simple_verification_fallback(claim)
    
    def handle_evidence_shortage(self, claim: str) -> VerificationResult:
        """Return uncertain result when evidence is insufficient"""
        return VerificationResult(
            verdict="UNCERTAIN",
            confidence=0.3,
            reasoning="Insufficient evidence available for verification",
            metadata={"warning": "LIMITED_EVIDENCE"}
        )
```

## Performance Considerations

### Optimization Strategies

1. **Caching**
   - LLM response caching for similar claims
   - Evidence caching for repeated sources
   - Configuration caching to avoid repeated loading

2. **Parallel Processing**
   - Concurrent evidence gathering
   - Parallel LLM calls for complex claims
   - Asynchronous state updates

3. **Resource Management**
   - Token usage optimization
   - Memory cleanup after verification
   - Connection pooling for external APIs

4. **Load Balancing**
   - Agent instance pooling
   - Claim distribution based on complexity
   - Graceful degradation under load

### Performance Metrics

```python
@dataclass
class PerformanceMetrics:
    verification_time: float
    tokens_used: int
    api_calls_made: int
    evidence_sources_checked: int
    memory_usage: float
    cache_hit_rate: float
```

## Integration with ECAMAN Architecture

This core agent architecture integrates seamlessly with the broader [ECAMAN system architecture](./ARCHITECTURE_RECOMMENDATION.md):

- **Meta-Agent Orchestrator** creates agents using this architecture
- **Adversarial Debate Arena** uses agents in prosecutor/defender roles
- **Graph-Based Consensus Network** aggregates results from multiple agents
- **Swarm Burst Mode** rapidly deploys lightweight versions of these agents

The modular design ensures agents can be:
- Dynamically spawned with different configurations
- Specialized for specific domains or verification types
- Coordinated in multi-agent verification workflows
- Scaled horizontally based on demand

---

*This architecture provides the foundation for reliable, scalable, and intelligent fact verification while maintaining flexibility for future enhancements and research directions.*