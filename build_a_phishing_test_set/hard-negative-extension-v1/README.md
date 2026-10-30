# Hard-negative extension v1

## Added challenge

**40 synthetic non-phishing hard negatives + 40 matched phishing controls**, covering 20 scenario families with two independently authored wording variants per family. This is a new `hard_negative_challenge` split, not additional training data. The original 800/100/100 synthetic splits and 100 public emails remain unchanged.

Each pair shares its subject and business/security topic but changes the action requested. This tests whether a classifier distinguishes legitimate handling of a sensitive task from disclosure of secrets, bypass of safeguards or deceptive financial redirection. The scenarios were authored before scoring this challenge; failed cases were not mined or cherry-picked using the models' predictions.

| Scenario group | Included families |
|---|---|
| Identity and account access | Self-initiated resets; first-party MFA number matching; security-driven credential rotation |
| QR and business workflows | Facilities QR; existing vendor workspace; contract signing; expected bank statements; secure-mail messages; expected deliveries |
| Financial authorization | Supplier callback verification; payroll callback approval; normal executive-purchase controls |
| Administrative activity | Managed VPN deployment; controlled signed macro workbooks; approved PowerShell inventory jobs |
| Quoted or non-actionable content | Security warnings quoting attacks; forwarded samples for SOC triage; awareness exercises; inert IOC bulletins |
| Non-phishing marketing | Public promotions or unwanted mail without credential/payment harvesting; generic spam is not promoted to a phishing-positive label |

These are authored scenario families, not verified real-world campaigns. “Hard” describes the intended lexical/semantic confound, not proof that every example defeats every model. Some legitimate messages explicitly state safety or approval context, and several share broad topics with the original training set.

## Measured baseline results

Models were refit using exactly the original **800 synthetic training emails**, original feature settings and seed 172289201. Only `email_text` was supplied as a feature. No challenge examples, labels or rationales were used for training, calibration, feature selection or threshold tuning. Earlier synthetic-test and public-holdout confusion counts were reproduced unchanged.

| Baseline | New false positives / 40 negatives | FPR | Phishing recall | F1 on all 80 | Both pair members correct |
|---|---:|---:|---:|---:|---:|
| Always benign | 0 | .000 | .000 | .000 | .000 |
| Fixed keyword rule | 9 | .225 | .700 | .727 | .475 |
| Word TF-IDF + logistic regression | **11** | **.275** | 1.000 | .879 | .725 |
| Character TF-IDF + logistic regression | **15** | **.375** | .850 | .764 | .500 |

**Failure concentration:** Both learned models flag all benign variants in MFA number matching, security warnings quoting an attacker, and forwarded samples for SOC review (2/2 negatives in each family). The character model also flags both inert IOC bulletins. These are good regression targets for quote handling, action attribution and first-party-versus-third-party authentication context.

The always-benign baseline illustrates why a low FPR is insufficient: it detects none of the malicious controls. Pair success requires both the benign and malicious member to be correct, penalizing a model that assigns the same verdict to a whole topic. No confidence interval is claimed from this small, authored set with correlated variants. **DistilBERT was not run; no transformer score is implied.**

## Labels and schema

- **`phishing_label=0`:** Constructed non-phishing request or informational message. An optional/unwanted marketing notice can be non-phishing without being a desirable message or suitable for automatic delivery.
- **`phishing_label=1`:** Constructed malicious social-engineering request, including credential/MFA theft, deceptive financial diversion and unsafe software-execution lures. Generic spam alone is not positive evidence.
- **`negative_rationale`, `lexical_cue`, `family_id`, `pair_id`, `wording_variant`:** Gold explanation or audit metadata. Never pass these fields to a classifier. The rationale explains the benign member and is deliberately attached to both members rather than exposing a label-specific input field.
- **Unknown context:** `endpoint_state`, `correlated_compromise`, `response_label`, `entities` and `campaign_id` are null. Email classification does not establish host compromise or authorization for containment. This extension adds no invented endpoint evidence or entity annotations.

The bundled schema adds a third record variant to the existing synthetic/public schema; older contracts are not weakened. The entire new split stays outside training. Pairs must remain together if the challenge is later reorganized. It is not a sealed future test set now that its texts and errors are visible.

## Deliverables and reproduction

- `hard_negatives.csv` — the 40 non-phishing examples, with construction rationale and pairing metadata.
- `challenge.jsonl` — all 80 paired records, including malicious controls.
- `baseline_scores.csv` — 12 rows: four baselines × original synthetic test, public holdout and new challenge. Includes FPR, confusion counts and challenge pair success.
- `hard_negative_extension.zip` — all of the above plus the full **1,180-record `augmented_dataset_v3.jsonl`**, extended schema, scenario specification, generator/scorer, per-example predictions, per-family scores, manifest, pinned dependency versions and the public data attribution/card.

Extract the archive into its own directory and run `python3 generate_and_score.py` with NumPy and scikit-learn available. No downloads, LLM, GPU or transformer model is needed. `scenarios.json` contains all scenario texts; change that specification to add cases, then regenerate. The base dataset and schema are included so reproduction does not depend on another workspace path.

Checks run: 80 unique challenge texts, exactly 40 balanced pairs, no normalized exact match against the preceding 1,100 records, all rows preserving the old base prefix, schema-variant validity, deterministic repeated generation/scoring and archive CRC. Exact deduplication is not semantic independence or campaign decontamination.

The existing DistilBERT runner has a pinned **1,100-record** input contract. This 1,180-record export intentionally does not silently replace that input or alter its contract; its runner needs an explicit additional evaluation split before it can score this challenge. Earlier artifacts remain available unchanged.

## Safety, provenance and limits

All new messages are fictional authored text. The demonstration MFA number is not a real credential; the only destination is an inert, defanged `.example` URL. There are no attachments, live endpoints, executable payloads or operational actions. The archive's public base records retain the earlier licensing, privacy and source/class-confounding caveats; see `PUBLIC_DATA_CARD.md` and `ATTRIBUTION.md` inside it.

Labels represent construction intent, not independent analyst adjudication. Two wordings per family are more varied than identifier-only substitutions but still limited. Quote boundaries, explicit approval claims and 'existing portal' wording can themselves become shortcuts. A real attacker can falsely claim authorization; these messages do not cryptographically verify a sender or change ticket. Assess real-world authorization with telemetry and trusted context rather than treating safety language as proof. This is a development/regression challenge, not a deployment approval dataset.
