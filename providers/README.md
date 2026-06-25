# Providers

This module owns execution backend adapters.

Provider support is intentionally empty for now. Future adapters for DevAgent,
CLI coding agents, LLM SDKs, or subagents should normalize execution results
back to Core Kernel evidence.

Providers own task-local execution loops: reading assigned context, editing,
running checks, and fixing bounded failures. Shiki Core owns project and phase
routing, task contracts, stop conditions, review gates, evidence, and plan
state. A provider may be powerful enough to complete several compatible items in
one session, but each item still returns evidence that Core Kernel can review
and record independently.
