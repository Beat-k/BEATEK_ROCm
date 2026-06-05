# The Resource Provider Framework
**BEATEK Holdings, LLC · Jeremy F. Jackson**
**Conceived:** August 2025 · **First Published:** June 5, 2026
**Patent Pending**

---

## The Stack

Every layer of modern compute has a category of company that owns it:

| Resource | Providers |
|---|---|
| CPU Resource Providers | AMD · Intel |
| GPU Resource Providers | AMD · NVIDIA · Intel |
| NPU Resource Providers | Intel |
| TPU Resource Providers | Google · Qualcomm · Apple |
| Memory Resource Providers | Samsung · Micron · SK Hynix |
| **Intelligence Resource Provider** | **BEATEK** |

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

BEATEK does not compete with AMD, NVIDIA, Google, Intel, or Samsung.
BEATEK completes them.

Every chip they manufacture becomes more valuable when an Intelligence
Resource Provider makes it part of a working stack.

BEATEK is that layer.

---

## Validated Production Work

| Component | Result |
|---|---|
| gfx1100 Windows ROCm fix | 110 t/s · exit code 2 eliminated |
| BEA_TidePool VRAM Architecture | Coral TPU + RX 7900 GRE sharing VRAM over PCIe |
| Dispatch latency | ~3000ms (NVMe) → ~5ms (VRAM) |
| Test suite | 91 passed |
| Stack | RX 7900 GRE · Coral Dual Edge TPU · ROCm 7.1 · Windows 11 |

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
