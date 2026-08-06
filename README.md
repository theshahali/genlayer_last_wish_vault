# LastWish Vault — Liveness-Verified Succession Vault (Dead Man's Switch)

An Intelligent Contract primitive built on **GenLayer** for automated estate succession, liveness verification, and dead man's switch asset claims, grounded in capability-specific live endpoint probing.

---

## 📖 Overview

The `LastWishVault` allows account holders to lock assets into a succession vault that periodically probes a live heartbeat endpoint. If the account owner remains active and responsive, the vault remains `FUNDED_ACTIVE`. If the heartbeat endpoint becomes unresponsive or invalid across the grace period, the contract transitions to `SUCCESSION_READY`, unlocking the funds for claim by the designated `beneficiary`.

---

## 🛠️ Named Equivalence Rule: Graduated Liveness Consensus

Consensus splits judgment into strict and fuzzy parts:
1. **Strict Part**: The `status_tier` (`FUNDED_ACTIVE` vs `SUCCESSION_READY`) MUST match 100% exactly across all consensus validators because it directly mutates on-chain succession state.
2. **Fuzzy Part**: The `quality_score` (0–100) must match within a bounded tolerance of $\pm 5$ points within the same status tier. Scores straddling a tier boundary (e.g. 69 vs 70) are explicitly rejected.

---

## ⚙️ Lifecycle State Machine

- `FUNDED_ACTIVE`: Vault funded by owner; liveness probe verified intact.
- `GRACE_PERIOD`: Pending liveness re-probe during grace window.
- `SUCCESSION_READY`: Inactivity verified by consensus nodes; beneficiary claim unlocked.
- `CLAIMED_RELEASED`: Succession funds claimed by designated beneficiary.
- `RECLAIMED_CANCELLED`: Vault deposit reclaimed by original owner.

---

## 🚀 How to Test in GenLayer Studio

1. **Deploy Contract**: Deploy `LastWishVault` with your wallet address as `operator`.
2. **Create Vault**: Call `create_vault`:
   * `beneficiary`: `"0x5c48c6f77617fc05761433cc4019a79b47d1ec7d"`
   * `heartbeat_endpoint`: `"google.com"`
   * `expected_secret_token`: `"v=spf1"`
   * `deposit_amount`: `10000`
   * `grace_period_days`: `7`
   > *Returns: `"VAULT_1"`*
3. **Audit Heartbeat**: Call `audit_liveness_heartbeat("VAULT_1")`.
4. **Inspect Status**: Call `get_vault("VAULT_1")`.
5. **Claim Succession**: Call `claim_succession("VAULT_1")` (as beneficiary).
