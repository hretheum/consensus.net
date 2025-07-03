# Agent Data Flow Visualization

This document provides detailed visualizations of data flow within the Core AI Agent Architecture, complementing the main [core-agent-architecture.md](./core-agent-architecture.md) document.

## Component Interaction Flow

```mermaid
graph TD
    A[Raw Claim Input] --> B[Input Processor]
    B --> C[ProcessedClaim]
    C --> D[State Manager]
    D --> E[AgentState]
    
    C --> F[Evidence Engine]
    F --> G[Evidence Gathering]
    G --> H[EvidenceBundle]
    
    C --> I[LLM Interaction]
    I --> J[LLM API Call]
    J --> K[LLMResponse]
    
    H --> L[Verification Logic]
    K --> L
    E --> L
    L --> M[VerificationChain]
    
    M --> N[Output Generator]
    N --> O[VerificationResult]
    
    O --> P[State Manager Update]
    P --> Q[Session Cleanup]
    
    style A fill:#e1f5fe
    style O fill:#c8e6c9
    style L fill:#fff3e0
    style F fill:#f3e5f5
    style I fill:#fce4ec
```

## Detailed Process Flow with Data Structures

```mermaid
sequenceDiagram
    participant U as User/System
    participant IP as InputProcessor
    participant SM as StateManager
    participant EE as EvidenceEngine
    participant LLM as LLMInteraction
    participant VL as VerificationLogic
    participant OG as OutputGenerator
    
    U->>IP: Raw claim string
    IP->>IP: parse_claim()
    IP->>IP: extract_context()
    IP->>IP: validate_input()
    IP->>SM: ProcessedClaim
    
    SM->>SM: initialize_session()
    SM->>SM: create AgentState
    SM->>VL: AgentState + ProcessedClaim
    
    VL->>EE: search_sources(claim)
    EE->>EE: retrieve_evidence()
    EE->>EE: assess_credibility()
    EE->>VL: EvidenceBundle
    
    VL->>LLM: generate_verification_prompt()
    LLM->>LLM: call_llm(LLMRequest)
    LLM->>LLM: parse_llm_response()
    LLM->>VL: LLMResponse
    
    VL->>VL: analyze_claim_structure()
    VL->>VL: cross_reference_sources()
    VL->>VL: calculate_confidence()
    VL->>VL: detect_bias()
    VL->>OG: VerificationChain
    
    OG->>OG: format_result()
    OG->>OG: compile_evidence_summary()
    OG->>OG: generate_reasoning_chain()
    OG->>SM: VerificationResult
    
    SM->>SM: store_verification()
    SM->>SM: cleanup_session()
    SM->>U: VerificationResult
```

## Data Structure Relationships

```mermaid
classDiagram
    class ProcessedClaim {
        +string original_text
        +string normalized_text
        +string domain
        +ClaimComplexity complexity
        +dict context
        +dict preprocessing_metadata
        +datetime timestamp
    }
    
    class Evidence {
        +string content
        +string source
        +float credibility_score
        +float relevance_score
        +datetime timestamp
        +dict metadata
    }
    
    class EvidenceBundle {
        +List~Evidence~ supporting_evidence
        +List~Evidence~ contradicting_evidence
        +List~Evidence~ neutral_evidence
        +float overall_quality
        +total_evidence_count() int
    }
    
    class LLMRequest {
        +string prompt
        +string model
        +dict parameters
        +string context
        +string expected_format
        +int max_tokens
        +float temperature
    }
    
    class LLMResponse {
        +string content
        +dict metadata
        +string model_used
        +int tokens_used
        +float confidence
        +datetime timestamp
    }
    
    class VerificationStep {
        +string step_type
        +any input_data
        +any output_data
        +float confidence
        +string reasoning
        +datetime timestamp
    }
    
    class VerificationChain {
        +List~VerificationStep~ steps
        +string overall_verdict
        +float final_confidence
        +List~string~ uncertainty_factors
        +float processing_time
    }
    
    class AgentState {
        +string agent_id
        +string session_id
        +ProcessedClaim current_claim
        +List~VerificationResult~ verification_history
        +dict intermediate_results
        +float confidence_calibration
        +dict domain_expertise
        +datetime session_start_time
        +add_verification(result) void
    }
    
    class VerificationResult {
        +string claim
        +string verdict
        +float confidence
        +string reasoning
        +List~string~ sources
        +List~string~ evidence
        +dict metadata
        +datetime timestamp
        +string agent_id
    }
    
    ProcessedClaim --> AgentState : stored_in
    Evidence --> EvidenceBundle : aggregated_into
    EvidenceBundle --> VerificationChain : feeds_into
    LLMRequest --> LLMResponse : produces
    LLMResponse --> VerificationChain : contributes_to
    VerificationStep --> VerificationChain : part_of
    VerificationChain --> VerificationResult : generates
    VerificationResult --> AgentState : stored_in
```

## Error Handling Flow

