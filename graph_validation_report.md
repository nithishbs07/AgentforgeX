# Graph Extraction Validation Report

## Text Input
"TCP is a transport protocol. It uses IP at the network layer. AIMD is used for congestion control in TCP."

## Extracted Entities
1. **TCP** (Type: `Protocols`, Confidence: 0.95, ID: `doc123:TCP`)
2. **IP** (Type: `Protocols`, Confidence: 0.95, ID: `doc123:IP`)
3. **AIMD** (Type: `Algorithms`, Confidence: 0.95, ID: `doc123:AIMD`)
4. **congestion control** (Type: `Networking Terms`, Confidence: 0.95, ID: `doc123:congestion control`)

## Extracted Relationships
1. **TCP** -[`USES`]-> **congestion control** (Confidence: 0.92)
2. **AIMD** -[`IMPLEMENTS`]-> **congestion control** (Confidence: 0.90)
3. **TCP** -[`CONNECTS_TO`]-> **IP** (Confidence: 0.90)

## Latency Metrics
- **Entity Extraction Latency**: 83.9 seconds (83887.72 ms)
- **Relationship Extraction Latency**: 75.9 seconds (75875.29 ms)

## Status
✅ **Success**. EntityExtractor and RelationshipExtractor both successfully invoked `qwen2.5-coder:7b` on Ollama, returning rich structural schema rather than the regex fallback mode.
