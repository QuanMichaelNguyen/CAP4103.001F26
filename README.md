# Multimodal Exam Identity Authentication (CAP4103 Fall 2026)

**Scope:** Experimental biometric user authentication for an online-proctoring scenario. This does **not** determine whether cheating occurred; it evaluates whether a claimed identity is consistent with face and keystroke biometrics. This is not affiliated with Honorlock.

## Research questions
- **RQ1:** How do face and keystroke authentication compare when distinguishing genuine users from impostors?
- **RQ2:** Does equal-weight score fusion improve performance over either modality alone?
- **RQ3:** How does changing the face-to-keystroke fusion weight affect performance?

## Setup and dataset acquisition
Python 3.10+ recommended. Run from the repository root:

```bash
python -m venv .venv
# On Windows: .venv\\Scripts\\activate
# On macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -c "from sklearn.datasets import fetch_olivetti_faces; fetch_olivetti_faces(download_if_missing=True)"
```

Download the **Keystroke Dynamics - Benchmark Data Set** from Carnegie Mellon University: https://www.cs.cmu.edu/~keystroke/ . Save `DSL-StrongPasswordData.csv` in `data/`. Check licensing and permitted educational use before downloading or redistributing. Dataset files are not checked into Git.

```bash
python -m src.experiment --mode real --keystroke-csv data/DSL-StrongPasswordData.csv --n-users 40
python -m pytest -q
```

Output is written to `results/metrics.json`, `results/identity_mapping.json`, and four project PNG figures plus HW3-generated score distributions, ROC, and DET curves. All evaluation data derives from the actual public datasets if `--mode real` successfully completes.

## Offline smoke test (NOT valid research data)
```bash
python -m src.experiment --mode demo --n-users 12 --output results/demo
```
Demo mode generates **synthetic data** for software verification only. Never cite its metrics as empirical findings. `results/demo/` output is intentionally not a research deliverable.

## Protocol
1. Select up to 40 users in each modality using a fixed random seed (`4103`); **simulate** a one-to-one user identity mapping. A face subject and keystroke subject are different real people and are **not** claimed to be the same individual.
2. Within each modality and subject, assign 50% of samples to enrollment, 20% to validation, and the rest to test (integer rounded). All three partitions are mutually exclusive. Use enrollment-only preprocessing and templates.
3. Facial matcher: standardize facial pixels, apply enrollment-trained PCA, compare probe and per-user template with negative Euclidean distance. Keystroke matcher: standardize time features, calculate negative Euclidean distance to the enrolled template.
4. RQ1 computes individual probe comparisons; RQ2 and RQ3 aggregate held-out probe scores per `(actual identity, claimed identity)` so different numbers of face and typing samples cannot duplicate or manufacture synchronized observations. This estimates performance on **identity-level mean scores**, not per-keystroke continuous monitoring.
5. Standardize both modality scores using **validation-score statistics**, then fuse them: `score = weight*face + (1-weight)*keystroke`. RQ2 uses weight 0.5. RQ3 tests weights 0, 0.25, 0.5, 0.75, 1.0. Choose a weight using validation EER alone, then report the locked test EER.
6. Report EER (nearest observed crossing, FAR/FRR average), d-prime, genuine/impostor score distributions. For small datasets, rates are approximate and may be unstable; no confidence intervals are claimed.

**Known limitations:** synthetic cross-dataset user identities; a fixed passphrase typing dataset; different sample granularity for RQ1 vs fusion; no face liveness or real exam data; and no evidence that identity mismatch equals cheating. Score fusion can be vulnerable to spoofing and demographic or device effects. Thresholds are not suitable for a production proctoring decision.

## Course compliance notes
- The provided HW3 `main.py` is preserved unchanged in `hw3/main.py`. The adapter in `src/hw3_evaluation.py` calls its `Evaluator` on **actual** genuine and impostor scores from every experiment (not the random synthetic scores in HW3’s standalone example `main()`). Its input scores are calibrated to [0,1] using validation-only statistics. The results appear under `hw3` in `results/metrics.json`; HW3 produces genuine/impostor distributions, DET and ROC plots for RQ1 and fused conditions. HW3 uses a fixed threshold grid and may differ slightly from our independent empirical-threshold EER.
- Report/presentation are draft artifacts. Replace `RESULTS PENDING` placeholders with real metrics and plots after dataset execution; do not present demo-mode metrics as real results.
- The report template and project description disagree on bibliography article count; November 15 instructions make the annotated bibliography optional (4+ articles if used). See `report/`.

## Project deliverables
- `report/CAP4103_Exam_Authentication_DRAFT.docx`: course-format paper with methodology, ethics, references, and explicit placeholders for experiment findings.
- `presentation/CAP4103_Exam_Authentication_DRAFT.pptx`: nine slides based on the supplied template with result placeholders.
- `templates/`: supplied editable templates for reproducibility.
- `build_deliverables.py`: regenerate the two draft documents based on those templates (`python build_deliverables.py`). **Regeneration replaces draft documents**, so edit copies before running it again.
- `hw3/main.py` and `src/hw3_evaluation.py`: original course evaluator and integration adapter.
- `PUSH_INSTRUCTIONS.md`: GitHub branch publishing steps, because the connection lacks write permission.

To finish the scientific report, run the real datasets and copy the numbers and generated figures into the drafts. The current report and slides are **not** a finalized empirical submission.
