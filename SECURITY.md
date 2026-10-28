# Security and disclosure

This is local research software, with no hosted service, credentials, telemetry, or AI API integration. Bundled inputs are synthetic. Use an approved environment and institution-approved dependency process for any real-data evaluation. Never upload private records to public issues, this repository, or an external assistant.

Report a vulnerability privately using GitHub's private vulnerability reporting when enabled. If that channel is unavailable, open an issue containing only a request for a private reporting channel, with no exploit, private dataset, credential, or identifying record.

## Threat and trust boundaries

| Boundary | Implemented defense | Residual limitation |
| --- | --- | --- |
| Structured input | Exact fields, finite normalized values, opaque identifiers, UTC chronology | No semantic verification that upstream assertions are true |
| Policy | Declarative comparisons, allowlisted feature registry, bounded groups, no eval | An authorized policy author can choose poor weights or mappings |
| SQLite writes | Parameters, foreign-key entity linkage, atomic ingestion, collision rejection | Database owner can modify files; local file ACL/encryption is host-owned |
| Assessment runs | Single transaction freezes each batch; complete-only exports | One writer; lock duration scales with portfolio. Not a distributed execution service |
| Review history | Append-only SQL triggers and content-linked hash chain | No authenticated identity, RBAC service, external notarization or signature |
| Offline HTML | Embedded synthetic data, text rendering, no network libraries | Anyone with the HTML can read every embedded example; not a secure data viewer |
| Model artifacts | Numeric JSON logistic artifact; no pickle loading | Unsupported external artifact formats must not be loaded by ad hoc extensions |
| Dependencies | Reproducible lockfile and CI checks | Dependency approval and vulnerability monitoring remain adopter responsibilities |

Reversals, deduplication across multiple economic-event identifiers, currency conversion, and source authentication belong in a validated adapter. Do not coerce a rejected record into a benign default to get a batch through.
