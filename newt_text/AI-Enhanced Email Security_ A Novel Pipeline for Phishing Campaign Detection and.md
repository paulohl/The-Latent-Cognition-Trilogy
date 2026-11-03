# AI-Enhanced Email Security: A Novel Pipeline for Phishing Campaign Detection and Profiling

## Key details
Tarini Saka, Kami E. Vaniea and Nadin Kökciyan. *ACM Transactions on Internet Technology*, online 25 September 2026. DOI: 10.1145/3848625. The publisher's page returned a 403 to automated retrieval, so the bibliographic record and abstract were checked through OpenAlex and the ACM just-accepted listing surfaced in search.

## Links
- [Publisher page](https://doi.org/10.1145/3848625)

## Summary
The paper proposes a three-part phishing-email response pipeline: a fine-tuned language model extracts contextual features, community-detection algorithms group related phishing emails into candidate campaigns, and campaign profiles summarize attacks for analysts. Its abstract describes the system as a complement to SOC staff, not a replacement. The accessible abstract does not give enough information to validate reported detection or analyst-efficiency gains, and it does not establish that the campaign groups are independently adjudicated ground truth.

## Why it matters to you
Your *Transforming Incident Response* study combines classification, threat-intelligence extraction and response workflow. Your newer benchmark artifacts explicitly distinguish a phishing campaign from a synthetic template family and refuse to label generic spam as a phishing positive. This paper provides a concrete alternative for how to connect email classification to campaign grouping and analyst-facing profiles. The useful comparison is whether its inferred communities represent verified campaigns and what review or response decisions they enable, rather than treating an email-level F1 score as an incident-response outcome. Its feature-extraction and clustering stages also offer a reference point for describing which stages your current benchmark actually measures.