```mermaid
graph TD
    A[Processing Step] --> B{Error Occurred?}
    B -->|No| C[Continue Normal Flow]
    B -->|Yes| D[Identify Error Type]
    
    D --> E[Input Error]
    D --> F[LLM Error]
    D --> G[Evidence Error]
    D --> H[System Error]
    
    E --> I[Return Error Result with User Guidance]
    F --> J[Fallback to Simpler Verification]
    G --> K[Return Uncertain Result with Warning]
    H --> L[Retry with Exponential Backoff]
    
    I --> M[Log Error for Analysis]
    J --> M
    K --> M
    L --> N{Retry Successful?}
    
    N -->|Yes| C
    N -->|No| O[Return System Error Result]
    O --> M
    
    M --> P[Update Performance Metrics]
    P --> Q[End]
    
    style A fill:#e3f2fd
    style D fill:#fff3e0
    style E fill:#ffebee
    style F fill:#fff8e1
    style G fill:#f3e5f5
    style H fill:#fce4ec
```

## State Management Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Idle
    
    Idle --> Initializing : New Claim Received
    Initializing --> Processing : Session Created
    
    Processing --> GatheringEvidence : Evidence Search
    GatheringEvidence --> LLMProcessing : Evidence Found
    LLMProcessing --> AnalyzingResults : LLM Response
    AnalyzingResults --> GeneratingOutput : Analysis Complete
    GeneratingOutput --> Completed : Result Generated
    
    Processing --> Error : Input Error
    GatheringEvidence --> Error : Evidence Error
    LLMProcessing --> Error : LLM Error
    AnalyzingResults --> Error : Analysis Error
    GeneratingOutput --> Error : Output Error
    
    Error --> Completed : Error Handled
    
    Completed --> Cleanup : Store Results
    Cleanup --> Idle : Session Ended
    
    Error --> Retry : Recoverable Error
    Retry --> Processing : Retry Attempt
    
    note right of Processing
        AgentState tracks current
        session and progress
    end note
    
    note right of Error
        Error handling preserves
        session state for debugging
    end note
```

## Component Integration Patterns

### 1. Pipeline Pattern (Main Flow)

```mermaid
graph LR
    A[Input] --> B[Process] --> C[Reason] --> D[Output]
    
    subgraph "Process Stage"
        B1[Parse] --> B2[Validate] --> B3[Normalize]
    end
    
    subgraph "Reason Stage"
        C1[Gather] --> C2[Analyze] --> C3[Verify]
    end
    
    B --> B1
    B3 --> C
    C --> C1
    C3 --> D
```

### 2. Adapter Pattern (LLM Integration)

```mermaid
graph TD
    A[Agent Logic] --> B[LLM Adapter Interface]
    B --> C[OpenAI Adapter]
    B --> D[Ollama Adapter]
    B --> E[Future LLM Adapter]
    
    C --> F[OpenAI API]
    D --> G[Ollama API]
    E --> H[Future LLM API]
    
    style B fill:#e1f5fe
    style A fill:#f3e5f5
```

### 3. Observer Pattern (State Management)

```mermaid
graph TD
    A[AgentState] --> B[State Change Event]
    B --> C[Metrics Collector]
    B --> D[Logger]
    B --> E[Performance Monitor]
    B --> F[Debug Tracer]
    
    style A fill:#fff3e0
    style B fill:#e8f5e8
```

## Performance and Monitoring Data Flow

```mermaid
graph TD
    A[Verification Process] --> B[Performance Metrics Collection]
    
    B --> C[Timing Data]
    B --> D[Resource Usage]
    B --> E[API Call Stats]
    B --> F[Cache Performance]
    
    C --> G[PerformanceMetrics Object]
    D --> G
    E --> G
    F --> G
    
    G --> H[Metrics Storage]
    G --> I[Real-time Monitoring]
    G --> J[Performance Optimization]
    
    style A fill:#e3f2fd
    style G fill:#fff3e0
    style H fill:#f3e5f5
    style I fill:#e8f5e8
    style J fill:#fce4ec
```

## Parallel Processing Flow

For complex claims requiring multiple verification approaches:

```mermaid
graph TD
    A[Complex Claim] --> B[Claim Decomposition]
    B --> C[Sub-claim 1]
    B --> D[Sub-claim 2]
    B --> E[Sub-claim 3]
    
    C --> F[Evidence Gathering 1]
    D --> G[Evidence Gathering 2]
    E --> H[Evidence Gathering 3]
    
    F --> I[LLM Analysis 1]
    G --> J[LLM Analysis 2]
    H --> K[LLM Analysis 3]
    
    I --> L[Result Aggregation]
    J --> L
    K --> L
    
    L --> M[Final Verification Result]
    
    style A fill:#e1f5fe
    style L fill:#fff3e0
    style M fill:#c8e6c9
```

---

These diagrams provide visual representations of the data flow patterns described in the core agent architecture documentation, helping developers understand the relationships between components and the flow of information through the verification process.