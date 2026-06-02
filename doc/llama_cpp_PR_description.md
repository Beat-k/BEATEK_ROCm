# ggml-hip: fix KV cache crash and disable Flash Attention on gfx1100 Windows ROCm

## Summary

Fixes a deterministic crash (`exit code 2`, `Exception 0xc0000005`) during
`llama_init_from_model` on AMD Radeon RX 7900 series (gfx1100) under Windows
ROCm. GPU is correctly detected and layers offload successfully, but inference
crashes at KV cache initialization every time.

Confirmed working on Linux with the same GPU and same model. Windows-specific.
Regression present since approximately Ollama 0.11.5. Related: ollama/ollama#12045

---

## Root Cause

Two independent issues compound on gfx1100 Windows ROCm:

### 1. KV cache stream affinity (`common.cuh`)

On Windows ROCm, the driver enforces stream affinity — device memory allocated
on the default stream is not guaranteed visible on a separately created compute
stream without an explicit synchronization barrier.

`ggml_hip_context_init_device` allocates the KV cache buffer via the pool
allocator (default stream), then immediately uses it via `ctx->stream` (a
non-default compute stream). On Linux, unified VM tolerates this. On Windows
the pointer is invalid at first access — hence the access violation at a fixed
address.

**Fix:** `hipDeviceSynchronize()` + `hipStreamSynchronize(stream)` after KV
cache and scratch buffer allocation, before the compute stream touches them.

### 2. Flash Attention memory layout on gfx1100 Windows (`ggml-cuda.cu`)

Flash Attention creates split K/V view tensors backed by offsets into the KV
buffer. On gfx1100 Windows ROCm this layout triggers a secondary fault even
after the stream sync fix is applied. The issue does not reproduce on Linux.

**Fix:** Return `false` from `ggml_cuda_supports_op` for
`GGML_OP_FLASH_ATTN_EXT` when running on gfx1100 under Windows HIP. llama.cpp
falls back to standard SDPA automatically.

---

## Changes

```
ggml/src/ggml-cuda/common.cuh   | 19 +++++++++++++++++++
ggml/src/ggml-cuda/ggml-cuda.cu | 16 ++++++++++++++++
2 files changed, 35 insertions(+)
```

Both changes are gated on `#if defined(_WIN32)` and `gcnArchName` prefix check
— no impact on Linux, no impact on other GPU architectures.

---

## Validation

**Hardware:** AMD Radeon RX 7900 GRE · gfx1100 · Windows 11  
**ROCm:** 7.1  
**Build:** clang 21 / Ninja / VS 2026

Before patch:
```
offloaded 33/33 layers to GPU
Exception 0xc0000005 0x0 0x0 0x7fffb68751fe
llama runner process has terminated with exit code 2
```

After patch:
```
- ROCm0 : AMD Radeon RX 7900 GRE (16368 MiB, 16218 MiB free)
- prompt eval: 86.87 tokens/s
- eval:        110.17 tokens/s
- total time:  245.94 ms / 22 tokens
```

Ollama end-to-end:
```
prompt eval rate: 108.75 tokens/s  ← GPU confirmed, was crashing before
total duration:   1.34s
```

HIP allocation isolation test (stream sync pattern):
```
[PASS] KV buffer allocated at 0x304000000
[PASS] hipDeviceSynchronize() OK
[PASS] Memcpy to KV buffer via compute stream succeeded
```

---

## Notes

- The two fixes are independent and additive. Either alone is insufficient.
- The FA gate is intentionally conservative — gfx1100 Windows only. Other
  architectures and Linux are unaffected.
- A HIP-level isolation test (`tests/kv_cache_alloc_test.py`) reproduces the
  stream affinity pattern without requiring a full model load.
- ROCm 7.1 ships `__clang_hip_cmath.h` with an imbalanced `#if` block (line 109)
  that requires a one-line patch before building against VS 2026. This is a
  ROCm header bug, not a llama.cpp issue, but worth noting for Windows builders.
