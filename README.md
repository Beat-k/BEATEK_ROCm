⟦TCS⟧
DOMAIN:       beatek.project
DOC_TYPE:     project.readme
PLATFORM:     BEATEK_ROCm
VERSION:      2026.06.01
AUTHORITY:    draft
COSIGN:       Jeremy F. Jackson (Jaxxon) · BEATEK Holdings LLC
TRIBUNAL:     PENDING
STAMP_ID:     TCS-2026-0601-BEATEK-ROCM-README-001
⟦/TCS⟧

# BEATEK_ROCm
**gfx1100 Windows Inference Fix · Open Source Contribution Project**

*BEATEK Holdings, LLC · Jeremy F. Jackson · June 2026*

---

## What This Is

BEATEK_ROCm is a focused open source contribution project targeting a
confirmed regression in llama.cpp and Ollama that causes GPU inference to
crash on AMD Radeon RX 7900 series (gfx1100) under Windows 11.

This project documents the crash precisely, analyzes the root cause, and
develops a fix suitable for upstream contribution to llama.cpp and Ollama.

---

## The Bug

**Affected hardware:** AMD Radeon RX 7900 GRE · gfx1100 · Windows 11
**Affected software:** Ollama 0.11.5+ on Windows · llama.cpp with ROCm
**Regression since:** Ollama 0.11.5 (confirmed working in 0.11.4)
**Ollama issue:** https://github.com/ollama/ollama/issues/12045

### Symptom

GPU is correctly detected and model layers offload successfully:
```
library=ROCm compute=gfx1100 name=ROCm0
description="AMD Radeon RX 7900 GRE"
total="16.0 GiB" available="14.9 GiB"
offloaded 33/33 layers to GPU
```

But inference crashes at context initialization:
```
Exception 0xc0000005 0x0 0x0 0x7fffb68751fe
llama runner process has terminated with exit code 2
```

### Root Cause (Working Theory)

The crash occurs inside `ggml-hip.dll` during `llama_init_from_model` when
the KV cache is being allocated on the GPU. The access violation at a fixed
address (`0x7fffb68751fe`) suggests a null or invalid pointer dereference
in the ROCm KV cache allocation path, specifically triggered by the
interaction between:

1. Flash Attention auto-enable (added in 0.11.5)
2. gfx1100 KV cache memory layout on Windows ROCm 6.x
3. The specific VRAM allocation pattern for the KV + compute buffers

The crash occurs even with `OLLAMA_FLASH_ATTENTION=false` in later testing,
which suggests the Flash Attention flag is not the sole trigger — the
underlying KV cache allocation code path was also changed in the same
release window.

---

## Environment (Confirmed Crash)

| Component | Version |
|-----------|---------|
| OS | Windows 11 |
| GPU | AMD Radeon RX 7900 GRE |
| GPU arch | gfx1100 (Navi 31) |
| Driver | 60033.23 |
| Ollama | 0.24.0 |
| ROCm | 6.x (bundled in Ollama) |
| llama.cpp | Ollama-bundled |
| Models tested | mistral:7b · llama3.1:8b · qwen2.5:7b |

All models crash at the same address. CPU mode works correctly for all models.

---

## Project Structure

```
BEATEK_ROCm/
├── README.md                          ← This file
├── crash_analysis/
│   ├── crash_log.txt                  ← Full stack trace from production
│   ├── environment.md                 ← Exact environment details
│   └── reproduction.md                ← Steps to reproduce
├── patches/
│   ├── ggml_hip_kv_alloc.patch        ← KV cache allocation fix
│   └── flash_attention_gfx1100.patch  ← FA gating for gfx1100 Windows
├── builds/
│   ├── build_windows_directml.md      ← Build llama.cpp with DirectML
│   ├── build_windows_rocm.md          ← Build llama.cpp with ROCm
│   └── build_linux_rocm.md            ← Build llama.cpp with ROCm on Linux
└── tests/
    ├── gfx1100_inference_test.py      ← Validates fix end to end
    └── kv_cache_alloc_test.py         ← Isolated KV cache allocation test
```

---

## How BEATEK_ROCm Works

### The Engineering Pipeline

BEATEK_ROCm is not just a bug report. It is a structured patch development
pipeline that goes from a production crash to an upstream-ready fix:

