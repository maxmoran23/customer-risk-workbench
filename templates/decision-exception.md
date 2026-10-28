# Decision and exception record

**Status: synthetic worked record; no approval or operational exception is granted.** Preserve the original assessment separately.

## Worked situation

A synthetic assessment has `score=null`, provisional index `22`, and bounds `[22,28]`. One optional factor is unavailable, but the interval lies in one illustrative band. A reviewer may decide to request evidence or conduct a scoped manual review. They must not rewrite the score to `22` and describe it as fully observed.

| Field | Required content |
| --- | --- |
| Decision ID | Unique opaque reference |
| Assessment reference | Exact assessment hash, customer ID, cutoff, policy hash |
| Requested action | Concrete review action within the authorized scope |
| Reason | Facts and evidence supporting the action |
| Unresolved information | Missing factors, source issues, assumptions |
| Requester and reviewer | Actual accountable identities in approved environment |
| Decision time | Timezone-aware timestamp |
| Validity/expiry | Explicit period or event trigger |
| Supersession | Previous decision reference and reason, preserving history |

## Exception analysis

| Question | Worked interpretation |
| --- | --- |
| What is being excepted? | No exception is needed merely to acknowledge an incomplete bounded band; an exception would need a specific control/use being bypassed |
| What remains unknown? | The missing optional factor and any source-quality limitation |
| What cannot be changed by approval? | Historical evidence availability, arithmetic result, or legal obligations |
| What is the compensating control? | Defined additional review with evidence and accountable owner, if authorized |
| What ends the exception? | Expiry, evidence arrival, changed risk, or explicit superseding decision |

## Screening boundary

An unresolved screening route must be handled through the separate authorized screening process. A customer-risk exception cannot clear a hit, determine a license, or change a legal disposition. `FALSE` and `UNKNOWN` route values are also not clearance statements.

## Recording and integrity

Store the decision alongside, not inside, the original calculation. A later record can supersede an earlier decision without deleting it. Application-level append behavior alone does not provide authenticated approval or tamper-proof storage; adopting controls must establish those properties where needed.

**Current decision: not made.** Required completion evidence: actual authority, supporting documents, timestamp, conditions, expiry, and record-integrity control.
