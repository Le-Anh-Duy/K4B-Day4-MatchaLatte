"""Smoke tests for the two team-built IT Helpdesk bonus tools.

Run: python test_bonus_tools.py
"""
from __future__ import annotations

from pathlib import Path

from tools import TOOL_FUNCTIONS
from tools.check_software_license.tool import check_software_license
from tools.unlock_user_account import tool as unlock_module


def main() -> None:
    licensed = check_software_license("EMP-1001", "Office")
    assert licensed["entitled"] is True
    assert licensed["software"] == "Microsoft 365"
    assert licensed["available_seats"] == 18

    unlicensed = check_software_license("EMP-1002", "Adobe")
    assert unlicensed["entitled"] is False
    assert unlicensed["license_status"] == "not_assigned"
    assert check_software_license("EMP-9999", "Zoom")["error"] == "employee_not_found"
    assert check_software_license("EMP-1001", "Unknown App")["error"] == "software_not_found"

    assert unlock_module.unlock_user_account("EMP-1003", "sso", False)["status"] == "needs_confirmation"
    assert unlock_module.unlock_user_account("EMP-1001", "sso", True)["error"] == "account_not_locked"
    assert unlock_module.unlock_user_account("EMP-1003", "email", True)["error"] == "unsupported_system"
    assert unlock_module.unlock_user_account("EMP-9999", "sso", True)["error"] == "employee_not_found"

    unlocked = unlock_module.unlock_user_account("EMP-1003", "sso", True)
    action_path = Path(unlocked["path"])
    try:
        assert unlocked["status"] == "unlocked"
        assert unlocked["new_status"] == "active"
        assert action_path.is_file()
    finally:
        action_path.unlink(missing_ok=True)

    assert TOOL_FUNCTIONS["check_software_license"] is check_software_license
    assert TOOL_FUNCTIONS["unlock_user_account"] is unlock_module.unlock_user_account
    print("ok: bonus license lookup and confirmed account unlock")


if __name__ == "__main__":
    main()
