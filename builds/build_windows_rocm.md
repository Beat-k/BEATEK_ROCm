⟦TCS⟧
DOMAIN:       beatek.project
DOC_TYPE:     build.instructions
PLATFORM:     BEATEK_ROCm
VERSION:      2026.06.01
AUTHORITY:    draft
COSIGN:       Jeremy F. Jackson (Jaxxon) · BEATEK Holdings LLC
TRIBUNAL:     PENDING
STAMP_ID:     TCS-2026-0601-BEATEK-ROCM-BUILD-WINDOWS-001
⟦/TCS⟧

# Build llama.cpp with ROCm (Windows) — gfx1100

**Purpose:** Build the patched llama.cpp with ROCm for Windows gfx1100.
Apply BEATEK patches before building to resolve the KV cache crash.

---

## Prerequisites

### Required Tools

- Visual Studio 2022 (Community or higher) with:
  - MSVC v143 toolchain
  - Windows 11 SDK (10.0.22621+)
  - CMake tools component
- CMake 3.28+
- Git for Windows
- Python 3.11+

### ROCm for Windows

Download ROCm 6.x for Windows from AMD:
```
https://rocm.docs.amd.com/en/latest/deploy/windows/
```

Install to default location: `C:\Program Files\AMD\ROCm\6.x\`

Verify install:
```powershell
hipinfo
# Should report: Device 0: AMD Radeon RX 7900 GRE, gfx1100
```

---

## Clone llama.cpp

```powershell
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
```

---

## Apply BEATEK Patches

From the BEATEK_ROCm repo:

```powershell
# Apply KV cache allocation fix
git apply path\to\BEATEK_ROCm\patches\ggml_hip_kv_alloc.patch

# Apply Flash Attention gfx1100 gate
git apply path\to\BEATEK_ROCm\patches\flash_attention_gfx1100.patch
```

Verify patches applied cleanly:
```powershell
git diff --stat
# Should show: ggml/src/ggml-cuda/ggml-cuda.cu and fattn.cu modified
```

---

## Configure with ROCm for gfx1100

```powershell
# Set ROCm path (adjust version as needed)
$env:HIP_PATH = "C:\Program Files\AMD\ROCm\6.1"

cmake -B build `
  -DGGML_HIP=ON `
  -DAMDGPU_TARGETS=gfx1100 `
  -DGGML_HIP_ROCM=ON `
  -DGGML_CUDA=OFF `
  -DGGML_DIRECTML=OFF `
  -DCMAKE_BUILD_TYPE=Release `
  -DCMAKE_PREFIX_PATH="$env:HIP_PATH" `
  -A x64
```

---

## Build

```powershell
cmake --build build --config Release -j8
```

> **Note:** The HIP compilation step can take 15–30 minutes.
> Parallel jobs (`-j8`) reduce this significantly.

Build output:
```
build\bin\Release\llama-server.exe
build\bin\Release\llama-cli.exe
build\bin\Release\ggml-hip.dll        ← patched version
```

---

## Run Patched llama-server

```powershell
.\build\bin\Release\llama-server.exe `
  --model path\to\model.gguf `
  --host 0.0.0.0 `
  --port 8080 `
  -ngl 99 `
  --no-flash-attn
```

`--no-flash-attn` is included as a belt-and-suspenders flag alongside the
compiled-in guard from `flash_attention_gfx1100.patch`.

---

## Validate Patch Works

```powershell
# Run the BEATEK validation test
python path\to\BEATEK_ROCm\tests\gfx1100_inference_test.py --endpoint http://localhost:8080
```

Expected output:
```
[PASS] GPU inference completed
[PASS] source_type: GPU (not CPU fallback)
[PASS] Latency: < 5s first token
[PASS] No exit code 2
```

---

## Replace Ollama's ggml-hip.dll

Once validated, the patched DLL can replace Ollama's bundled version:

```powershell
# Back up original
Copy-Item "C:\Users\$env:USERNAME\AppData\Local\Programs\Ollama\lib\ollama\rocm\ggml-hip.dll" `
          "C:\Users\$env:USERNAME\AppData\Local\Programs\Ollama\lib\ollama\rocm\ggml-hip.dll.bak"

# Install patched version
Copy-Item "build\bin\Release\ggml-hip.dll" `
          "C:\Users\$env:USERNAME\AppData\Local\Programs\Ollama\lib\ollama\rocm\ggml-hip.dll"
```

Restart Ollama and test:
```powershell
ollama run mistral:7b "Hello"
# Should complete without exit code 2
```

---

*BEATEK Holdings, LLC · Jeremy F. Jackson · June 2026*
