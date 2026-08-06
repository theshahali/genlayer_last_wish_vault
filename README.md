# Liveness Attestation & Dead Man's Switch Decision Oracle

An Intelligent Contract decision primitive built on **GenLayer** for automated estate succession decision gates, liveness attestation, and dead man's switch status verdicts, grounded in capability-specific live endpoint probing.

---

## 📖 Overview

The `LastWishVault` decision oracle allows account holders to register a liveness decision gate that periodically probes a live heartbeat endpoint. Rather than holding unbacked token deposits, it substantively binds live endpoint responsiveness and secret token verification to produce on-chain decision verdicts (`ACTIVE_LIVE` $\rightarrow$ `GRACE_PERIOD_WARNING` $\rightarrow$ `SUCCESSION_READY_INACTIVE`).

---

## 🛠️ Graduated Liveness Equivalence Rule

Consensus splits judgment into strict and fuzzy parts:
1. **Strict Part**: The `liveness_verified` boolean MUST match 100% exactly across all consensus validators because it directly mutates on-chain decision states.
2. **Fuzzy Part**: The `quality_score` (0–100) must match within a bounded tolerance of $\pm 5$ points.

---

## ⚙️ Multi-Step Grace Period State Machine Flow

- `ACTIVE_LIVE`: Heartbeat probe verified intact; liveness attested.
- `GRACE_PERIOD_WARNING`: 1st heartbeat failure recorded; vault enters grace warning window without triggering immediate succession.
- `SUCCESSION_READY_INACTIVE`: Confirmed inactivity across grace window; succession decision unlocked.

---

## 🚀 How to Test in GenLayer Studio

1. **Deploy Contract**: Deploy `LastWishVault` with your wallet address as `operator`.
2. **Create Vault Gate**: Call `create_vault`:
   * `beneficiary`: `"0x5c48c6f77617fc05761433cc4019a79b47d1ec7d"`
   * `heartbeat_endpoint`: `"google.com"`
   * `expected_secret_token`: `"v=spf1"`
   * `grace_period_days`: `7`
   > *Returns: `"VAULT_1"`*
3. **Audit Heartbeat**: Call `audit_liveness_heartbeat("VAULT_1")`.
4. **Inspect Status**: Call `get_vault("VAULT_1")`.
