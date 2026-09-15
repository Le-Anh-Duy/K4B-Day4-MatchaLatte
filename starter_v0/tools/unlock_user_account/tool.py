from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from tools._shared import ROOT, err


USER_FILE = ROOT / "helpdesk_data" / "users.json"
ACTION_DIR = ROOT / "account_actions"


def unlock_user_account(
    employee_id: str = "",
    system: str = "sso",
    confirmed: bool = False,
) -> dict[str, Any]:
    tool_name = "unlock_user_account"
    if not isinstance(employee_id, str) or not employee_id.strip():
        return {"tool": tool_name, "error": "missing_employee_id"}
    if not isinstance(system, str):
        return {"tool": tool_name, "error": "invalid_system_type"}
    employee_key = employee_id.strip().upper()
    system_key = (system or "sso").strip().lower()
    if system_key != "sso":
        return {"tool": tool_name, "error": "unsupported_system", "supported_systems": ["sso"]}
    try:
        users = json.loads(USER_FILE.read_text(encoding="utf-8"))
        employee = next((user for user in users["users"] if user["employee_id"] == employee_key), None)
        if employee is None:
            return {"tool": tool_name, "employee_id": employee_key, "error": "employee_not_found"}
        account_status = employee.get("account_status", "unknown")
        if account_status != "locked":
            return {
                "tool": tool_name,
                "employee_id": employee_key,
                "system": system_key,
                "error": "account_not_locked",
                "account_status": account_status,
            }
        if confirmed is not True:
            return {
                "tool": tool_name,
                "status": "needs_confirmation",
                "employee_id": employee_key,
                "system": system_key,
                "message": "Unlock only after the user explicitly confirms this employee ID and SSO system.",
            }

        now = datetime.now(timezone.utc)
        seed = f"{now.isoformat()}|{employee_key}|{system_key}"
        action_id = "UNLOCK-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8].upper()
        payload = {
            "action_id": action_id,
            "employee_id": employee_key,
            "system": system_key,
            "previous_status": account_status,
            "new_status": "active",
            "unlocked_at": now.isoformat(),
            "source": "educational_local_mock",
        }
        ACTION_DIR.mkdir(parents=True, exist_ok=True)
        path = ACTION_DIR / f"{action_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"tool": tool_name, "status": "unlocked", **payload, "path": str(path)}
    except Exception as exc:
        return err(tool_name, exc)
