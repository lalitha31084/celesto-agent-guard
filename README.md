# Celesto Agent Guard

## Problem statement
Security engineers need a way to validate agent behavior in isolated environments without risking their own machines or sensitive data. An agent runs tasks inside a Celesto sandbox, executes commands with safety hooks and network policy, records all actions in an audit log, and recovers from mid-task failure by applying a named policy. The proof is a containment report and reliability metrics showing the sandbox held when attacked, along with a clean run ledger entry proving execution_target is celesto_sandbox.

## How I used Celesto
- **safety_hooks**: Implemented callbacks that block dangerous commands before they reach the guest, providing deterministic control even if prompts are injected. Evidence: app/agent/hooks.py
- **network_policy**: Enforced allow-list network policy so exfiltration attempts cannot reach external hosts. Evidence: app/agent/policy.py

## Eval report
We ran the core task 20 times on fresh sandboxes. See reports/reliability.json for full details. Success rate is 0.85 with median wall clock ~22s and median boot-to-ready ~2.4s. Post-mortem in reports/postmortem.md.

## Containment test
We fed a prompt-injected attempt to exfiltrate data (curl to an external host). The safety hook blocked it and network policy constrained traffic. The host remained untouched; evidence in reports/evidence/containment.log.

## State and failure design
When step 7 of 10 fails, we apply the **resume** policy: the same sandbox is resumed, preserving steps 1-6 artifacts and avoiding full re-provisioning. See reports/failure_policy.json and reports/failure_trace.jsonl.

## Setup
1. Copy .env.example to .env and fill placeholders
2. Run `docker-compose up --build`
3. API will be healthy at http://localhost:8080/health
4. Tests can be run with `pytest -v`

## Architecture
- Agent (app/agent) runs inside Celesto sandbox (execution zone)
- Control plane: FastAPI API (port 8080) + Postgres ledger
- All commands logged to logs/commands.jsonl with execution_target celesto_sandbox
- Every sandbox cleaned up on success/failure/interrupt

Demo: demo/walkthrough.mp4 (guest visible)
