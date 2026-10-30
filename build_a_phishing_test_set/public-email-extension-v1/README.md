# Public-email extension v1

## Added data

**100 historical public-email records: 50 source-labeled phishing positives and 50 source-labeled non-spam negatives.** They form a new `public_holdout`, separate from all synthetic training, validation and test records. `augmented_dataset.jsonl` contains the original 1,000 records unchanged, followed by these 100 public records. The original v1 deliverables are not overwritten.

| Class | Source | Selection and provenance |
|---|---|---|
| 1: phishing | Jose Nazario, original 2021 phishing mailbox, https://monkey.org/~jose/phishing/phishing-2021 | Original mailbox corpus membership, excluding internal metadata messages, empty/oversized text and ten conservatively screened entries. The host describes hand classification with possible errors. |
| 0: non-phishing proxy | Enron.csv in Champa's *Phishing Email Curated Datasets*, https://doi.org/10.5281/zenodo.8339691 | Only rows with the curator's `label=0` (non-spam) from the first 2 MiB. Generic spam rows (`label=1`) are never treated as phishing. Non-spam is a source label, not a new independent security adjudication. |

The original paper's requested DOI is https://doi.org/10.22541/au.177446759.98281679/v1. Public records extend its **email classification** task only. There is no invented endpoint telemetry, compromise truth, containment label or expert IOC annotation for these historical messages.

## Results: frozen synthetic-trained baselines

Both learned baselines were refit with exactly the original v1 specifications on **only the 800 synthetic training emails**. No public training examples, threshold tuning or public-test-driven hyperparameter search was used. All features come only from `email_text`; source, label, record ID and duplicate-group metadata are excluded. This is transfer evaluation, not a claim that these simple models are the best models for the public data.

| Baseline | Synthetic-test F1 | Public F1 | Public precision | Public recall | Public FPR | Public TN / FP / FN / TP |
|---|---:|---:|---:|---:|---:|---|
| Always benign | .000 | .000 | .000 | .000 | .000 | 50 / 0 / 50 / 0 |
| Fixed keyword rule | .000 | .145 | .800 | .080 | .020 | 49 / 1 / 46 / 4 |
| Word TF-IDF + logistic regression | .800 | **.645** | .549 | .780 | .640 | 18 / 32 / 11 / 39 |
| Character TF-IDF + logistic regression | .800 | **.738** | .717 | .760 | .300 | 35 / 15 / 12 / 38 |

Public holdout size is 100, balanced 50/50. Public accuracies are .50, .53, .57 and .73 respectively. FPR is FP/(FP+TN). Undefined positive precision is recorded as zero. No sampling-based uncertainty interval is supplied: records are selected, source-confounded, and not independent known campaigns.

The result exposes a synthetic-to-public distribution gap: the word model incorrectly flags 32/50 source-labeled legitimate emails. It does **not** isolate which part of this gap is due to realism, source formatting, age, redaction, language or topic.

## Selection, grouping and review

- **Bounded retrieval:** Download the complete 2,719,946-byte Nazario 2021 mailbox and exactly the first 2,097,152 bytes of Enron.csv. Drop the final potentially truncated CSV record. Hashes pin those bytes; regeneration stops if the sources change.
- **Usable text:** Decode text MIME parts, prefer plain text to HTML, and extract visible HTML plus anchor targets if no plain part exists. Do not retain attachments. Keep texts between 150 and 16,000 characters after transformations. This intentionally favors text-bearing messages and omits attacks whose evidence lives solely in attachments/images.
- **Conservative review:** Exclude Nazario indices 12, 17, 19, 29, 33, 40, 45, 69, 76 and 87. Reasons include generic money-transfer fraud, apparently legitimate encryption notices, and attachment/transport-dependent evidence that the text export cannot establish. Original source indices are zero-based mailbox record order. Reasons are recorded in the manifest and script. This was an iterative text-level screen, **not blinded expert adjudication**; remaining labels are the source labels.
- **Duplicate proxy:** Across all usable candidates, lowercase; replace URLs and digit sequences; tokenize words. Connect exact normalized matches or TF-IDF word/bigram cosine similarity ≥0.90, using connected components. Exclude components with conflicting class labels. Select one SHA256-ranked representative per component until each class has 50. No selection depends on baseline success/failure.
- **Campaign honesty:** `template_group_id` is only an inferred duplicate/template component. `campaign_id=null` for every public example. These are not verified campaign-separated splits. Related attacks can evade a 0.90 similarity threshold; repeated mailbox themes remain.
- **Synthetic overlap:** No normalized exact text matches against any of the original 1,000 synthetic records. No claim of universal semantic decontamination or absence from model pretraining.

