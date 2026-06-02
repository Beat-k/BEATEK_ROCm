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

## Contribution Targets

| Project | Type | Target |
|---------|------|--------|
| llama.cpp | Pull Request | KV cache fix for gfx1100 Windows ROCm |
| Ollama | Issue comment | Root cause analysis + patch reference |
| ROCm docs | Documentation | gfx1100 Windows known issues |

---

## Current Workaround

While the fix is being developed, GPU inference on Windows uses DirectML
via LM Studio. This bypasses ROCm entirely and works correctly on gfx1100.

Long term: Linux ROCm (BEA_Lace_OS) will own GPU inference when the
BEA Aura Console hardware provides proper PCIe topology.

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
