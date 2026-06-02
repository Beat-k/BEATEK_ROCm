# Ollama Issue #12045 Comment — Root Cause Analysis + Fix

---

**Root cause identified and fix validated on gfx1100 Windows ROCm.**

Hardware: AMD Radeon RX 7900 GRE · gfx1100 · Windows 11 · ROCm 7.1

---

## What's happening

Two independent bugs in `ggml-hip` compound on gfx1100 Windows:

**1. KV cache stream affinity**

On Windows ROCm, the driver enforces stream affinity — device memory allocated
on the default HIP stream is not guaranteed visible on a separately created
compute stream without an explicit sync barrier. `ggml_hip_context_init_device`
allocates the KV cache buffer on the default stream, then immediately accesses
it via a non-default compute stream. On Linux, unified VM tolerates this. On
Windows the pointer is invalid at first access — access violation at the fixed
address you see in the crash log.

**2. Flash Attention memory layout**

FA on gfx1100 Windows creates split K/V view tensors that trigger a secondary
fault in the same init path, even after the stream sync fix. Linux is unaffected.

---

## The fix

35 lines across two files in llama.cpp:

- `ggml/src/ggml-cuda/common.cuh` — add `hipDeviceSynchronize()` +
  `hipStreamSynchronize(stream)` after KV cache allocation, before the compute
  stream touches the buffer
- `ggml/src/ggml-cuda/ggml-cuda.cu` — gate `GGML_OP_FLASH_ATTN_EXT` off for
  gfx1100 on Windows, falling back to standard SDPA

Both changes are gated on `#if defined(_WIN32)` and arch prefix check — no
impact on Linux or other architectures.

---

## Validation

Before: `exit code 2` every run, deterministic crash address  
After:

```
prompt eval rate: 108.75 tokens/s
total duration:   1.34s
```

Tested with mistral:7b, llama3.1:8b, qwen2.5:7b — all run without crashing.

---

## For users hitting this now

You can replace Ollama's bundled `ggml-hip.dll` with a patched build manually:

1. Build llama.cpp from source on Windows with ROCm following
   `builds/build_windows_rocm.md` in the BEATEK_ROCm repo (link below)
2. Copy `build\bin\ggml-hip.dll` to:
   - `C:\Users\<you>\AppData\Local\Programs\Ollama\lib\ollama\rocm\ggml-hip.dll`
   - `C:\Users\<you>\AppData\Local\Programs\Ollama\lib\ollama\rocm\lib\ollama\rocm\ggml-hip.dll`
3. Restart Ollama

Or wait for the llama.cpp PR to land and Ollama to ship an updated build.

---

## References

- BEATEK_ROCm project: https://github.com/beatek/BEATEK_ROCm
- llama.cpp PR: *(link once filed)*
- Patch: `patches/beatek_rocm_HEAD.patch`
- HIP isolation test: `tests/kv_cache_alloc_test.py`

*— Jeremy F. Jackson · BEATEK Holdings, LLC*