## Transformations and safe handling

Remove selected address/header lines, redact ordinary and spaced/tokenized email addresses, redact long phone-like digit sequences, remove `[SPAM]` subject markers, normalize whitespace and strip residual HTML while retaining discoverable destinations. Defang `http://`/`https://` schemes and `www.` prefixes. These changes apply to both classes. Broad number redaction can alter dates, IPs or numeric URL fragments; this export is not suitable for exact original-IOC extraction.

**This is not guaranteed anonymization.** Historical names, signatures, addresses, domains, path fragments and other identifying text may remain. No raw headers or attachments are packaged. Do not send these messages, activate domains, follow URLs, or import them into a live mail pipeline. Dataset-source download URLs in metadata are intentionally intact. Embedded attack URLs remain inert text with altered schemes; defanging is not proof a domain is harmless.

## Schema and files

`schema.json` uses two explicit alternatives: unchanged synthetic v1 records and public-email records. For public rows, `endpoint_state`, `correlated_compromise`, `response_label`, `entities` and `campaign_id` are **null = unavailable**, not false, benign, no action or an empty annotation set. Do not score public rows for response/NER tasks. Public source labels, source URL, record index, parsed-record checksum, transformations and inferred group are retained.

Deliverables:

- `public_emails.csv`: 100 public rows with transformed email text, binary source label and provenance; nulls are empty CSV cells.
- `augmented_dataset.jsonl`: 1,100 total records, with unchanged v1 splits plus `public_holdout`.
- `baseline_scores.csv`: original synthetic-test and new public-holdout classification scores.
- `schema.json`: machine-readable record types and field descriptions.
- `public-email-extension-v1.zip`: all the above plus `add_public_emails.py`, `dataset.synthetic.jsonl`, `synthetic_schema.json`, `public_records.jsonl`, `predictions.csv`, `source_manifest.json`, `requirements.txt`, this card and `ATTRIBUTION.md`.

Extract the archive into its own directory and run `python3 add_public_emails.py` with the listed dependencies available. The script uses network access solely for the two source downloads, verifies pinned input hashes, reproduces selection and scores, and writes beside itself. It does not send mail, query attack domains, save attachments or execute response actions. The delivered transformed dataset can also be used entirely offline. Source timestamps in the manifest naturally change on regeneration; data selections and scores should not change under the recorded dependency versions.

## Licensing and attribution

Jose Nazario's original host explicitly states **CC BY 4.0**: https://monkey.org/~jose/phishing/README.txt. The Enron curated dataset record declares **CC BY 4.0**: https://zenodo.org/api/records/8339691. Both require attribution, a license link and disclosure of modifications; see `ATTRIBUTION.md` in the archive. This is a record of the publishers' licenses, **not independent clearance of underlying third-party email copyright, privacy or personality rights**, especially for the curated Enron derivative. Review before redistribution beyond this research workspace or sensitive/public use.

The curator requests credit to Arifa I. Champa, Md Fazle Rabbi and Minhaz F. Zibran for their 2024 dataset/analysis work; complete requested reference details are in the attribution file.

## Remaining limits

**Source is perfectly confounded with class**: positives are Nazario 2021, negatives are historical Enron business mail. A model could learn source/style/era rather than phishing intent. The bounded Enron prefix and deterministic selection are not a representative population sample; 50/50 prevalence is artificial. The negative corpus contains tokenized text, and positive messages include some non-English content. Attachments, mail authentication and images are absent. No campaigns are ground-truthed and no independent annotators validated every label.

For a stronger benchmark, collect both classes within each contemporary source, adjudicate ambiguous emails, and establish campaign/time holdouts from real metadata. Keep this visible development holdout separate from a future sealed evaluation set.
