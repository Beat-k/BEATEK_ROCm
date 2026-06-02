⟦TCS⟧
DOMAIN:       beatek.platform
DOC_TYPE:     readme.integration
PLATFORM:     BEA_Aura_CDE_HV
VERSION:      2026.06.01
AUTHORITY:    draft
COSIGN:       Jeremy F. Jackson (Jaxxon) · BEATEK Holdings LLC
TRIBUNAL:     PENDING
STAMP_ID:     TCS-2026-0601-BEATEK-TIDEPOOL-GPU-BRIDGE-001
⟦/TCS⟧

# BEATEK_ROCm × BEA_TidePool Integration

**Owner:** Jeremy F. Jackson · BEATEK Holdings, LLC
**Repos:** [Beat-k/BEATEK_ROCm](https://github.com/Beat-k/BEATEK_ROCm) · [Beat-k/BEA_TidePool](https://github.com/Beat-k/BEA_TidePool)
**Status:** ✅ Phase 1 complete — GPU inference validated at 108 t/s · Phase 2 (TidePool wiring) is the active critical path

---

## What This Document Is

This is the integration playbook for connecting `BEATEK_ROCm` (the gfx1100 Windows
ROCm crash fix) to `BEA_TidePool` (the Coral TPU CacheRAM staging layer). It covers
every step required — from fixing the Ollama exit code 2 crash, through applying the
BEATEK patches, to wiring GPU inference results into TidePool's results zone so
BEA_Inference can route GPU and Coral TPU jobs through a single unified pipeline.

Until Phase 1 is complete, the GPU slot in BEA_Inference is blocked. This document
is the single source of truth for unblocking it.

---

## The Problem

### The Crash

Ollama on Windows crashes with exit code 2 when loading any model on a gfx1100 GPU
(AMD RX 7900 / 7900 GRE / 7900 XTX). The crash occurs at KV cache initialization —
after the GPU is detected, during the first graph execution setup.

```
library=ROCm compute=gfx1100 total="16.0 GiB" available="14.9 GiB"
[exit code 2]
```

Root cause: `ggml-hip.dll` allocates KV cache memory on the default HIP stream, then
immediately accesses it via a separately created compute stream. On Linux, the ROCm
driver uses unified VM and tolerates this. On Windows ROCm 6.x, the driver enforces
stream affinity — the pointer is invalid on the compute stream without an explicit
sync barrier. The result is an access violation (0xc0000005) at a deterministic
address every single run.

A second issue — Flash Attention on gfx1100 Windows creates split K/V view tensors
with a memory layout that triggers a secondary fault even with the stream fix applied.

### Why TidePool Is Blocked

BEA_Inference routes LLM generation jobs to the GPU slot. That slot is wired, the
routing logic is in place, BEA_Amplify is ready to measure latency — but every
attempt to use the GPU ends in exit code 2. Until the crash is fixed:

- GPU inference is unavailable
- BEA_Inference falls back to CPU (~4–60s per generation)
- `tidepool_gpu_bridge.py` has nothing to receive — no GPU results land in TidePool

### The Dependency Chain

```
ROCm gfx1100 crash
    → GPU slot in BEA_Inference blocked
        → BEA_Amplify cannot confirm source_type: GPU
            → tidepool_gpu_bridge.py receives no GPU results
                → TidePool results zone only receives Coral TPU jobs
                    → BEA_Inference cannot unify GPU + Coral routing
```

Fix the crash → everything downstream unblocks automatically.

> **Phase 1 is complete.** The patched build was compiled and validated on ROCm 7.1
> (86.87 prompt t/s, 110.17 eval t/s via llama-server; 108.75 t/s via Ollama).
> The `kv_cache_alloc_test.py` stream sync tests all pass. GPU is confirmed active.

---

## Architecture: How They Connect

```
BEA_Amplify (validation layer)
        │
        ▼
BEA_Inference router
        │
        ├── GPU route (ROCm · gfx1100 Windows) ─────────────────────┐
        │     llama.cpp (patched ggml-hip.dll)                       │
        │     llama-server → /v1/chat/completions                    │
        │     latency: ~1–3s first token                             │
        │                                               TidePoolGPUBridge
        │                                               submit_gpu_job()
        │                                               complete_gpu_job()
        │                                                             │
        └── Coral TPU route ────────────────────────────────────────-┤
              TidePoolInferenceQueue                                  │
              /bea_tidepool/queue/job_<uuid>.bin                     │
              Coral classifies / infers                               │
              TidePoolResultsManager                                  │
                                                                      ▼
                                           /bea_tidepool/results/job_<uuid>.result
                                                                      │
                                                           BEA_Pulse notifies
                                                           tidepool.job_complete
                                                           source_type: GPU | Coral
                                                                      │
                                                                      ▼
                                                         Requesting pillar picks up result

        └── CPU fallback (BEAOllama CPU mode)
              OLLAMA_LLM_LIBRARY=cpu · last resort only
```

Both GPU and Coral results land in the same TidePool results zone. BEA_Inference
treats them identically downstream — the only difference is `source_type` in the
BEA_Pulse payload.

---

## Phase 1 — Fix the GPU (BEATEK_ROCm)

**Repo:** `Beat-k/BEATEK_ROCm`
**Blocker:** Yes — nothing in Phase 2 or 3 is possible until this is done.

---

### Step 1.1 — Confirm Prerequisites

```powershell
# CMake 3.28+
cmake --version

# Visual Studio 2022 + MSVC v143 required

# ROCm 6.x for Windows
# Download: https://rocm.docs.amd.com/en/latest/deploy/windows/

# Confirm GPU is visible to ROCm
hipinfo
# Expected: Device 0: AMD Radeon RX 7900 GRE, gfx1100
```

---

### Step 1.2 — Clone llama.cpp and Apply Both Patches

```powershell
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Patch 1 — KV cache stream sync fix (core crash fix)
git apply path\to\BEATEK_ROCm\patches\ggml_hip_kv_alloc.patch

# Patch 2 — Flash Attention safety gate for gfx1100 Windows
git apply path\to\BEATEK_ROCm\patches\flash_attention_gfx1100.patch

# Confirm both applied cleanly
git diff --stat
# Expected: ggml/src/ggml-cuda/ggml-cuda.cu and fattn.cu modified
```

**What the patches do:**

| Patch | What It Fixes |
|---|---|
| `ggml_hip_kv_alloc.patch` | Inserts `hipDeviceSynchronize()` + `hipStreamSynchronize()` after KV cache alloc. Commits device memory to the compute stream before first use. Fixes the exit code 2 crash. |
| `flash_attention_gfx1100.patch` | Gates `GGML_OP_FLASH_ATTN_EXT` off on gfx1100 Windows. Forces SDPA fallback path. Fixes secondary FA memory layout fault. |

Both patches are required. They are independent and additive.

---

### Step 1.3 — Build with ROCm for gfx1100

```powershell
$env:HIP_PATH = "C:\Program Files\AMD\ROCm\7.1"

cmake -B build `
  -DGGML_HIP=ON `
  -DAMDGPU_TARGETS=gfx1100 `
  -DGGML_HIP_ROCM=ON `
  -DGGML_CUDA=OFF `
  -DGGML_DIRECTML=OFF `
  -DCMAKE_BUILD_TYPE=Release `
  -DCMAKE_PREFIX_PATH="$env:HIP_PATH" `
  -DCMAKE_C_COMPILER="$env:HIP_PATH\bin\clang.exe" `
  -DCMAKE_CXX_COMPILER="$env:HIP_PATH\bin\clang++.exe" `
  -G Ninja

cmake --build build --config Release -j8
```

> HIP compilation takes 15–30 minutes. `-j8` is recommended.

Output:
```
build\bin\Release\llama-server.exe
build\bin\Release\ggml-hip.dll     ← patched DLL
```

---

### Step 1.4 — Run kv_cache_alloc_test.py (No Model Needed)

Hits HIP directly. Confirms the stream affinity fix is working before loading a model.

```powershell
python path\to\BEATEK_ROCm\tests\kv_cache_alloc_test.py
# PASS = patch is working at the HIP level
# FAIL = stream affinity issue still present — recheck patch application
```

---

### Step 1.5 — Start llama-server and Run gfx1100_inference_test.py

```powershell
# Terminal 1 — start the patched server
.\build\bin\Release\llama-server.exe `
  --model path\to\model.gguf `
  --host 0.0.0.0 --port 8080 `
  -ngl 99 --no-flash-attn

# Terminal 2 — run end-to-end validation
python path\to\BEATEK_ROCm\tests\gfx1100_inference_test.py --endpoint http://localhost:8080
```

Expected:
```
✅ [PASS] Server health
✅ [PASS] Inference completes without crash
✅ [PASS] First-token latency ≤ 10s   ← GPU signal
✅ [PASS] Backend metadata
✅ [PASS] Stability (3 requests)
✅ ALL TESTS PASSED — GPU inference on gfx1100 is working
```

Latency > 10s means CPU fallback. Confirm `-ngl 99` is set and `ggml-hip.dll` is
the patched build, not Ollama's original bundle.

---

### Step 1.6 — Replace Ollama's Bundled ggml-hip.dll

```powershell
# Back up original
Copy-Item `
  "$env:LOCALAPPDATA\Programs\Ollama\lib\ollama\rocm\ggml-hip.dll" `
  "$env:LOCALAPPDATA\Programs\Ollama\lib\ollama\rocm\ggml-hip.dll.bak"

# Install patched version
Copy-Item `
  "build\bin\Release\ggml-hip.dll" `
  "$env:LOCALAPPDATA\Programs\Ollama\lib\ollama\rocm\ggml-hip.dll"

# Restart Ollama and confirm
ollama run mistral:7b "Hello"
# Expected: response, no exit code 2
```

---

### Step 1.7 — Confirm GPU in BEA_Inference

Check BEA_Amplify logs for `source_type: GPU`. First-token latency target is 1–3s.
If still showing CPU, confirm `OLLAMA_LLM_LIBRARY` is not set to `cpu`.

---

## Phase 2 — Connect GPU Results to TidePool (BEA_TidePool)

**Repo:** `Beat-k/BEA_TidePool`
**Prerequisite:** Phase 1 complete. GPU inference confirmed passing.

---

### Step 2.1 — Enable the GPU Bridge

```powershell
# Windows
$env:BEA_TIDEPOOL_GPU_BRIDGE_ENABLED   = "true"
$env:BEA_TIDEPOOL_GPU_INFERENCE_DEVICE = "gfx1100"
```

```bash
# Linux / BEA_Lace_OS
export BEA_TIDEPOOL_GPU_BRIDGE_ENABLED=true
export BEA_TIDEPOOL_GPU_INFERENCE_DEVICE=gfx1100
```

---

### Step 2.2 — Wire BEA_Amplify to the Bridge

```python
from bea_tidepool import (
    TidePoolZoneManager,
    TidePoolInferenceQueue,
    TidePoolResultsManager,
    TidePoolGPUBridge,
)

# --- One-time setup at boot ---
zone_mgr    = TidePoolZoneManager()
queue       = TidePoolInferenceQueue(zone_mgr, pulse_publish=bea_pulse.publish)
results_mgr = TidePoolResultsManager(zone_mgr, pulse_publish=bea_pulse.publish)
gpu_bridge  = TidePoolGPUBridge(
    zone_manager    = zone_mgr,
    results_manager = results_mgr,
    inference_queue = queue,
    pulse_publish   = bea_pulse.publish,
)

# --- Per inference request ---
import time, json

# 1. Stage the job in TidePool queue
job = gpu_bridge.submit_gpu_job(
    input_data    = json.dumps({"prompt": user_prompt}).encode(),
    role_id       = "llm_generation",
    source_pillar = "bea_amplify",
)

# 2. Run GPU inference
t0 = time.monotonic()
response  = call_llama_server(user_prompt)   # your existing call
latency_s = time.monotonic() - t0

# 3. Stage result in TidePool results zone
gpu_bridge.complete_gpu_job(
    job_id        = job.job_id,
    result_data   = json.dumps(response).encode(),
    role_id       = "llm_generation",
    source_pillar = "bea_amplify",
    latency_s     = latency_s,
)

# 4. Read and acknowledge
data = results_mgr.read_result(job.job_id)
results_mgr.acknowledge(job.job_id)
```

---

### Step 2.3 — Confirm source_type: GPU in BEA_Pulse

Watch for `tidepool.gpu_job_complete`. Payload must include:

```json
{
  "job_id":        "a3f1...",
  "role_id":       "llm_generation",
  "source_pillar": "bea_amplify",
  "result_bytes":  1842,
  "latency_s":     1.83,
  "backend":       "ROCm",
  "device":        "gfx1100",
  "source_type":   "GPU"
}
```

---

### Step 2.4 — Run test_gpu_bridge.py

```bash
cd BEA_TidePool
python -m pytest tests/test_gpu_bridge.py -v
```

All 7 tests must pass:

```
PASS  test_submit_gpu_job_stages_to_queue
PASS  test_submit_gpu_job_emits_pulse_event
PASS  test_complete_gpu_job_writes_result
PASS  test_complete_gpu_job_emits_pulse_event
PASS  test_fail_gpu_job_emits_failed_event
PASS  test_gpu_queue_depth
PASS  test_full_pipeline
```

---

## Phase 3 — BEA_Inference Unified Routing

### Routing Decision

```python
def route_inference_job(job):
    if gpu_rocm_available() and not job.requires_tpu_classify:
        return "GPU"        # LLM generation · ~1–3s · full quality
    elif coral_tpu_available() and job.is_classifiable:
        return "Coral"      # Intent / signal classify · ~4ms · 2W
    else:
        return "CPU"        # Last resort · ~4–60s
```

### Fallback Chain

```
GPU (ROCm · gfx1100)            ← primary
    ↓ unavailable
LM Studio (DirectML)            ← interim workaround
    ↓ unavailable
BEAOllama CPU mode              ← always available
```

Once Ollama ships a corrected `ggml-hip.dll` (post llama.cpp PR), LM Studio
is no longer needed in the critical path.

---

## BEA_Pulse Event Map

| Event | Source | Priority | Key Fields |
|---|---|---|---|
| `tidepool.gpu_job_queued` | GPUBridge | NORMAL | `job_id`, `backend: "ROCm"`, `device: "gfx1100"`, `bytes` |
| `tidepool.job_queued` | InferenceQueue | NORMAL | `job_id`, `source_pillar`, `queue_depth` |
| `tidepool.job_started` | InferenceQueue | NORMAL | `job_id`, `role_id` |
| `tidepool.gpu_job_complete` | GPUBridge | HIGH | `job_id`, `latency_s`, `source_type: "GPU"`, `result_bytes` |
| `tidepool.job_complete` | ResultsManager | HIGH | `job_id`, `source_pillar`, `result_bytes` |
| `tidepool.gpu_job_failed` | GPUBridge | CRITICAL | `job_id`, `error`, `backend: "ROCm"` |
| `tidepool.job_failed` | InferenceQueue | CRITICAL | `job_id`, `error` |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `BEA_TIDEPOOL_GPU_BRIDGE_ENABLED` | `true` | Enable GPU → TidePool bridge |
| `BEA_TIDEPOOL_GPU_INFERENCE_DEVICE` | `gfx1100` | GPU arch name for BEA_Pulse payloads |
| `BEA_TIDEPOOL_MOUNT_PATH` | `/bea_tidepool` | TidePool NVMe mount point |
| `BEA_TIDEPOOL_EMBER_STAGING_ENABLED` | `true` | EMBER anticipatory pre-staging |
| `BEA_TIDEPOOL_CHECKSUM_VERIFY` | `true` | SHA-256 verify on result reads |
| `BEA_TIDEPOOL_QUEUE_DEPTH_WARN` | `8` | Queue depth backlog warning threshold |
| `OLLAMA_LLM_LIBRARY` | _(unset)_ | Set to `cpu` to force CPU fallback |
| `HIP_PATH` | `C:\Program Files\AMD\ROCm\7.1` | ROCm install path for Windows build |

---

## Status Tracker

| Task | Repo | Status |
|---|---|---|
| Crash documented with addresses | BEATEK_ROCm | ✅ |
| Environment snapshot captured | BEATEK_ROCm | ✅ |
| Reproduction steps written | BEATEK_ROCm | ✅ |
| Root cause isolated in ggml-hip | BEATEK_ROCm | ✅ |
| `ggml_hip_kv_alloc.patch` written | BEATEK_ROCm | ✅ |
| `flash_attention_gfx1100.patch` written | BEATEK_ROCm | ✅ |
| `kv_cache_alloc_test.py` written | BEATEK_ROCm | ✅ |
| `gfx1100_inference_test.py` written | BEATEK_ROCm | ✅ |
| Build docs written | BEATEK_ROCm | ✅ |
| `tidepool_gpu_bridge.py` written | BEA_TidePool | ✅ |
| `tests/test_gpu_bridge.py` written | BEA_TidePool | ✅ |
| This integration README | BEA_TidePool | ✅ |
| Linux reference build confirmed | BEATEK_ROCm | ✅ |
| **Patched Windows build compiled** | BEATEK_ROCm | ✅ ROCm 7.1 · VS 2026 · CMake 4.3.3 |
| `kv_cache_alloc_test.py` passing | BEATEK_ROCm | ✅ All stream sync tests pass |
| `gfx1100_inference_test.py` passing | BEATEK_ROCm | ✅ 108 t/s confirmed |
| Ollama DLL replaced and confirmed | BEATEK_ROCm | ✅ 108.75 t/s via Ollama end-to-end |
| GPU confirmed in BEA_Inference | BEA_Aura | 🟡 **← Phase 2 entry point** |
| BEA_Amplify wired to gpu_bridge | BEA_TidePool | 🔴 **← Next step** |
| `tidepool.gpu_job_complete` confirmed | BEA_TidePool | 🔴 Pending Phase 2 |
| `test_gpu_bridge.py` all passing | BEA_TidePool | 🔴 Pending Phase 2 |
| BEA_Inference unified routing active | BEA_Aura | 🔴 Pending Phase 2 |
| llama.cpp PR submitted upstream | BEATEK_ROCm | 🟡 PR description ready — submission pending |
| Ollama issue filed with root cause | BEATEK_ROCm | 🟡 Ready to post |

---

## Interim Workaround

Phase 1 is complete. The patched ROCm build is validated at 108 t/s on gfx1100
Windows. LM Studio (DirectML) is no longer needed in the primary path.

DirectML remains available as a fallback if the ROCm path is unavailable:
[`builds/build_windows_directml.md`](https://github.com/Beat-k/BEATEK_ROCm/blob/master/builds/build_windows_directml.md)

The active critical path is now Phase 2: wiring BEA_Amplify to `tidepool_gpu_bridge.py`.

---

## References

- [Beat-k/BEATEK_ROCm](https://github.com/Beat-k/BEATEK_ROCm)
- [Beat-k/BEA_TidePool](https://github.com/Beat-k/BEA_TidePool)
- [llama.cpp — ggml-hip backend](https://github.com/ggerganov/llama.cpp/tree/master/ggml/src/ggml-cuda)
- [Ollama Issues — ROCm gfx1100 Windows](https://github.com/ollama/ollama/issues)
- [AMD ROCm Documentation](https://rocm.docs.amd.com/)
- [ROCm for Windows — Install Guide](https://rocm.docs.amd.com/en/latest/deploy/windows/)
- [gfx1100 — RDNA3 Architecture](https://gpuopen.com/rdna3/)

---

*BEATEK Holdings, LLC · Jeremy F. Jackson · Dallas, Texas · © 2026*
*Patent Pending · jeremy.jackson0@beatek.io*

*BEA_TidePool — The VRAM of the Coral. The water the reef runs on.*
*BEATEK_ROCm — Fix the crash. Free the GPU. Let the reef run hot.*