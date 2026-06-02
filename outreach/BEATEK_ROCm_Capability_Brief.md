# BEATEK Holdings, LLC
## ROCm gfx1100 Windows Inference — Validated Fix & Integration Consulting

**Contact:** Jeremy F. Jackson · jeremy.jackson0@beatek.io · Dallas, Texas
**Date:** June 2026 · Patent Pending

---

## The Problem

Every AMD Radeon RX 7900 series user (gfx1100) running Ollama or llama.cpp
on Windows is blocked by a deterministic crash at inference startup:

```
offloaded 33/33 layers to GPU
Exception 0xc0000005 0x0 0x0 0x7fffb68751fe
llama runner process has terminated with exit code 2
```

The GPU is detected. Layers offload correctly. Inference never starts.
Present since Ollama 0.11.5. Unresolved as of June 2026.
The same hardware runs ROCm inference correctly on Linux.

---

## What BEATEK Found

Two independent root causes compound on gfx1100 Windows ROCm:

**1. KV Cache Stream Affinity**
The Windows ROCm 6.x/7.x driver enforces stream affinity on device allocations.
`ggml-hip` allocates the KV cache buffer on the default HIP stream, then
immediately accesses it on a separately created compute stream — without a sync
barrier. On Linux, unified VM tolerates this. On Windows the pointer is invalid
at first access. Result: access violation at a fixed, deterministic address.

**2. Flash Attention Memory Layout**
Flash Attention on gfx1100 Windows creates split K/V view tensors with an
unresolved memory layout issue specific to this architecture on Windows ROCm.
Triggers a secondary fault independent of the stream affinity issue.

---

## What BEATEK Built

A validated 35-line patch across two files in llama.cpp that resolves
both root causes completely:

```
ggml/src/ggml-cuda/common.cuh   | 19 lines — stream sync fix
ggml/src/ggml-cuda/ggml-cuda.cu | 16 lines — FA gate for gfx1100 Windows
```

Both changes are gated on `#if defined(_WIN32)` and `gcnArchName` prefix check.
No impact on Linux. No impact on other GPU architectures.

Also documented: ROCm 7.1 + VS 2026 header conflicts (two files in
`clang/21/include/`) that block any Windows ROCm build against the current
MSVC STL — not previously documented anywhere.

---

## Validated Results

**Hardware:** AMD Radeon RX 7900 GRE · gfx1100 · Windows 11 · ROCm 7.1

| Metric | Before Patch | After Patch |
|---|---|---|
| Inference startup | Exit code 2 · crash | ✅ Clean |
| Prompt eval | N/A | 86.87 tokens/s |
| Token generation | N/A | 110.17 tokens/s |
| Ollama end-to-end | Crash | ✅ 108.75 tokens/s · 1.34s |
| HIP stream sync test | N/A | ✅ All tests passing |

---

## What BEATEK Is Offering

**Consulting engagements — fixed scope, validated delivery:**

| Engagement | Scope | Deliverable |
|---|---|---|
| **Fix Integration** | Apply and integrate patch into ROCm Windows stack or Ollama bundle | Merged fix + validation report |
| **Build Environment** | Full Windows ROCm 7.x + VS 2026 build documentation | Reproducible build guide + header patch docs |
| **Test Suite** | HIP-level isolation tests + end-to-end inference validation | Automated test suite for gfx1100 Windows |
| **Ongoing Support** | Windows ROCm gfx1100 maintenance retainer | Monthly support + regression testing |

---

## About BEATEK

BEATEK Holdings, LLC is a Dallas-based compute platform engineering firm
building BEA_Aura — a heterogeneous inference platform combining AMD GPU,
Coral Edge TPU, and multi-OS orchestration. BEATEK_ROCm was developed as a
production requirement: the RX 7900 GRE is the primary inference GPU in the
BEA_Aura stack. We fixed this because we needed it to work. The fix is
validated in production.

---

**Jeremy F. Jackson** · Founder, BEATEK Holdings, LLC
jeremy.jackson0@beatek.io · Dallas, Texas · © 2026
Patent Pending · beatek-rocm-validated-2026-06-02
