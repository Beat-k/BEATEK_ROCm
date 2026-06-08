# BEATEK_ROCm ↔ BEA_TidePool Integration

This guide wires the ROCm GPU inference path (`BEATEK_ROCm`, `BEA_Amplify`,
`BEA_Inference`, or Ollama/llama.cpp ROCm on `gfx1100` Windows) into
`BEA_TidePool` so GPU jobs use the same queue, results zone, and BEA_Pulse
events as the existing TidePool inference pipeline.

---

## Validated Fix Status ✅

> **The BEATEK_ROCm patch has been validated in production.**
> Exit code 2 crash on gfx1100 Windows is resolved. Inference runs stably
> across multiple requests and training epochs. See [Validated Results](#validated-results) below.

---

## Purpose

`TidePoolGPUBridge` provides a stable handoff for the ROCm path when the native
backend on Windows `gfx1100` can terminate with process exit code `2` before a
direct result handoff occurs. The bridge ensures that:

1. GPU input is staged in `/bea_tidepool/queue/`
2. GPU output is staged in `/bea_tidepool/results/`
3. BEA_Pulse receives explicit queue, completion, and failure events
4. Downstream BEA pillars can consume GPU results using the existing
   TidePool results pickup contract

### Patches Applied

The following source-level patches to the ROCm llama.cpp backend eliminate the
exit code 2 crash on `gfx1100` Windows:

| File | Change |
|---|---|
| `ggml-cuda.cu` | KV cache stream affinity — fixes memory ordering race on RDNA3 |
| `common.cuh` | Flash Attention gate for `gfx1100` Windows — disables the unsupported FA path |

**Without these patches:** every request terminates with process exit code `2`
before the model produces output.  
**With these patches:** requests complete fully and results stage correctly into
TidePool.

---

## End-to-End Flow

```text
BEA_Amplify / BEA_Inference
    ↓  submit_gpu_job()
/bea_tidepool/queue/job_<uuid>.bin
    ↓  ROCm llama.cpp / Ollama backend on gfx1100 Windows
    ↓  complete_gpu_job() or fail_gpu_job()
/bea_tidepool/results/job_<uuid>.result
    ↓  TidePoolResultsManager.read_result()
Requesting pillar acknowledges pickup
```

---

## Validated Results

### BEATEK ROCm Benchmark — RX 7900 GRE gfx1100 / Windows 11

**Hardware:**

| Field | Value |
|---|---|
| GPU | AMD Radeon RX 7900 GRE 16GB |
| Arch | gfx1100 |
| Backend | ROCm 7.1 · Windows 11 |
| Layers | 33/33 offloaded to GPU (ngl 99) |
| Model | Mistral 7B Instruct v0.3 Q4_K_M |
| CPU | AMD Ryzen 7 5700X3D |
| RAM | 64 GB |

**Benchmark Run 1** — 10 requests × 200 tokens (2 000 tokens total):

| Req | Latency | Tokens | t/s |
|---|---|---|---|
| [01] | 3.87s | 200 | 51.7 |
| [02] | 2.40s | 200 | 83.4 |
| [03] | 2.40s | 200 | 83.3 |
| [04] | 3.89s | 200 | 50.7 |
| [05] | 3.93s | 200 | 50.9 |
| [06] | 3.93s | 200 | 50.9 |
| [07] | 2.41s | 200 | 83.1 |
| [08] | 2.41s | 200 | 83.1 |
| [09] | 2.42s | 200 | 82.6 |
| [10] | 2.41s | 200 | 83.1 |

| Metric | Value |
|---|---|
| Avg latency | 3.01s |
| Min latency | 2.40s |
| Max latency | 3.93s |
| Avg t/s | 66.5 |
| Overall t/s | 66.5 |

**Benchmark Run 2** — 10 requests × 200 tokens (sustained / warm cache):

| Req | Latency | Tokens | t/s |
|---|---|---|---|
| [01] | 4.04s | 200 | 49.5 |
| [02] | 2.49s | 200 | 80.2 |
| [03] | 2.40s | 200 | 83.3 |
| [04] | 4.02s | 200 | 49.8 |
| [05] | 4.06s | 200 | 49.3 |
| [06] | 4.01s | 200 | 49.8 |
| [07] | 2.41s | 200 | 83.1 |
| [08] | 2.43s | 200 | 82.4 |
| [09] | 2.41s | 200 | 83.1 |
| [10] | 2.42s | 200 | 82.5 |

| Metric | Value |
|---|---|
| Avg latency | 3.07s |
| Min latency | 2.40s |
| Max latency | 4.06s |
| Avg t/s | 65.2 |
| Overall t/s | 65.2 |

Run 2 shows the prompt cache growing naturally (5 prompts → 10 prompts,
~167 MiB KV state) with no instability. The llama.cpp server logs confirm
`update_slots: all slots are idle` cleanly after every request — no hung slots,
no exit code 2.

---

### Community Validation — AMD Developer Community

**Thread:** *Validated fix for gfx1100 Windows ROCm inference crash + VRAM-based heterog*  
**Forum:** AMD Developer Community → ROCm Developers → Getting Started  
**Date:** June 2026

An independent community member (**Jillian_Taylor**, RX 7700 XT / gfx1101,
Ubuntu 24.04 6.8 kernel) tested the BEATEK_ROCm patch against a training
workload and reported complete stabilization:

> *"I tested your fix with a short epoch run (2) followed by a full training run.
> I pulled up numbers from pre-fix for comparison. This completely stabilized the
> training environment! Thank you so much for sharing your work."*

**Training results — Qwen2.5-3B QLoRA, mixed-proficiency-v1 dataset, 1 007 samples:**

| Date | Epochs | Runtime (s) | Steps/sec | Samples/sec | Final Loss | RDNA3 Fix | Stability |
|---|---|---|---|---|---|---|---|
| 2026-05-30 | 13.33 | ~1800 | unstable | unstable | n/a | No | stalls, jitter, hipBLASLt warnings |
| 2026-05-30 | 13.33 | 635.7 | 0.315 | 2.517 | 0.4687 | No | completed but unstable throughput |
| 2026-06-06 | 2 | 829.9 | 0.304 | 2.427 | 1.509 | **Yes** | **fully stable, no ROCm errors** |
| 2026-06-06 | 13.33 | 635.7 | 0.315 | 2.517 | 0.4687 | **Yes** | **fully stable, clean long run** |

Jillian_Taylor also added the following environment variables to stabilize
ROCm + PyTorch on the gfx1101 path:

```bash
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True,max_split_size_mb:256"
export HSA_OVERRIDE_GFX_VERSION="11.0.0"
export HSA_ENABLE_SDMA=1
export ROCM_FORCE_ENABLE_DP=1
```

**BEATEK response (Jax_Jaxxon):**

> *"Satisfaction guaranteed. I'm happy BEATEK services was able to assist.
> We will continue working on ROCm and HIP for future developments and will
> be happy to share."*

---

## 1. Provision TidePool

Create or mount the TidePool working directories where the BEA services can see
them:

```text
/bea_tidepool/
├── hot/
├── warm/
├── cold/
├── queue/
├── results/
└── swap/
```

Set the mount path if you do not use the default:

```bash
export BEA_TIDEPOOL_MOUNT_PATH=/bea_tidepool
```

## 2. Initialize TidePool Components

```python
from BEA_TidePool import (
    TidePoolConfig,
    TidePoolGPUBridge,
    TidePoolInferenceQueue,
    TidePoolResultsManager,
    TidePoolZoneManager,
)

cfg = TidePoolConfig(MOUNT_PATH="/bea_tidepool")
zone_manager = TidePoolZoneManager(mount_path=cfg.MOUNT_PATH, cfg=cfg)
results_manager = TidePoolResultsManager(zone_manager=zone_manager, cfg=cfg)
inference_queue = TidePoolInferenceQueue(zone_manager=zone_manager, cfg=cfg)
gpu_bridge = TidePoolGPUBridge(
    zone_manager=zone_manager,
    results_manager=results_manager,
    inference_queue=inference_queue,
    cfg=cfg,
    pulse_publish=bea_pulse.publish,  # event_type, payload
)
```

## 3. Queue a GPU Job

When `BEA_Amplify` or `BEA_Inference` prepares a ROCm request, submit the input
through the bridge instead of writing directly to the queue:

```python
job = gpu_bridge.submit_gpu_job(
    input_data=b"<prompt-or-tensor-bytes>",
    role_id="ai_coordination",
    source_pillar="BEA_Amplify",
)
```

What happens:

- `TidePoolInferenceQueue.submit_job()` writes
  `/bea_tidepool/queue/job_<uuid>.bin`
- The queue entry is recorded with `source_pillar="gpu_rocm"`
- `tidepool.gpu_job_queued` is emitted with:
  - `job_id`
  - `role_id`
  - `source_pillar`
  - `bytes`
  - `backend="ROCm"`
  - `device="gfx1100"`

## 4. Run ROCm / Ollama Inference

Your GPU worker can now pick up the staged file, invoke the ROCm backend, and
return bytes to the bridge. Keep the worker simple:

1. Read `/bea_tidepool/queue/job_<uuid>.bin`
2. Run ROCm llama.cpp or Ollama ROCm on the `gfx1100` device
3. Capture the raw result bytes
4. Call `complete_gpu_job()` on success
5. Call `fail_gpu_job()` if the backend exits early or returns an error

## 5. Complete the GPU Job

```python
result = gpu_bridge.complete_gpu_job(
    job_id=job.job_id,
    result_data=b"<model-output>",
    role_id="ai_coordination",
    source_pillar="BEA_Amplify",
    latency_s=0.318,
)
```

What happens:

- `TidePoolInferenceQueue.mark_complete(job_id)` closes the queue lifecycle
- `TidePoolResultsManager.write_result(...)` writes
  `/bea_tidepool/results/job_<uuid>.result`
- `tidepool.gpu_job_complete` is emitted with:
  - `job_id`
  - `role_id`
  - `source_pillar`
  - `result_bytes`
  - `latency_s`
  - `backend="ROCm"`
  - `device="gfx1100"`
  - `source_type="GPU"`

Downstream services can then read the result with the existing
`TidePoolResultsManager.read_result()` and clean it up with
`acknowledge(job_id)`.

## 6. Handle ROCm Failure Paths

If ROCm, Ollama, or llama.cpp terminates with the known Windows `gfx1100`
failure mode (for example process exit code `2`), mark the job failed:

```python
gpu_bridge.fail_gpu_job(job.job_id, error="ROCm backend exit code 2")
```

This emits `tidepool.gpu_job_failed` with:

- `job_id`
- `error`
- `backend="ROCm"`
- `device="gfx1100"`

The queue record is marked failed through TidePool's normal lifecycle tracking.

## 7. BEA_Pulse Events to Subscribe To

For GPU-specific telemetry, subscribe to:

- `tidepool.gpu_job_queued`
- `tidepool.gpu_job_complete`
- `tidepool.gpu_job_failed`

You may also continue to use the existing TidePool core events emitted by
`TidePoolInferenceQueue` and `TidePoolResultsManager`, especially if other
consumers already listen for:

- `tidepool.job_queued`
- `tidepool.job_started`
- `tidepool.job_complete`
- `tidepool.job_failed`

## 8. Operational Notes

- Keep the queue and results directories on the TidePool NVMe path, not a
  temporary GPU worker directory.
- Treat `gpu_rocm` as the internal queue source for ROCm-submitted work.
- Preserve the original requesting pillar in the bridge event payloads and
  result writes so downstream routing stays intact.
- If the GPU worker starts processing explicitly, it can still call
  `inference_queue.mark_started(job_id)` before invoking the backend.
- After a successful read, acknowledge the result so the staged result file is
  removed from `/bea_tidepool/results/`.
