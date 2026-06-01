⟦TCS⟧
DOMAIN:       beatek.project
DOC_TYPE:     build.instructions
PLATFORM:     BEATEK_ROCm
VERSION:      2026.06.01
AUTHORITY:    draft
COSIGN:       Jeremy F. Jackson (Jaxxon) · BEATEK Holdings LLC
TRIBUNAL:     PENDING
STAMP_ID:     TCS-2026-0601-BEATEK-ROCM-BUILD-LINUX-001
⟦/TCS⟧

# Build llama.cpp with ROCm (Linux) — gfx1100

**Purpose:** Reference build on BEA_Lace_OS (Linux). This build runs
correctly without any patches, confirming the crash is Windows-specific.

---

## Platform

- **OS:** BEA_Lace_OS (Debian 12 / Ubuntu 24.04 base)
- **GPU:** AMD Radeon RX 7900 GRE (gfx1100) via PCIe passthrough
- **ROCm:** 6.1.x (native package install)
- **Kernel:** 6.8+ with AMDGPU driver

---

## Install ROCm on Linux

```bash
# Add ROCm repo (Debian/Ubuntu)
wget https://repo.radeon.com/amdgpu-install/6.1/ubuntu/jammy/amdgpu-install_6.1.60100-1_all.deb
sudo dpkg -i amdgpu-install_6.1.60100-1_all.deb
sudo amdgpu-install --usecase=rocm

# Add user to render/video groups
sudo usermod -aG render,video $USER
```

Reboot, then verify:
```bash
rocminfo | grep -A3 "gfx1100"
# Should show: AMD Radeon RX 7900 GRE · gfx1100
```

---

## Install Build Dependencies

```bash
sudo apt-get install -y \
  cmake \
  ninja-build \
  git \
  python3 python3-pip \
  rocm-hip-sdk \
  hipcc
```

---

## Clone llama.cpp

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
```

> **No patches needed on Linux.** This is the reference build to confirm
> the hardware is not the problem. Apply patches only for the Windows build.

---

## Configure for gfx1100

```bash
cmake -B build \
  -DGGML_HIP=ON \
  -DAMDGPU_TARGETS=gfx1100 \
  -DCMAKE_BUILD_TYPE=Release \
  -GNinja
```

---

## Build

```bash
cmake --build build --config Release -j$(nproc)
```

Build output:
```
build/bin/llama-server
build/bin/llama-cli
```

---

## Run llama-server on Linux

```bash
./build/bin/llama-server \
  --model /path/to/model.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -ngl 99
```

Server log should show:
```
ggml_cuda_init: found 1 ROCm devices:
  Device 0: AMD Radeon RX 7900 GRE, gfx1100
load_tensors: offloaded 33/33 layers to GPU
llama_context: Flash Attention was auto, set to enabled
llama server listening at http://0.0.0.0:8080
```

No crash. Inference runs correctly at ~40+ tok/s.

---

## Validate

```bash
python3 /path/to/BEATEK_ROCm/tests/gfx1100_inference_test.py \
  --endpoint http://localhost:8080
```

Expected:
```
[PASS] GPU inference completed
[PASS] source_type: GPU (not CPU fallback)
[PASS] Flash Attention: enabled
[PASS] Latency: < 3s first token
```

This is the **target state** for the Windows ROCm fix — identical behavior,
both platforms.

---

## Why This Matters

The Linux build:

1. **Proves the hardware is not defective** — same GPU, works correctly
2. **Provides a diff target** — compare Linux ggml-hip build flags vs Ollama's
   Windows bundled build to isolate compile-time differences
3. **Becomes the primary inference path** once BEA Aura Console hardware
   provides correct PCIe topology for Linux GPU passthrough

---

## BEA_Lace_OS Integration

Once the Linux server is running, configure BEA_Amplify to route to it:

```yaml
inference:
  backend: rocm_linux
  endpoint: http://<bea-lace-ip>:8080
  fallback: directml_windows
```

---

*BEATEK Holdings, LLC · Jeremy F. Jackson · June 2026*
