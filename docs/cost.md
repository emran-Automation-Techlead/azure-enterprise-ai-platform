# Cost Architecture

> **No exact Azure prices are quoted here.** Prices change by region and over time. Verify current pricing on the Azure pricing pages and in the Azure Pricing Calculator before relying on any figure.

## What drives cost, by service

| Service | How it is billed (concept) | Notes for this design |
|---|---|---|
| **Azure OpenAI** | Per token, input and output, per model | Dominant variable cost at scale. `gpt-4.1-mini` is a small model. Embeddings are billed per token too (one-time for indexing + one small call per question). |
| **Azure AI Search** | Per service tier and units (replicas × partitions), **even when idle** | The largest fixed cost in this project (Basic tier). Delete the service when not in use. |
| **Blob Storage** | Per GB stored + operations | Negligible for 20 small files. |
| **Azure Container Apps** | Per vCPU-second, memory-second and requests; free grants may apply | `min replicas = 1` means it runs continuously. Scale-to-zero saves cost at the price of cold starts. |
| **Application Insights / Log Analytics** | Per GB ingested | Traces were noisy (SDK HTTP logs); lowering log levels reduces ingestion. |
| **Key Vault** | Per operation | Very small. |
| **Container Registry** | Per tier per day + storage | Small for one image. |
| **Networking** | Egress | Small here; larger with private endpoints and multi-region designs. |

## Token usage (measured in this project)
A grounded answer used roughly **800 to 1,500 tokens** per question (prompt with up to four documents + answer). Questions blocked by rules or refused by the grounding gate used **0 model tokens**, which is itself a cost control.

## Ways to reduce cost
- **Grounding gate and rules before the model:** refusals and "not enough information" cost no generation.
- **Smaller model** for routing and grounded answers; reserve larger models for hard cases.
- **Fewer, shorter retrieved chunks:** send only documents above the relevance cutoff (done: `MIN_DOC_SCORE`).
- **Caching:** cache answers and embeddings for repeated questions (not built).
- **Scale rules:** scale to zero off-hours; cap max replicas.
- **Log hygiene:** reduce telemetry volume.

## Scaling considerations
- Search: add replicas for query throughput/availability, partitions for index size.
- OpenAI: tokens-per-minute quotas and rate limiting (HTTP 429) need retry/back-off and possibly multiple deployments.
- Container Apps: scale on concurrent requests.

## Lifecycle in this project
Resources were created in one resource group so that the whole deployment can be removed by deleting that group once the evidence is saved. Until it is deleted, the always-on resources (notably Azure AI Search and the Container App with one minimum replica) continue to bill.
