⟦TCS⟧
DOMAIN:       beatek.project
DOC_TYPE:     crash.environment
PLATFORM:     BEATEK_ROCm
VERSION:      2026.06.01
AUTHORITY:    draft
COSIGN:       Jeremy F. Jackson (Jaxxon) · BEATEK Holdings LLC
TRIBUNAL:     PENDING
STAMP_ID:     TCS-2026-0601-BEATEK-ROCM-ENV-001
⟦/TCS⟧

# Environment Snapshot — gfx1100 Windows ROCm Crash

**Captured:** May 30–31, 2026
**Purpose:** Exact environment for crash reproduction and upstream bug report

---

## Host System

| Component | Value |
|-----------|-------|
| OS | Windows 11 Pro |
| OS Build | 26100.x |
| Architecture | x86_64 |
| RAM | 64 GB DDR5 |
| CPU | AMD Ryzen 9 7950X |
| Storage | PCIe Gen 5 NVMe |

---

## GPU

| Component | Value |
|-----------|-------|
| GPU Model | AMD Radeon RX 7900 GRE |
| GPU Architecture | RDNA3 · Navi 31 |
| gfx Target | gfx1100 |
| VRAM | 16 GiB GDDR6 |
| VRAM Available at crash | 14.9 GiB (after driver reservation) |
| Driver Version | 60033.23 |
| Driver Package | Adrenalin Edition |
| ROCm runtime | Bundled in Ollama (ROCm 6.x) |

---

## Software

| Component | Version |
|-----------|---------|
| Ollama | 0.24.0 |
| llama.cpp | Ollama-bundled (commit embedded in binary) |
| ggml-hip.dll | 512,912,264 bytes (SHA256 pending) |
| Python | 3.11.x |
| CUDA toolkit | N/A — ROCm only |

---

## ggml-hip.dll Location

```
C:\Users\jjack\AppData\Local\Programs\Ollama\lib\ollama\rocm\ggml-hip.dll
```

File size: 512,912,264 bytes
Loaded at runtime via Ollama's dynamic backend loader.

---

## Models Tested (All Crash)

| Model | Format | Layers | Result |
|-------|--------|--------|--------|
| mistral:7b | GGUF Q4_K_M | 33 | ❌ Exit code 2 |
| llama3.1:8b | GGUF Q4_K_M | 33 | ❌ Exit code 2 |
| qwen2.5:7b | GGUF Q4_K_M | 33 | ❌ Exit code 2 |

All models crash at the same code path (`llama_init_from_model`), confirming
the issue is not model-specific.

---

## Environment Variables at Time of Crash

```
OLLAMA_LLM_LIBRARY=        (unset — auto-selects ROCm)
OLLAMA_FLASH_ATTENTION=    (unset — auto-enabled by Ollama 0.11.5+)
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
```

### With CPU Workaround (Working)

```
OLLAMA_LLM_LIBRARY=cpu
```

---

## Ollama Server Log at Time of Crash

```
time=2026-05-30T... level=INFO source=gpu.go msg="inference compute"
  id=GPU-xxxxxxxx library=ROCm variant="" compute=gfx1100
  driver=60033.23 name=ROCm0 total="16.0 GiB" available="14.9 GiB"

load_backend: loaded ROCm backend from
  C:\Users\jjack\AppData\Local\Programs\Ollama\lib\ollama\rocm\ggml-hip.dll

ggml_cuda_init: found 1 ROCm devices:
  Device 0: AMD Radeon RX 7900 GRE, gfx1100 (0x1100),
  VMM: no, Wave Size: 32, ID: 0

load_tensors: offloading 32 repeating layers to GPU
load_tensors: offloading output layer to GPU
load_tensors: offloaded 33/33 layers to GPU
load_tensors:   CPU_Mapped model buffer size =    72.00 MiB
load_tensors:        ROCm0 model buffer size =  4097.52 MiB

llama_kv_cache:      ROCm0 KV buffer size =   512.00 MiB
llama_context: Flash Attention was auto, set to enabled

Exception 0xc0000005 0x0 0x0 0x7fffb68751fe

llama runner process has terminated with exit code 2
```

---

## Linux Reference (Working — Same GPU)

| Component | Value |
|-----------|-------|
| OS | BEA_Lace_OS (Debian-based) |
| Kernel | 6.8+ with AMDGPU |
| ROCm | 6.1.x (native install) |
| llama.cpp | Built from source · master branch |
| gfx target | gfx1100 |
| Result | ✅ Inference runs correctly |

The same physical GPU, passed through to Linux, runs llama.cpp with ROCm
without this crash. This confirms: hardware is not the issue.

---

*BEATEK Holdings, LLC · Jeremy F. Jackson · June 2026*
