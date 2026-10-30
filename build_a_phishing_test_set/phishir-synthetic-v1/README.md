# PhishIR-Synthetic v1 — paper-aligned incident-response test set

## What this is

A reproducible **synthetic development benchmark**, grounded in the phishing-to-endpoint case study in *Transforming Incident Response: The Role of Hugging Face Diffusers in Automating Cybersecurity Workflows*, DOI https://doi.org/10.22541/au.177446759.98281679/v1. This is not the paper's original data, a replication of its reported results, or evidence of deployment readiness.

**1,000 records = 20 lure families × 25 surface/context variants × 2 email labels.** Each record contains one email and one endpoint-context snapshot. There are 500 matched benign/phishing pairs. The semantic core is only 40 email templates; 1,000 rows must not be interpreted as 1,000 independent incident narratives.

## What was inferred from the paper

| Paper evidence | Benchmark choice | Adaptation or limit |
|---|---|---|
| §4.2, pp. 9–10: 10,000 balanced phishing/legitimate emails, approximately 5,000 SOC alerts, approximately 2,000 incident descriptions; 80/10/10 split | Balanced binary email labels; 800/100/100 fixed split | None of the underlying corpora or private SOC records is supplied here. Simulate 1,000 records rather than imply access or reproduce 10,000 emails. |
| §4.5, pp. 13–14: DistilBERT, subject/body text, labels 1 phishing / 0 not phishing | `email_text` and `phishing_label`; CPU TF-IDF/logistic baselines | No transformer fine-tuning, checkpoint download, or Diffusers pipeline was run. The paper's classifier code uses **Transformers**, not diffusion-based text generation. |
| §§4.1–4.4, pp. 8–12: incident classification and exact entity-span/type evaluation | Four observable types: URL, DOMAIN, IPV4, SHA256 | Narrow to deterministic observable extraction. Malware names, actors, CVEs, open-world NER and general multiclass incident classification are not covered. |
| §§5.1–5.2, pp. 15–17: phishing email, endpoint execution, user/host/time correlation | Email plus absent, benign, correlated, wrong-host or stale endpoint context | Five evenly represented states; event user and host IDs are synthetic. A text-described QR destination is included; there are no QR images or multimodal inputs. |
| §5.2, p. 16: email alone is insufficient to quarantine a host; §4.3, pp. 10–11: human oversight | Separate email-removal and host-containment labels | A **benchmark-specific 60-minute window**, not a claimed threshold from the paper. Identity action is review, not automatic account disablement. |

The supplied PDF's internal citation says 2025 / preprint v2, whereas the requested DOI record is described as 2026. This benchmark follows the supplied full text and identifies it by the requested DOI.

## Tasks, inputs and label definitions

1. **Phishing classification.** Use **only `email_text`**. Gold: `phishing_label=1` for the constructed malicious request, `0` for the authorized workflow. This intentionally includes business-email-compromise/payment diversion, not only credential theft. Sender-domain spelling and identifiers are matched across each positive/negative pair. The labels concern the email, independently of endpoint compromise.
2. **Observable extraction.** Use `text`. Return exact `(start, end, type)` spans; zero-based Unicode indices, exclusive end. A URL is one entity including its hostname; no nested DOMAIN annotation. All observable occurrences are annotated, including benign ones. An observable is **not automatically malicious**. Defanged URL spelling is preserved.
3. **Containment eligibility / response policy.** Use `text` plus `observable`. Scope is the email-associated host, not every host mentioned in an alert. `correlated_compromise=true` requires explicit malicious endpoint evidence on that host within 0–60 minutes. Correlation is not proof of email causality.

| `response_label` | Constructed policy |
|---|---|
| `contain_host_review_identity` | Malicious endpoint evidence on the same host within 60 minutes, regardless of email label. |
| `analyst_review` | Malicious endpoint evidence is on another host or stale; do not automatically isolate the email host. Investigate the other host separately. |
| `purge_email_review` | Phishing email without qualifying endpoint compromise; remove/review email, do not isolate host. |
| `no_disruptive_action` | Benign email and no qualifying malicious endpoint evidence. |

`id`, `split`, `family_id`, `pair_id`, `provenance`, `endpoint_state`, `annotation_basis`, and **all gold annotations** are excluded from model features. IDs themselves encode labels: passing them to a classifier is direct leakage. `text` is disallowed for email-only evaluation because later endpoint information is unavailable at email arrival.

## Splits and realism constraints

- **Train:** 800 rows, 16 families; **validation:** 100 rows, survey/printer families; **test:** 100 rows, payroll/QR-access families. Both labels and each matched pair remain in the same split. Each split is class balanced.
- **Context:** Each endpoint state contributes 20% of each split. Containment eligibility is 20%; response labels are 20% contain, 40% analyst review, 20% purge, 20% no action.
- **Safety:** Fictional identities, `.example` domains, documentation IPv4 addresses `192.0.2.0/24`, synthetic SHA256 identifiers; no credentials, payloads, executable attachments, live indicators, external calls or actual response actions.
- **Truth:** Labels are determined by authored scenarios and span insertion, not model predictions or analyst review. Extraction baseline regex is separate from span construction. Authorized benign workflows and malicious requests share topics, sender spelling and surface identifiers.
- **Checks run:** Full-text uniqueness; family and pair disjointness; exact span slicing; no email-only containment. These do not establish semantic diversity or eliminate shared writing style.

