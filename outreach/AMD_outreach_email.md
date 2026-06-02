# AMD Outreach Email — gfx1100 Windows ROCm Fix

**To:** rocm-github-master-branching@amd.com
**CC:** devgurus@amd.com
**Subject:** Validated fix for gfx1100 Windows ROCm inference crash — consulting engagement inquiry

---

Hi,

My name is Jeremy Jackson. I'm the founder of BEATEK Holdings, LLC, a compute
platform engineering firm based in Dallas. I'm reaching out because I've
diagnosed and validated a fix for the deterministic crash affecting gfx1100
users running ROCm inference on Windows — and I'd like to discuss a consulting
engagement to get it integrated properly.

**The issue:**
Every AMD Radeon RX 7900 series user running Ollama or llama.cpp on Windows
hits exit code 2 at inference startup. The GPU is detected, layers offload,
and then the process crashes at KV cache initialization. It's been open since
approximately Ollama 0.11.5 and is unresolved as of this writing.

**What I found:**
Two independent root causes:

1. Windows ROCm enforces stream affinity on device allocations. `ggml-hip`
allocates the KV cache buffer on the default HIP stream and immediately
accesses it on a separately created compute stream without a sync barrier.
On Linux, unified VM tolerates this. On Windows the pointer is invalid at
first access — access violation at a deterministic address every run.

2. Flash Attention on gfx1100 Windows has an unresolved memory layout issue
with split K/V view tensors that triggers a secondary fault independent of
the stream affinity issue.

**What I built:**
A 35-line patch across two files in llama.cpp that resolves both issues
completely. Gated on `#if defined(_WIN32)` and `gcnArchName` prefix — no
impact on Linux, no impact on other architectures.

**Validated results on RX 7900 GRE · gfx1100 · Windows 11 · ROCm 7.1:**
- 110.17 tokens/s direct (llama-server)
- 108.75 tokens/s end-to-end (Ollama)
- 1.34s total inference time
- All HIP stream sync tests passing
- No exit code 2

I also documented ROCm 7.1 + VS 2026 header conflicts in `clang/21/include/`
that block any Windows ROCm build against the current MSVC STL — not
previously documented publicly.

**What I'm proposing:**
A consulting engagement to integrate this fix into the ROCm Windows stack,
document the full Windows ROCm 7.x + VS 2026 build environment, and deliver
a reproducible test suite for gfx1100 Windows inference. I have a capability
brief available on request.

I'm happy to get on a call at your convenience.

**Jeremy F. Jackson**
Founder, BEATEK Holdings, LLC
jeremy.jackson0@beatek.io
Dallas, Texas
