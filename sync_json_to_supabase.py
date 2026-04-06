from __future__ import annotations

import json
import os
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

from supabase import create_client

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "monthly_tracker_data.json"
SECRETS_FILE = BASE_DIR / ".streamlit" / "secrets.toml"


def load_supabase_credentials() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()

    if url and key:
        return url, key

    if tomllib is not None and SECRETS_FILE.exists():
        with open(SECRETS_FILE, "rb") as file:
            secrets = tomllib.load(file)
        supabase = secrets.get("supabase", {})
        url = str(supabase.get("url", "")).strip()
        key = str(supabase.get("key", "")).strip()

    if not url or not key or "YOUR_PROJECT_ID" in url or "YOUR_ANON_KEY" in key:
        raise RuntimeError(
            "Supabase credentials are missing. Set SUPABASE_URL and SUPABASE_KEY, "
            "or update .streamlit/secrets.toml with real values."
        )

    return url, key


def load_local_payload() -> dict:
    if not DATA_FILE.exists():
        raise RuntimeError(f"Local data file not found: {DATA_FILE}")

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        raise RuntimeError("Local JSON must contain a top-level object.")

    payload.setdefault("budgets", {})
    payload.setdefault("transactions", [])
    payload.setdefault("savings_goals", {})
    return payload


def upload_payload(payload: dict) -> None:
    url, key = load_supabase_credentials()
    client = create_client(url, key)
    client.table("tracker_data").upsert({"id": 1, "payload": payload}).execute()


def main() -> None:
    payload = load_local_payload()
    upload_payload(payload)
    print("Uploaded local JSON to Supabase")
    print(f"Budgets: {len(payload.get('budgets', {}))}")
    print(f"Transactions: {len(payload.get('transactions', []))}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Upload failed: {exc}")
        raise SystemExit(1)
