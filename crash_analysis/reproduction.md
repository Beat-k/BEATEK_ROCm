⟦TCS⟧
DOMAIN:       beatek.project
DOC_TYPE:     crash.reproduction
PLATFORM:     BEATEK_ROCm
VERSION:      2026.06.01
AUTHORITY:    draft
COSIGN:       Jeremy F. Jackson (Jaxxon) · BEATEK Holdings LLC
TRIBUNAL:     PENDING
STAMP_ID:     TCS-2026-0601-BEATEK-ROCM-REPRO-001
⟦/TCS⟧

# Reproduction Steps — gfx1100 Windows ROCm Crash

**Crash type:** Access violation (0xc0000005) in ggml-hip.dll
**Reproducibility:** 100% — deterministic crash address, every model, every run
**Time to reproduce:** ~2 minutes from clean Ollama install

---

## Prerequisites

- Windows 11 (build 22000+)
- AMD Radeon RX 7900 GRE (gfx1100) or any RDNA3 card using gfx1100
- AMD Adrenalin driver 60033.23 or later
- No custom environment variables set (clean test)

---

## Step 1 — Install Ollama 0.24.0

Download and install from the Ollama releases page:
```
https://github.com/ollama/ollama/releases/tag/v0.24.0
```

Install to default location:
```
C:\Users\<user>\AppData\Local\Programs\Ollama\
```

Do **not** set any environment variables before this step.

---

## Step 2 — Verify GPU Is Detected

Start Ollama service (or let installer start it), then run:

```powershell
ollama run mistral:7b "hello"
```

In the Ollama server log (viewable via `ollama serve` in terminal), you should
see:

```
library=ROCm compute=gfx1100 name=ROCm0
description="AMD Radeon RX 7900 GRE"
total="16.0 GiB" available="14.9 GiB"
```

GPU is correctly detected. ✅

---

## Step 3 — Pull a Test Model

```powershell
ollama pull mistral:7b
```

Wait for full download (~4 GB). Any 7B or 8B model works — the crash is
not model-specific.

---

## Step 4 — Trigger the Crash

Run inference:

```powershell
ollama run mistral:7b "What is 2 + 2?"
```

**Expected crash output:**

```
load_tensors: offloaded 33/33 layers to GPU
llama_kv_cache:      ROCm0 KV buffer size =   512.00 MiB
llama_context: Flash Attention was auto, set to enabled
Exception 0xc0000005 0x0 0x0 0x7fffb68751fe
llama runner process has terminated with exit code 2
Error: exit status 2
```

The crash is deterministic. Same address, same behavior, every run.

---

## Step 5 — Confirm CPU Fallback Works

```powershell
$env:OLLAMA_LLM_LIBRARY = "cpu"
ollama run mistral:7b "What is 2 + 2?"
```

Inference completes correctly, slowly (~4–60s first token). This confirms:
- The model loads correctly
- The failure is in ggml-hip.dll, not the model or the Ollama runtime

---

## Step 6 — Confirm Flash Attention Flag Does Not Fix It

```powershell
$env:OLLAMA_FLASH_ATTENTION = "false"
Remove-Item Env:OLLAMA_LLM_LIBRARY  # restore GPU mode
ollama run mistral:7b "What is 2 + 2?"
```

Still crashes — the crash address shifts slightly between runs but the
access violation pattern persists. Flash Attention disable alone is not
the fix.

---

## Crash Classification

| Property | Value |
|----------|-------|
| Exception code | 0xc0000005 (ACCESS_VIOLATION) |
| Access type | Read from invalid address 0x0 |
| Crash address | 0x7fffb68751fe (deterministic) |
| Module at crash | ggml-hip.dll |
| Call stack top | llama_init_from_model → NewContextWithModel |
| Trigger | KV cache + context initialization after tensor load |
| Reproducible | ✅ 100% |

---

## Notes for Upstream Report

- GPU detection succeeds (not a driver/ROCm version issue)
- All 33 layers offload correctly (not a VRAM size issue)
- KV cache buffer allocation on GPU succeeds (log shows 512 MiB allocated)
- Crash occurs **after** KV cache, **inside** context init (`llama_init_from_model`)
- Linux with same GPU and same model: no crash (confirms Windows ROCm path)
- All 7B/8B models tested crash identically

---

*BEATEK Holdings, LLC · Jeremy F. Jackson · June 2026*
