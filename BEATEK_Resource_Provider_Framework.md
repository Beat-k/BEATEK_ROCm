# The Resource Provider Framework
**BEATEK Holdings, LLC · Jeremy F. Jackson**
**Conceived:** August 2025 · **First Published:** June 5, 2026
**Patent Pending**

---

## The Stack

Every layer of modern compute has a category of company that owns it:

| Resource | Providers |
|---|---|
| CPU Resource Providers | AMD · Intel · Apple |
| GPU Resource Providers | AMD · NVIDIA · Intel · Apple |
| NPU Resource Providers | Intel · Qualcomm · Apple |
| TPU Resource Providers | Google · Qualcomm · Apple |
| Memory Resource Providers | Samsung · Micron · SK Hynix |
| **Intelligence Resource Providers** | **BEATEK · Sony · Microsoft · Nintendo · Amazon · Apple · Dell · HP · Lenovo** |

---

## What Each Layer Does

CPU, GPU, NPU, TPU, and Memory Resource Providers manufacture components.
They make the silicon. They ship the hardware. They write the drivers.

They do not make the components work together as intelligence.

That is the gap.

---

## What an Intelligence Resource Provider Does

An Intelligence Resource Provider takes the output of every layer below it
and produces a unified, working, heterogeneous intelligence stack.

Not renting compute.
Not writing models.
Not managing cloud clusters.

**Making the hardware think.**

The GPU Resource Provider gives you 16GB of VRAM.
The NPU Resource Provider gives you on-chip AI acceleration.
The TPU Resource Provider gives you an edge classifier.
The Memory Resource Provider gives you the bandwidth.

The Intelligence Resource Provider makes them one system —
sharing memory, dispatching jobs, running inference —
as a single coherent platform.

Every company in the Intelligence Resource Providers row takes silicon
from the rows above and makes it think. The silicon does not change.
What changes is what you do with it.

---

## Why This Category Didn't Exist Before

Because the hardware wasn't there yet.

ROCm on Windows wasn't production-ready.
VRAM wasn't addressable as shared compute memory.
PCIe co-processor architectures weren't validated outside research labs.

As of June 3, 2026 — on an RX 7900 GRE · gfx1100 · ROCm 7.1 —
all three are production reality.

The category exists because the infrastructure finally supports it.
BEATEK built on it the day it became possible.

---

## BEATEK's Position

BEATEK does not compete with AMD, NVIDIA, Google, Intel, Apple, or Samsung.
BEATEK completes them.

Every chip they manufacture becomes more valuable when an Intelligence
Resource Provider makes it part of a working stack.

BEATEK is that layer.

---

## Validated Production Stack — June 5, 2026

### GPU Layer — AMD RX 7900 GRE · ROCm gfx1100

| Component | Result |
|---|---|
| gfx1100 Windows ROCm fix | exit code 2 eliminated · production stable |
| ROCm Benchmark — Run 1 | 66.5 t/s avg · 83.4 t/s peak · 3.01s avg latency |
| ROCm Benchmark — Run 2 | 65.2 t/s avg · 83.3 t/s peak · 3.07s avg latency |
| Layers offloaded | 33/33 fully GPU · ngl 99 |
| KV cache | 4 slots · 2048 ctx each · 992 MiB VRAM |
| Model | Mistral 7B Instruct v0.3 Q4_K_M |
| Server | llama-server · 127.0.0.1:8080 · LIVE |

**BEATEK ROCm patch applied:**
- KV cache stream affinity (ggml-cuda.cu)
- Flash Attention gate for gfx1100 Windows (common.cuh)
- Without fix: exit code 2 crash on every request

### TPU Layer — Google Coral Dual-Edge TPU

| Component | Result |
|---|---|
| Coral benchmark | 50 jobs · 100% SourceType.CORAL · 0 fallbacks |
| Avg latency | 2164.5ms (NVMe TidePool queue path — correct physics) |
| Min latency | 2112.5ms |
| P50 latency | 2114.6ms (2ms spread — extremely consistent) |
| P95 latency | 2316.4ms |
| Silicon inference | 0.147ms on-chip · 6,820 inferences/sec per die |
| Active roles | 5 roles · 46% TOPS allocated · 54% available |
| All ops | Mapped to Edge TPU · 0 off-chip streaming on all models |

**5 Coral Secretary roles live:**

| Role | Pillar | TOPS | Priority |
|---|---|---|---|
| amplify_signal_monitor | BEA_Amplify | 8% | 3 |
| grid_power_watch | BEA_Grid | 5% | 7 |
| lens_visual_classifier | BEA_Lens | 10% | 5 |
| scene_analyze | BEA_Prism | 15% | 2 |
| audio_s_degree_classifier | BEA_4D_Audio | 8% | 4 |

**All models trained, quantized int8, compiled with edgetpu_compiler v16.0:**
- Full integer quantization · TFLITE_BUILTINS_INT8
- 1 Edge TPU subgraph per model · entire model on-chip
- 0.00B off-chip streaming on all 5 models

### Intelligence Layer — BEA_Nexus 4D Formula

```
VISUAL  (BEA_Lens)      ⊕
AUDIO   (BEA_4D_Audio)  ⊕
DEPTH   (BEA_Prism)     ⊕
MOTION  (pending)
────────────────────────
Composite → Ω (MAXIMUM_STATE)
Immersion: full_4d · Is Omega: True
```

Validated 4D frame — Siege 6 scenario:
- VISUAL E[16] green outdoor · AUDIO E[31] gunfire 880Hz S°=12.0°
- MOTION E[22] player sprinting · DEPTH E[14] HIGH quality
- Composite: E[23] · full_4d · Omega: True

### Full Stack

| Component | Status |
|---|---|
| llama-server (ROCm gfx1100) | LIVE · 127.0.0.1:8080 · 66.5 t/s avg |
| BEACoralBridge (NSSM) | LIVE · 5 roles assigned · Keepalive OK |
| BEA_Secretary (BEA_Lace_OS) | LIVE · 192.168.1.207:7475 · Trust Gate ACTIVE |
| GPU Bridge | LIVE · watching TidePool NVMe queue |
| TidePool | T:\BEATEK_Ecosystem\TidePool · all zones present |
| BEA_Lace_OS VM | T:\BEA_Lace_OS · IP 192.168.1.207 |
| Platform | T:\ Samsung 980 PRO NVMe · full ecosystem |

### Hardware

```
CPU:    AMD Ryzen 7 5700X3D · 64GB RAM
GPU:    AMD RX 7900 GRE 16GB · gfx1100 · ROCm 7.1
TPU:    Google Coral Dual-Edge · 8 TOPS · ~2W constant
OS:     Windows 11 · BEA_Lace_OS (Hyper-V VM)
NVMe:   Samsung 980 PRO (T:\) · TidePool IPC layer
```

Full documentation: https://github.com/Beat-k/BEATEK_ROCm

---

## The Definition

> **Intelligence Resource Provider** *(n.)*
> A company or entity that integrates heterogeneous compute hardware —
> CPU, GPU, NPU, TPU, and memory — into a unified intelligence platform.
> Distinguished from component manufacturers by operating at the
> system level rather than the silicon level.
> The layer that turns hardware into intelligence.

---

*BEATEK Holdings, LLC · Jeremy F. Jackson · Dallas, Texas · © 2026*
*Conceived August 2025 · Published June 5, 2026*
*"We don't make the chips. We make the chips think."*