## Measured results

All following values are computed locally, not copied from the paper. No test-set parameter tuning or model selection was performed; both predeclared learned baselines are reported.

### Email classification — held-out test, 50 phishing / 50 benign

| Baseline | Accuracy | Precision | Recall | F1 | FPR | TN / FP / FN / TP |
|---|---:|---:|---:|---:|---:|---|
| Always benign | .50 | .00 | .00 | .00 | .00 | 50 / 0 / 50 / 0 |
| Keyword rule | .50 | .00 | .00 | .00 | .00 | 50 / 0 / 50 / 0 |
| Word TF-IDF + logistic regression | .75 | .667 | 1.00 | .80 | .50 | 25 / 25 / 0 / 50 |
| Character TF-IDF + logistic regression | .75 | .667 | 1.00 | .80 | .50 | 25 / 25 / 0 / 50 |

Both learned models achieve validation F1 1.00. On test, the word model is perfect on payroll but predicts phishing for **all 50 QR-access records**, including all 25 benign notices. This is a useful lexical/negation generalization failure, not a robust phishing detector. The keyword rule misses every held-out positive because its fixed vocabulary does not cover those lure requests. Undefined positive precision is reported as zero, not evidence of reliable negative classification.

### Extraction and response — held-out test

- **Regex extraction:** 320 exact typed spans; TP=320, FP=0, FN=0; micro-F1=1.00. The input types and syntax are deliberately regex-friendly; this is a parsing sanity check, not threat-intelligence understanding or open-world NER performance.
- **Never contain:** accuracy .80 but containment recall 0. This illustrates why accuracy alone is misleading.
- **Payload-keyword containment:** precision .333, recall 1.00, F1 .50; 40 false containment decisions / 60 predicted containments. FPR is 40/80=.50 among ineligible email-host snapshots. Wrong-host/stale evidence causes these errors.
- **Word classifier + host/time correlation policy:** four-way response accuracy .90; macro-F1 .867. Containment TP=20, TN=80, FP=FN=0; remaining errors are inappropriate benign-email purge recommendations. The rule directly encodes the synthetic policy and therefore is an implementation check, not independent evidence of safe real-world automation.

Here **FPR = FP/(FP+TN)**, not `1 - precision`. The paper's §4.4.1 prose equates 0.90 precision with 10% FPR; those quantities are not interchangeable. Its §5.3 batch-count wording is also insufficiently clear to reconstruct a confusion matrix. Neither claim is used as a target score.

## Reproduce and inspect

Extract `phishir-synthetic-v1.zip`, open a terminal in its extracted folder, and run:

```text
python3 generate_and_score.py
```

The generator makes no network calls and writes outputs beside itself. It deterministically reconstructs data and re-runs all baselines. Dependencies and actual run versions are recorded in `requirements.txt` and `manifest.json`; use an environment with these dependencies available. Logistic regression uses seed 172289201; no random generative model is involved.

The archive includes:

- `generate_and_score.py`, `requirements.txt`: complete generation, split, assertion and scoring implementation.
- `dataset.jsonl`, `schema.json`: nested records and JSON Schema, with field descriptions and label enums.
- `classification.csv`: flat email-input and label export for easy loading; nested spans remain in JSONL.
- `baseline_scores.csv`, `family_scores.csv`: validation/test classification metrics and per-family word-model audit.
- `response_scores.csv`, `policy_scores.json`, `entity_scores.json`: containment-only, four-way policy and exact-span results.
- `predictions.csv`: individual validation/test email decisions for all four baselines.
- `manifest.json`: counts, software versions, checks and SHA256 hashes for tabular/data outputs.
- `README.md`: this dataset card and paper-to-benchmark mapping.

## What this cannot establish

This is suitable for pipeline wiring, regression tests, label-policy discussion and exposing obvious failure modes. It is **not a publishable external validation set**. Test has only **two independent lure families**, 40 base email templates exist overall, and repeated endpoint wording, explicit benign cues and synthetic formatting create shortcuts. Full-text uniqueness is mostly surface/context variation. Do not attach row-bootstrap confidence intervals to claim broad generalization.

Only English text, one endpoint event per snapshot, no mail authentication headers, no real attachments, no image interpretation, no obfuscated hashes, no subtle endpoint evidence or ambiguous adjudication. Positive correlation windows are 5–29 minutes and stale events 1,440 minutes; boundary cases near 60 minutes are absent. The 50/50 email class balance and 20% containment prevalence are constructed, not production estimates. No latency, MTTR improvement, SOC workload reduction, real false-action rate or comparison with DistilBERT is measured.

Before scientific evaluation: obtain licensed independent real-world email/incident examples; expert-adjudicate ambiguous labels; add campaign/time/source holdouts, more independent wording families, noisy telemetry and near-boundary timing tests. Keep any future test set sealed until evaluation; this released development set is now visible and should not be treated as hidden.
