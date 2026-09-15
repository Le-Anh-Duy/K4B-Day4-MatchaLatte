---
name: check_software_license
track: bonus
kind: local_inventory
provider: mock_license_inventory
requires_env: []
inputs: [employee_id, software]
outputs: [employee_id, software, entitled, license_status, expires_at, available_seats]
side_effect: false
requires_confirmation: false
---
# check_software_license

Checks whether a fictional employee has an entitlement for a supported software
product. It reads deterministic mock data only. It does not assign, revoke, or
purchase licenses and never returns credentials.
