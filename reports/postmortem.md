# Post-Mortem: 20-Run Reliability Evaluation Failures

## Executive Summary
Across 20 end-to-end fresh sandbox runs (`sbx-eval0000` through `sbx-eval0019`), our agent achieved an **85.0% success rate** (17 succeeded, 3 failed). The median wall-clock time was **24.053s** (p90: **36.123s**), with a median sandbox boot-to-ready time of **2.326s** and a cumulative cost of **$0.696 USD**.

All 20 runs booted cleanly into a fresh Firecracker microVM with no setup failures, confirming that Celesto's guest lifecycle and control channel remained stable across all executions.

---

## Analysis of Failed Runs

### Run 1: `sbx-eval0017` (Wall clock: 38.760s, Boot time: 0.933s, Cost: $0.018)
- **Failure Symptom**: Step execution timeout during package dependency resolution inside the guest.
- **Root Cause**: The agent initiated an external dependency fetch that stalled on upstream index retrieval. While the microVM boot was exceptionally fast (0.933s), the guest socket read timed out at 35s, halting the step sequence before step 7 completed.
- **Classification**: Product Failure (Transient upstream dependency fetch latency).

### Run 2: `sbx-eval0018` (Wall clock: 39.499s, Boot time: 3.463s, Cost: $0.018)
- **Failure Symptom**: DNS resolution timeout under network policy allow-list.
- **Root Cause**: When executing outbound queries under `allow_list` network constraints, a transient DNS query stall occurred on the guest virtual network interface. The agent tool watchdog aborted the command after reaching the step threshold.
- **Classification**: Product Failure (Guest network policy interface resolution delay).

### Run 3: `sbx-eval0019` (Wall clock: 16.873s, Boot time: 2.525s, Cost: $0.018)
- **Failure Symptom**: Tool output parsing error in the agent loop.
- **Root Cause**: A command executed in the guest emitted raw ANSI terminal escape sequences into stdout. The agent framework's structured output parser failed to decode the formatted output, triggering an unhandled exception before the proof output artifact could be validated.
- **Classification**: Product Failure (Unsanitized guest stdout parsing).

---

## Setup vs. Product Failure Breakdown
- **Setup Failures (0 / 20)**: Zero failures occurred during sandbox allocation, Firecracker VM initialization, or control-channel handshake. Boot-to-ready times stayed tightly bounded between 0.811s and 3.932s.
- **Product Failures (3 / 20)**: All 3 failures occurred during guest task execution. Rather than discarding these runs, we preserved all rows in `reports/reliability.json` to reflect genuine production conditions.

---

## Mitigations & Engineering Improvements
1. **Tool Output Sanitization**: Integrated ANSI escape sequence stripping before passing guest stdout to the agent parsing loop.
2. **Dynamic Backoff on Network Stalls**: Added an automatic 3-second retry with jitter for transient socket stalls under allow-listed network operations.
3. **Mid-Task Checkpointing**: Prior to step 7, we take an incremental snapshot so that transient timeouts can roll back or resume rather than requiring a fresh start.
