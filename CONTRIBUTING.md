⟦TCS⟧
DOMAIN:       beatek.project
DOC_TYPE:     contribution.guide
PLATFORM:     BEATEK_ROCm
VERSION:      2026.06.02
AUTHORITY:    draft
COSIGN:       Jeremy F. Jackson (Jaxxon) · BEATEK Holdings LLC
TRIBUNAL:     PENDING
STAMP_ID:     TCS-2026-0601-BEATEK-ROCM-CONTRIB-001
⟦/TCS⟧

# Contributing to BEATEK_ROCm

Thank you for your interest in this project. BEATEK_ROCm exists to fix a
real crash that blocks GPU inference for every gfx1100 Windows user running
Ollama. Contributions that move the fix closer to upstream are welcome.

---

## What This Project Needs

| Area | What's Needed |
|------|---------------|
| **Testing** | Run `kv_cache_alloc_test.py` on gfx1100 Windows and report results |
| **Build validation** | Build with `build_windows_rocm.md` instructions and confirm patch applies clean |
| **Patch review** | Code review of `ggml_hip_kv_alloc.patch` and `flash_attention_gfx1100.patch` |
| **Upstream** | Help land the patches in llama.cpp and Ollama |
| **Other gfx targets** | Test on gfx1101, gfx1102, or other RDNA3 variants to check generalizability |
| **Linux ROCm** | Confirm the Linux reference build works on your gfx1100 system |

---

## Before You Contribute

1. **Read the root cause analysis** — `crash_analysis/reproduction.md` and
   `crash_analysis/environment.md`. Understand what the crash is and why.
2. **Understand the two patches** — `BEATEK_ROCm_README.md` §*How BEATEK_ROCm Works*
   explains the interaction between the KV alloc fix and the FA gate.
3. **Run the tests** — at minimum run `kv_cache_alloc_test.py` on your hardware
   before making any changes to the patches.

---

## Reporting Findings

If you can reproduce (or cannot reproduce) the crash on your hardware, open an
issue or send findings to **jeremy.jackson0@beatek.io** with:

- Your GPU model and gfx target (`rocminfo | grep gfx`)
- Your Windows version and AMD driver version
- Your Ollama version
- Full output of `ollama run mistral:7b "hello"` with ROCm backend
- Output of `kv_cache_alloc_test.py` if ROCm is installed

Negative results (no crash on gfx1100) are as valuable as positive ones.
Please include the full log, not just the conclusion.

---

## Submitting a Patch Improvement

### Setup

```powershell
git clone https://github.com/beatek/BEATEK_ROCm   # or fork
cd BEATEK_ROCm
```

### Rules for Patch Changes

1. **Do not break upstream applicability.** The patches must apply cleanly to
   the current llama.cpp `master` branch via `git apply`. Always verify:
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   git apply path/to/BEATEK_ROCm/patches/ggml_hip_kv_alloc.patch
   ```

2. **Scope patches tightly.** Each patch must touch only what is necessary.
   Do not bundle unrelated changes. Do not reformat or rename.

3. **Keep the Windows guard.** Both patches use `#if defined(_WIN32) && defined(GGML_HIP_ROCM)`.
   Changes must not remove this guard — the fix must not affect Linux builds.

4. **Update the commit message** in the patch header to accurately describe
   your change. Follow the existing format (summary line + blank + body +
   `Signed-off-by`).

5. **Test before submitting.** Run both test scripts and include the output
   in your pull request description.

### Pull Request Checklist

- [ ] `git apply` succeeds on current llama.cpp master
- [ ] `kv_cache_alloc_test.py` passes on gfx1100 Windows
- [ ] `gfx1100_inference_test.py` passes against a patched build
- [ ] Windows `#if` guard is present and correct
- [ ] No unrelated formatting or refactor changes
- [ ] Commit message in patch header is accurate
- [ ] `Signed-off-by: Your Name <your@email.com>` present in patch

---

## Submitting to Upstream (llama.cpp / Ollama)

The end goal is landing these fixes upstream. If you have experience with the
llama.cpp contribution process, help is especially welcome here.

### llama.cpp PR Requirements

llama.cpp uses a standard GitHub PR workflow. The patch should be submitted
as a proper commit (not a `.patch` file) with:

- Title: `ggml-hip: fix KV cache context alloc crash on gfx1100 Windows ROCm`
- Body: include the root cause explanation, the crash log excerpt, and a
  reference to this repository for the full analysis
- The PR must not break any existing CI targets — the `#if defined(_WIN32)`
  guard ensures Linux builds are not affected

### Ollama Issue Comment

A comment on https://github.com/ollama/ollama/issues/12045 with:
- The root cause analysis summary
- A reference to the llama.cpp PR once filed
- The crash log from `crash_analysis/`

---

## Code Style

Follow the surrounding code style in whatever file you are editing. For
llama.cpp / ggml-hip specifically:

- C-style casts, not C++-style, in C files
- Error checking on every HIP call (use the existing `GGML_CUDA_CHECK` or
  `hip_check` pattern already in the file)
- `GGML_LOG_ERROR` for error messages (not `fprintf` or `printf`)
- Comments in English, full sentences, present tense

---

## Conduct

This is a focused engineering project. Contributions are judged on technical
merit and accuracy. Be precise, be correct, cite your sources.

---

## License

This project uses a **dual license** — see `LICENSE` for full terms.

- **Non-commercial / open-source contributions** are accepted under the
  MIT license (License 1 in `LICENSE`).
- **Commercial use** of any contributed code requires a separate Commercial
  License from BEATEK Holdings, LLC (License 2 in `LICENSE`).

By submitting a contribution you affirm that:
1. Your contribution is your original work or you have the right to submit it.
2. You grant BEATEK Holdings, LLC the right to use your contribution under
   both the MIT and BEATEK Commercial licenses.
3. For patches submitted upstream to llama.cpp or Ollama, you additionally
   agree to those projects' contributor terms at the time of submission.

See `LICENSE` for the full patent notice and dual-license terms.

---

*BEATEK Holdings, LLC · Jeremy F. Jackson · Dallas, Texas · © 2026*
*jeremy.jackson0@beatek.io*
