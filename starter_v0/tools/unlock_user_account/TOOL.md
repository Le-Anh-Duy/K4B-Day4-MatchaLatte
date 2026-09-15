---
name: unlock_user_account
track: bonus
kind: action
provider: local_account_action_store
requires_env: []
inputs: [employee_id, system, confirmed]
outputs: [status, action_id, employee_id, system, unlocked_at, path]
side_effect: local_file_write
requires_confirmation: true
---
# unlock_user_account

Records a fictional SSO account-unlock action under `account_actions/`. It writes
nothing unless `confirmed` is explicitly true. Only accounts whose mock directory
status is `locked` can be unlocked; disabled, active, expired-password, and unknown
accounts are rejected. It never accepts passwords, OTPs, tokens, or recovery codes.