```
Production crash observed
          ↓
  1. CAPTURE — crash_analysis/
     • Raw crash output with exception address (crash_log.txt)
     • Exact environment snapshot: driver, OS, Ollama version (environment.md)
     • Step-by-step reproduction from a clean install (reproduction.md)
          ↓
  2. ISOLATE — understand what actually crashes
     • GPU detection ✓  — not a driver issue
     • Layer offload ✓  — not a VRAM issue
     • KV cache alloc ✓ — buffer allocation succeeds
     • crash inside llama_init_from_model, after KV cache, before first
       inference — pinpoints ggml-hip context init as the fault site
     • Linux same GPU: no crash — confirms Windows ROCm driver difference
          ↓
  3. ROOT CAUSE — HIP stream affinity on Windows ROCm 6.x
     • ggml-hip allocates KV buffer on default stream via pool allocator
     • Context init creates a separate compute stream (ctx->stream)
     • Pointer is immediately used on ctx->stream without a sync barrier
     • On Linux, ROCm unified VM tolerates cross-stream pointer use
     • On Windows ROCm 6.x, driver enforces stream affinity — pointer
       is invalid on the compute stream → ACCESS_VIOLATION 0xc0000005
     • FA split K/V views compound this: gfx1100 Windows has an additional
       memory layout issue in the FA code path
          ↓
  4. PATCH — patches/
     • ggml_hip_kv_alloc.patch
       Insert hipDeviceSynchronize() + hipStreamSynchronize(stream) after
       KV and scratch buffer allocation. Commits all allocations to the
       device before the compute stream accesses them.
     • flash_attention_gfx1100.patch
       Override ggml_hip_supports_op to return false for
       GGML_OP_FLASH_ATTN_EXT on gfx1100 Windows at runtime by checking
       prop.gcnArchName. llama.cpp auto-falls back to standard SDPA.
     The two patches are independent and additive. Both are applied.
          ↓
  5. BUILD — builds/
     • build_windows_rocm.md   ← apply patches, cmake ROCm, replace DLL
     • build_linux_rocm.md     ← reference build (no patches, for diff)
     • build_windows_directml.md ← interim workaround while ROCm is WIP
          ↓
  6. VALIDATE — tests/
     • kv_cache_alloc_test.py  — low-level HIP test
       Directly replicates the alloc → compute-stream → sync pattern
       from ggml-hip. Fails cleanly without the patch. No model needed.
     • gfx1100_inference_test.py — end-to-end API test
       Drives llama-server, checks inference completes, uses first-token
       latency as GPU signal (< 10s = GPU, > 20s = CPU fallback),
       runs 3 consecutive requests for stability.
          ↓
  7. UPSTREAM — contribution
     • llama.cpp PR with both patches
     • Ollama issue comment with root cause analysis + patch reference
     • ROCm docs gfx1100 Windows known issues section
```

### Why Two Patches, Not One

The KV alloc patch (`ggml_hip_kv_alloc.patch`) fixes the **stream affinity**
issue — the pointer is committed before use. This alone may resolve the crash
on some gfx1100 Windows configurations.

The Flash Attention gate (`flash_attention_gfx1100.patch`) fixes the **memory
layout** issue — FA creates split K/V view tensors with buffer offsets that
the Windows ROCm 6.x driver resolves differently on gfx1100 than on Linux.
This gate ensures llama.cpp never enters that code path on the affected target.

Disabling FA alone (via `OLLAMA_FLASH_ATTENTION=false`) does **not** fix the
crash — the KV allocation stream affinity issue exists independently of FA.
Both patches are required for a reliable fix.

### How the Linux Reference Build Helps

`build_linux_rocm.md` builds llama.cpp from source on BEA_Lace_OS with
`-DGGML_HIP=ON -DAMDGPU_TARGETS=gfx1100`. This build:
- Runs without the crash on the same physical GPU
- Gives a working reference binary to compare compile flags against
- Allows a direct diff of the Linux-built `libggml-hip.so` vs Ollama's
  Windows-bundled `ggml-hip.dll` to find additional build-time differences
- Becomes the primary inference path in BEA_Lace_OS when GPU passthrough
  is available

---

## Contribution Targets

| Project | Type | Target | Status |
|---------|------|--------|--------|
| llama.cpp | Pull Request | KV cache fix for gfx1100 Windows ROCm | 🟡 Patches written |
| Ollama | Issue comment | Root cause analysis + patch reference | 🟡 Analysis complete |
| ROCm docs | Documentation | gfx1100 Windows known issues | 🔴 Pending |

---

## Current Workaround

While the patched build is being compiled and tested, GPU inference on Windows
uses DirectML via LM Studio (`build_windows_directml.md`). This bypasses
ROCm entirely and works correctly on gfx1100 (~20–30 tok/s vs ~40+ tok/s
expected with ROCm).

Long term: Linux ROCm (BEA_Lace_OS) will own GPU inference when BEA Aura
Console hardware provides correct PCIe topology for passthrough.

---

## Relationship to BEA Stack

This project was born from building BEA_Aura_CDE_HV — a heterogeneous
compute platform using Coral Dual Edge TPU + AMD GPU + dedicated NVMe
inference bus across Linux and Windows. The gfx1100 ROCm crash was
encountered during production deployment and documented precisely.

Once fixed, the patch enables:
- BEA_Amplify to use the 7900 GRE natively without third-party wrappers
- BEA_Inference GPU route at full speed (~40 tok/s vs ~1 tok/s CPU)
- BEA_Lace_OS to run LLMs via ROCm on Linux when GPU is accessible

---

*BEATEK Holdings, LLC · Jeremy F. Jackson · © 2026*
*Patent Pending · jeremy.jackson0@beatek.io*
