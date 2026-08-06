# System Design & Security Model — LastWish Vault

## 1. System State Diagram

```
 [ Owner Deposits ] ──> FUNDED_ACTIVE ───(Heartbeat Fails)───> SUCCESSION_READY ───(Beneficiary Claim)───> CLAIMED_RELEASED
                             │                                     │
                             ├───(Owner Reclaim)──────────┐        ├───(Owner Reclaim)
                             ▼                            ▼        ▼
                    RECLAIMED_CANCELLED <─────────────────┴────────┘
```

---

## 2. Security & Equivalence Model

### Bidirectional Validator Consensus ("Graduated Liveness Equivalence")
Validators independently fetch the live network response from the target endpoint via `gl.nondet.web.render()`. 

Proposals are rejected if:
1. The proposed `status_tier` is inconsistent with endpoint liveness in EITHER direction (reporting `FUNDED_ACTIVE` when offline, or reporting `SUCCESSION_READY` when online).
2. The proposed `quality_score` straddles a tier boundary or deviates by more than $\pm 5$ points.
3. The leader claims `endpoint_reachable=false` when valid response data is present.

---

## 3. Access Control Architecture

- `create_vault`: Owner address captured automatically via `gl.message.sender_address`.
- `claim_succession`: Strictly restricted to `sender == vault.beneficiary or sender == self.operator`.
- `reclaim_vault`: Strictly restricted to `sender == vault.owner`.
