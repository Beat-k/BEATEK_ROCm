"""
BEATEK_ROCm — Patch Application Script
Applies KV cache stream sync fix and FA gate to real llama.cpp HEAD.
Run from: D:\BEATEK_Ecosystem\#BEA_OS\BEATEK_ROCm\llama.cpp

Usage:
    python ..\apply_beatek_patches.py
"""

import sys
import os
import shutil

# ---------------------------------------------------------------------------
# Target files
# ---------------------------------------------------------------------------

CU_FILE  = os.path.join("ggml", "src", "ggml-cuda", "ggml-cuda.cu")
CUH_FILE = os.path.join("ggml", "src", "ggml-cuda", "common.cuh")

# ---------------------------------------------------------------------------
# Patch 1 — FA gate in ggml-cuda.cu
# Wraps the GGML_OP_FLASH_ATTN_EXT case to return false on gfx1100 Windows
# ---------------------------------------------------------------------------

FA_OLD = """\
        case GGML_OP_FLASH_ATTN_EXT:
            return ggml_cuda_flash_attn_ext_supported(dev_ctx->device, op);"""

FA_NEW = """\
        case GGML_OP_FLASH_ATTN_EXT:
#if defined(_WIN32) && defined(GGML_USE_HIP)
            // BEATEK_ROCm: Flash Attention on gfx1100 Windows ROCm 6.x/7.x causes
            // a deterministic access violation (0xc0000005) during context init.
            // The split K/V buffer views use device pointer offsets that the Windows
            // ROCm driver does not commit synchronously on this target.
            // Disable FA on gfx1100 Windows and fall back to standard SDPA path.
            // Linux gfx1100 is NOT affected.
            // Tracking: https://github.com/ollama/ollama/issues/12045
            {
                hipDeviceProp_t prop;
                hipGetDeviceProperties(&prop, dev_ctx->device);
                if (strncmp(prop.gcnArchName, "gfx1100", 7) == 0) {
                    return false;
                }
            }
#endif // defined(_WIN32) && defined(GGML_USE_HIP)
            return ggml_cuda_flash_attn_ext_supported(dev_ctx->device, op);"""

# ---------------------------------------------------------------------------
# Patch 2 — Stream sync in common.cuh
# Inserts hipDeviceSynchronize after stream creation on Windows HIP
# ---------------------------------------------------------------------------

STREAM_OLD = """\
    cudaStream_t stream(int device, int stream) {
        if (streams[device][stream] == nullptr) {
            ggml_cuda_set_device(device);
            CUDA_CHECK(cudaStreamCreateWithFlags(&streams[device][stream], cudaStreamNonBlocking));
        }
        return streams[device][stream];
    }"""

STREAM_NEW = """\
    cudaStream_t stream(int device, int stream) {
        if (streams[device][stream] == nullptr) {
            ggml_cuda_set_device(device);
            CUDA_CHECK(cudaStreamCreateWithFlags(&streams[device][stream], cudaStreamNonBlocking));
#if defined(_WIN32) && defined(GGML_USE_HIP)
            // BEATEK_ROCm: On Windows ROCm 7.x with gfx1100, device memory allocated
            // on the default stream is not guaranteed visible on a newly created
            // non-blocking stream without an explicit sync barrier.
            // This causes an access violation (0xc0000005) when the compute stream
            // first accesses KV cache buffers allocated before this stream was created.
            // Insert hipDeviceSynchronize to commit all prior allocations before
            // the new stream is returned for use.
            // Linux ROCm uses unified VM and does not require this barrier.
            // Tracking: https://github.com/ollama/ollama/issues/12045
            {
                hipError_t sync_err = hipDeviceSynchronize();
                if (sync_err != hipSuccess) {
                    GGML_LOG_ERROR("ggml-hip: hipDeviceSynchronize failed after "
                                   "stream create on gfx1100 Windows: %s\\n",
                                   hipGetErrorString(sync_err));
                }
            }
#endif // defined(_WIN32) && defined(GGML_USE_HIP)
        }
        return streams[device][stream];
    }"""

# ---------------------------------------------------------------------------
# Apply helper
# ---------------------------------------------------------------------------

def apply_patch(filepath, old, new, patch_name):
    print(f"\n[{patch_name}] Patching {filepath} ...")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if old not in content:
        print(f"  [FAIL] Target string not found — source may have changed.")
        print(f"         Search for: {old[:80]!r}")
        return False

    count = content.count(old)
    if count > 1:
        print(f"  [WARN] Target string found {count} times — expected 1. Aborting.")
        return False

    # Back up original
    backup = filepath + ".beatek_orig"
    if not os.path.exists(backup):
        shutil.copy2(filepath, backup)
        print(f"  [INFO] Backup saved to {backup}")
    else:
        print(f"  [INFO] Backup already exists at {backup}")

    patched = content.replace(old, new, 1)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(patched)

    print(f"  [PASS] Patch applied successfully.")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Must run from llama.cpp root
    if not os.path.exists(CU_FILE):
        print(f"[ABORT] {CU_FILE} not found.")
        print(f"        Run this script from the llama.cpp root directory.")
        sys.exit(1)

    print("BEATEK_ROCm — Applying patches to llama.cpp HEAD")
    print("=" * 60)

    results = []

    # Patch 1 — FA gate
    ok = apply_patch(CU_FILE, FA_OLD, FA_NEW, "FA gate / ggml-cuda.cu")
    results.append(("Flash Attention gate (ggml-cuda.cu)", ok))

    # Patch 2 — Stream sync
    ok = apply_patch(CUH_FILE, STREAM_OLD, STREAM_NEW, "Stream sync / common.cuh")
    results.append(("Stream sync after create (common.cuh)", ok))

    # Summary
    print("\n" + "=" * 60)
    all_ok = all(r[1] for r in results)
    for name, passed in results:
        mark = "PASS" if passed else "FAIL"
        print(f"  [{'✅' if passed else '❌'}] [{mark}] {name}")

    print("=" * 60)
    if all_ok:
        print("\n✅ Both patches applied.")
        print("\nNext steps:")
        print("  1. Run: git diff > ..\\patches\\beatek_rocm_HEAD.patch")
        print("     (generates real patch from actual source for the PR)")
        print("  2. Run the cmake build:")
        print("     $env:HIP_PATH = 'C:\\Program Files\\AMD\\ROCm\\7.1'")
        print("     cmake -B build -DGGML_HIP=ON -DAMDGPU_TARGETS=gfx1100 `")
        print("           -DGGML_HIP_ROCM=ON -DGGML_CUDA=OFF -DGGML_DIRECTML=OFF `")
        print("           -DCMAKE_BUILD_TYPE=Release `")
        print("           -DCMAKE_PREFIX_PATH=$env:HIP_PATH -A x64")
        print("     cmake --build build --config Release -j8")
        sys.exit(0)
    else:
        print("\n❌ One or more patches failed — check output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
