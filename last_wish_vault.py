# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import json
import re
from dataclasses import dataclass
from genlayer import *


@allow_storage
@dataclass
class VaultRecord:
    id: str
    owner: str
    beneficiary: str
    heartbeat_endpoint: str
    expected_secret_token: str
    vault_deposit: u256
    released_amount: u256
    quality_score: u256
    grace_period_days: u256
    last_heartbeat_timestamp: str
    status: str
    last_audit_summary: str


class LastWishVault(gl.Contract):
    operator: str
    vaults: TreeMap[str, VaultRecord]
    next_vault_id: u256
    total_locked_pool: u256

    def __init__(self, operator: str):
        self.operator = operator.strip().strip('"').strip("'").lower()
        # GenLayer VM automatically instantiates storage-backed TreeMaps.
        # We must never assign TreeMap() manually in the constructor.
        self.next_vault_id = u256(0)
        self.total_locked_pool = u256(0)

    @gl.public.write
    def create_vault(
        self,
        beneficiary: str,
        heartbeat_endpoint: str,
        expected_secret_token: str,
        deposit_amount: int,
        grace_period_days: int = 7
    ) -> str:
        sender = str(gl.message.sender_address).lower()
        ben_clean = beneficiary.strip().strip('"').strip("'").lower()
        endpoint_clean = heartbeat_endpoint.strip().strip('"').strip("'").lower()
        secret_clean = expected_secret_token.strip().strip('"').strip("'")

        # Sanitize endpoint removing protocol prefixes if present
        if endpoint_clean.startswith("https://"):
            endpoint_clean = endpoint_clean[8:]
        elif endpoint_clean.startswith("http://"):
            endpoint_clean = endpoint_clean[7:]
        endpoint_clean = endpoint_clean.split("/")[0].strip()

        assert len(ben_clean) >= 10, "Invalid beneficiary address."
        assert len(endpoint_clean) > 3 and "." in endpoint_clean, "Invalid heartbeat endpoint."
        assert len(secret_clean) >= 3, "Expected secret token cannot be empty."
        assert deposit_amount > 0, "Vault deposit amount must be > 0."
        assert grace_period_days >= 1, "Grace period must be at least 1 day."

        v_num = int(self.next_vault_id) + 1
        self.next_vault_id = u256(v_num)
        v_id = "VAULT_" + str(v_num)

        staked = u256(deposit_amount)
        self.total_locked_pool = self.total_locked_pool + staked

        new_vault = VaultRecord(
            id=v_id,
            owner=sender,
            beneficiary=ben_clean,
            heartbeat_endpoint=endpoint_clean,
            expected_secret_token=secret_clean,
            vault_deposit=staked,
            released_amount=u256(0),
            quality_score=u256(100),
            grace_period_days=u256(grace_period_days),
            last_heartbeat_timestamp="2026-07-01",
            status="FUNDED_ACTIVE",
            last_audit_summary=f"LastWish succession vault initialized with {deposit_amount} tokens. Beneficiary: {ben_clean}. Grace period: {grace_period_days} days."
        )

        self.vaults[v_id] = new_vault
        return v_id

    @gl.public.write
    def audit_liveness_heartbeat(self, vault_id: str) -> None:
        assert vault_id in self.vaults, "Vault ID does not exist."

        vault = self.vaults[vault_id]
        sender = str(gl.message.sender_address).lower()

        # Access Control Guardrail: Only owner, beneficiary, or operator can trigger audit
        assert sender == vault.owner or sender == vault.beneficiary or sender == self.operator, \
            "Unauthorized: caller must be vault owner, beneficiary, or operator."

        assert vault.status in ("FUNDED_ACTIVE", "GRACE_PERIOD"), "Vault is not in auditable liveness status."
        assert int(vault.vault_deposit) > 0, "Vault has no locked funds."

        endpoint = vault.heartbeat_endpoint
        secret_token = vault.expected_secret_token

        # Derive live HTTP JSON probe URL from stored endpoint
        probe_url = "https://dns.google/resolve?name=" + endpoint + "&type=TXT"

        def get_input() -> str:
            web_data = gl.nondet.web.render(probe_url, mode="text")
            return (
                f"Live Liveness Heartbeat Probe API Response for Target Endpoint '{endpoint}':\n\n"
                f"{web_data}\n\n"
                f"Expected Secret Heartbeat Token: '{secret_token}'"
            )

        task = (
            "You are a Senior Decentralized Liveness & Succession Auditor for dead man's switch vaults.\n"
            "Parse the live network heartbeat probe response provided in the input.\n\n"
            "Your job:\n"
            "1. Inspect response status and check if endpoint is reachable.\n"
            "2. Inspect if expected secret heartbeat token or valid DNS records are present.\n"
            "3. If reachable and valid token/record found: set liveness_verified=true, quality_score=100.\n"
            "4. If unreachable or invalid: set liveness_verified=false, quality_score=0.\n\n"
            "Classify status_tier:\n"
            "- If liveness_verified is TRUE: status_tier = FUNDED_ACTIVE\n"
            "- If liveness_verified is FALSE: status_tier = SUCCESSION_READY\n\n"
            "Output JSON format:\n"
            "{\n"
            '  "endpoint_reachable": true/false,\n'
            '  "liveness_verified": true/false,\n'
            '  "quality_score": <integer score 0 to 100>,\n'
            '  "status_tier": "<FUNDED_ACTIVE or SUCCESSION_READY>",\n'
            '  "summary": "<brief liveness audit sentence>"\n'
            "}\n"
            "Respond ONLY with raw JSON."
        )

        criteria = (
            "Graduated Liveness Equivalence Rule:\n"
            "1. Strict Part: status_tier (FUNDED_ACTIVE vs SUCCESSION_READY) MUST match 100% exactly across all validators.\n"
            "2. Fuzzy Part: quality_score (0 to 100) must match within a bounded tolerance of +-5 points within the same status_tier.\n"
            "Independently parse the heartbeat response yourself. "
            "REJECT the leader's proposal if: "
            "(1) the proposed status_tier is inconsistent with endpoint liveness in EITHER direction (reporting ACTIVE when dead/offline or reporting SUCCESSION_READY when live), "
            "(2) the proposed quality_score straddles a tier boundary or deviates by more than +-5 points, "
            "(3) the proposed liveness_verified boolean is false when valid endpoint response data exists, or "
            "(4) the leader claims endpoint_reachable=false when valid response is present. "
            "The output must be valid JSON with keys: endpoint_reachable, liveness_verified, "
            "quality_score, status_tier, and summary."
        )

        consensus_result = gl.eq_principle.prompt_non_comparative(
            get_input,
            task=task,
            criteria=criteria
        )

        # Clean thinking blocks and markdown wrappers
        raw_json = consensus_result.strip()
        if "</think>" in raw_json:
            raw_json = raw_json.split("</think>")[-1].strip()
        if raw_json.startswith("```"):
            lines = raw_json.split("\n")
            if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
                raw_json = "\n".join(lines[1:-1]).strip()
            else:
                raw_json = raw_json.replace("```json", "").replace("```", "").strip()

        result = json.loads(raw_json)
        reachable = bool(result.get("endpoint_reachable", False))
        liveness = bool(result.get("liveness_verified", False))
        score_val = int(result.get("quality_score", 0))
        summary = str(result.get("summary", ""))

        assert reachable == True, "Failed to reach target heartbeat endpoint."

        if liveness and score_val >= 70:
            # Heartbeat verified alive -> Reset to FUNDED_ACTIVE
            vault.status = "FUNDED_ACTIVE"
            vault.quality_score = u256(score_val)
            vault.last_audit_summary = f"HEARTBEAT VERIFIED LIVE (Score: {score_val}/100): Vault remains active. " + summary
        else:
            # Heartbeat failed -> Transition to SUCCESSION_READY
            vault.status = "SUCCESSION_READY"
            vault.quality_score = u256(score_val)
            vault.last_audit_summary = f"HEARTBEAT FAILED / INACTIVE (Score: {score_val}/100): Succession ready for claim by beneficiary {vault.beneficiary}. " + summary

        self.vaults[vault_id] = vault

    @gl.public.write
    def claim_succession(self, vault_id: str) -> None:
        assert vault_id in self.vaults, "Vault ID does not exist."

        vault = self.vaults[vault_id]
        sender = str(gl.message.sender_address).lower()

        # Access Control: Only designated beneficiary can claim succession funds
        assert sender == vault.beneficiary or sender == self.operator, \
            "Only designated beneficiary or operator can claim succession payout."
        assert vault.status == "SUCCESSION_READY", "Vault status is not SUCCESSION_READY."
        assert int(vault.vault_deposit) > 0, "No locked funds available in vault."

        claim_amount = int(vault.vault_deposit)
        if int(self.total_locked_pool) >= claim_amount:
            self.total_locked_pool = u256(int(self.total_locked_pool) - claim_amount)

        vault.released_amount = u256(claim_amount)
        vault.vault_deposit = u256(0)
        vault.status = "CLAIMED_RELEASED"
        vault.last_audit_summary = f"Succession payout of {claim_amount} tokens successfully claimed by beneficiary {sender}."

        self.vaults[vault_id] = vault

    @gl.public.write
    def reclaim_vault(self, vault_id: str) -> None:
        assert vault_id in self.vaults, "Vault ID does not exist."

        vault = self.vaults[vault_id]
        sender = str(gl.message.sender_address).lower()

        # Access Control: Only vault owner can reclaim funds
        assert sender == vault.owner, "Only vault owner can reclaim funds."
        assert vault.status in ("FUNDED_ACTIVE", "GRACE_PERIOD", "SUCCESSION_READY"), \
            "Vault cannot be reclaimed in current status."
        assert int(vault.vault_deposit) > 0, "No locked funds available to reclaim."

        reclaim_amount = int(vault.vault_deposit)
        if int(self.total_locked_pool) >= reclaim_amount:
            self.total_locked_pool = u256(int(self.total_locked_pool) - reclaim_amount)

        vault.vault_deposit = u256(0)
        vault.status = "RECLAIMED_CANCELLED"
        vault.last_audit_summary = f"Vault funds of {reclaim_amount} tokens successfully reclaimed by owner {sender}."

        self.vaults[vault_id] = vault

    @gl.public.view
    def get_vault(self, vault_id: str) -> VaultRecord:
        assert vault_id in self.vaults, "Vault ID does not exist."
        return self.vaults[vault_id]

    @gl.public.view
    def is_succession_ready(self, vault_id: str) -> bool:
        assert vault_id in self.vaults, "Vault ID does not exist."
        return self.vaults[vault_id].status == "SUCCESSION_READY"

    @gl.public.view
    def get_total_locked_pool(self) -> u256:
        return self.total_locked_pool

    @gl.public.view
    def get_total_vaults(self) -> u256:
        return self.next_vault_id
