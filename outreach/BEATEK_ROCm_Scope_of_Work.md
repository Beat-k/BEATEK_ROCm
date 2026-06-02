# BEATEK Holdings, LLC
## Statement of Work — gfx1100 Windows ROCm Integration Engagement

**Prepared by:** Jeremy F. Jackson · BEATEK Holdings, LLC
**Contact:** jeremy.jackson0@beatek.io · Dallas, Texas
**Date:** June 2026 · Patent Pending

---

## Overview

This Statement of Work defines the scope, deliverables, timeline, and pricing
for a consulting engagement with BEATEK Holdings, LLC to integrate and validate
the BEATEK-developed fix for the gfx1100 Windows ROCm inference crash into
[CLIENT]'s environment or codebase.

The fix resolves a deterministic crash (exit code 2, Exception 0xc0000005)
affecting all AMD Radeon RX 7900 series (gfx1100) users running inference on
Windows via Ollama or llama.cpp with the ROCm backend. Validated at 110 t/s
on RX 7900 GRE · Windows 11 · ROCm 7.1.

---

## Engagement Options

---

### Option A — Fix Integration & Validation
**Best for:** Ollama, llama.cpp maintainers, AMD ROCm team

**Scope:**
- Technical walkthrough of both root causes (KV cache stream affinity + FA layout)
- Integration of the 35-line patch into [CLIENT]'s codebase or build pipeline
- Build environment configuration for Windows ROCm 7.x + VS 2026
- ROCm 7.1 clang header conflict documentation and resolution
- End-to-end validation on gfx1100 hardware
- Written validation report with benchmark results
- One round of post-integration support (30 days)

**Deliverables:**
- Integrated patch in [CLIENT]'s target branch
- Validation report (hardware, OS, ROCm version, benchmark numbers)
- Build environment documentation
- 30-day post-integration support window

**Timeline:** 2–3 weeks from engagement start

**Investment:** $8,000 – $12,000 fixed fee
*(Final price scoped after discovery call)*

---

### Option B — Full Build Environment Package
**Best for:** Enterprise teams running gfx1100 Windows inference at scale

**Scope:**
- Everything in Option A
- Full reproducible Windows ROCm 7.x + VS 2026 build documentation
- CMake configuration guide for gfx1100 targets
- ROCm header patch documentation (clang/21/include conflicts)
- HIP-level isolation test suite (stream sync, KV cache alloc)
- End-to-end inference test suite (llama-server + Ollama)
- Internal knowledge transfer session (1 hour)

**Deliverables:**
- Everything in Option A
- Full build guide (reproducible from scratch)
- Automated test suite (HIP-level + end-to-end)
- Knowledge transfer recording

**Timeline:** 3–4 weeks from engagement start

**Investment:** $15,000 – $22,000 fixed fee
*(Final price scoped after discovery call)*

---

### Option C — Ongoing Windows ROCm Support Retainer
**Best for:** Teams that need someone who owns the Windows ROCm stack

**Scope (monthly):**
- Regression testing against new ROCm / Ollama / llama.cpp releases
- Patch maintenance as upstream codebase evolves
- Priority email support (response within 1 business day)
- Quarterly build validation report
- Access to all future BEATEK ROCm Windows findings

**Deliverables (monthly):**
- Regression test results
- Updated patch status vs. upstream
- Quarterly validation report

**Investment:**
| Tier | Includes | Monthly |
|---|---|---|
| Basic | Regression testing + patch updates + email support | $2,000 |
| Standard | Basic + quarterly build validation + 2hr consulting | $4,000 |
| Premium | Standard + dedicated SLA (4hr response) + monthly call | $7,500 |

---

## What Is Not Included

- Hardware procurement or setup
- Upstream PR submission on behalf of client (available as add-on)
- Support for non-gfx1100 architectures (available as separate engagement)
- Legal or patent filings

---

## About BEATEK

BEATEK Holdings, LLC is a Dallas-based compute platform engineering firm
specializing in heterogeneous inference systems. BEATEK_ROCm was developed
as a production requirement for BEA_Aura — a platform combining AMD GPU,
Coral Edge TPU, and multi-OS orchestration. The gfx1100 Windows ROCm fix
was validated in production before any external engagement.

Full project documentation, patch files, and validation results:
**https://github.com/Beat-k/BEATEK_ROCm**

---

## Next Steps

1. Discovery call (30 min) — understand your environment and target
2. BEATEK sends scoped SOW with fixed fee
3. Client signs · 50% deposit to begin · 50% on delivery
4. Engagement starts within 5 business days of deposit

---

**Jeremy F. Jackson**
Founder, BEATEK Holdings, LLC
jeremy.jackson0@beatek.io
Dallas, Texas · © 2026
Patent Pending · beatek-rocm-validated-2026-06-02
