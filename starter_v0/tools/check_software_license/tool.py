from __future__ import annotations

import json
from typing import Any

from tools._shared import ROOT, err, fold_text


LICENSE_FILE = ROOT / "helpdesk_data" / "software_licenses.json"
USER_FILE = ROOT / "helpdesk_data" / "users.json"


def check_software_license(employee_id: str = "", software: str = "") -> dict[str, Any]:
    tool_name = "check_software_license"
    if not isinstance(employee_id, str) or not employee_id.strip():
        return {"tool": tool_name, "error": "missing_employee_id"}
    if not isinstance(software, str) or not software.strip():
        return {"tool": tool_name, "error": "missing_software"}
    try:
        employee_key = employee_id.strip().upper()
        users = json.loads(USER_FILE.read_text(encoding="utf-8"))
        if not any(user["employee_id"] == employee_key for user in users["users"]):
            return {"tool": tool_name, "employee_id": employee_key, "error": "employee_not_found"}

        data = json.loads(LICENSE_FILE.read_text(encoding="utf-8"))
        wanted = fold_text(software.strip())
        product = next((item for item in data["catalog"] if wanted in {
            fold_text(item["software"]), *(fold_text(alias) for alias in item.get("aliases", []))
        }), None)
        if product is None:
            return {
                "tool": tool_name,
                "software": software.strip(),
                "error": "software_not_found",
                "available_software": [item["software"] for item in data["catalog"]],
            }

        assignment = next((item for item in data["assignments"]
                           if item["employee_id"] == employee_key and item["software"] == product["software"]), None)
        status = assignment["status"] if assignment else "not_assigned"
        return {
            "tool": tool_name,
            "employee_id": employee_key,
            "software": product["software"],
            "entitled": status == "active",
            "license_status": status,
            "expires_at": product["expires_at"],
            "available_seats": max(0, product["total_seats"] - product["assigned_seats"]),
            "snapshot_at": data["snapshot_at"],
        }
    except Exception as exc:
        return err(tool_name, exc)
