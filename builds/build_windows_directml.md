⟦TCS⟧
DOMAIN:       beatek.project
DOC_TYPE:     build.instructions
PLATFORM:     BEATEK_ROCm
VERSION:      2026.06.01
AUTHORITY:    draft
COSIGN:       Jeremy F. Jackson (Jaxxon) · BEATEK Holdings LLC
TRIBUNAL:     PENDING
STAMP_ID:     TCS-2026-0601-BEATEK-ROCM-BUILD-DIRECTML-001
⟦/TCS⟧

# Build llama.cpp with DirectML (Windows)

**Purpose:** Workaround build while the ROCm gfx1100 patch is being developed.
DirectML bypasses ROCm entirely and works correctly on gfx1100 Windows.

---

## Prerequisites

### Required Tools

- Visual Studio 2022 (Community or higher) with:
  - MSVC v143 toolchain
  - Windows 11 SDK (10.0.22621+)
  - CMake tools component
- CMake 3.28+ (standalone or bundled with VS)
- Git for Windows
- Python 3.11+ (for test scripts)

### DirectML SDK

DirectML is included in the Windows SDK. No separate ROCm or CUDA install needed.

---

## Clone llama.cpp

```powershell
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
```

For a specific known-good commit (optional):
```powershell
git checkout <commit-hash>
```

---

## Configure with DirectML

```powershell
cmake -B build `
  -DGGML_DIRECTML=ON `
  -DGGML_CUDA=OFF `
  -DGGML_HIP=OFF `
  -DCMAKE_BUILD_TYPE=Release `
  -A x64
```

---

## Build

```powershell
cmake --build build --config Release -j8
```

Build output location:
```
build\bin\Release\llama-server.exe
build\bin\Release\llama-cli.exe
```

---

## Run llama-server with DirectML

```powershell
.\build\bin\Release\llama-server.exe `
  --model path\to\model.gguf `
  --host 0.0.0.0 `
  --port 8080 `
  -ngl 99
```

`-ngl 99` offloads all layers to DirectML (GPU). The GPU will be selected
automatically — AMD RX 7900 GRE is detected as the primary GPU via DXGI.

---

## Validate GPU Inference

```powershell
# Server should report GPU layers
# Check logs for: "n_gpu_layers = 33" and no CPU fallback warnings
curl http://localhost:8080/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{"model":"llama","messages":[{"role":"user","content":"Hello"}]}'
```

---

## Limitations vs ROCm

| Metric | DirectML | ROCm (when fixed) |
|--------|----------|-------------------|
| Throughput | ~20–30 tok/s | ~40+ tok/s |
| Precision | FP16 / FP32 | FP16 with native ops |
| Flash Attention | Limited support | Full RDNA3 support |
| Status | ✅ Works now | 🔴 Pending fix |

DirectML is the **interim production path** until the ROCm gfx1100 patch
lands in Ollama.

---

## Integration with BEA_Amplify

Set in BEA_Amplify config while DirectML is the active backend:

```yaml
inference:
  backend: directml
  endpoint: http://localhost:8080
  fallback: cpu
```

---

*BEATEK Holdings, LLC · Jeremy F. Jackson · June 2026*
