# Permission mode and approvals

Owner's rule: no approval hurdles; ask only when private data would be exposed (memory `feedback-no-permission-hurdles`).

## Working recipe (verified 2026-11-12 18:01 UTC)
1. `get_session` (no argument) first. If `permission_mode` is `plan`: stop; ask the owner to re-select Auto in the Claude app (session menu, top right), or to start a fresh session.
2. The phone's mode sheet offers Manual / Accept edits / Plan / Auto only (no bypass). If the app record and the phone disagree, tapping Accept edits then Auto re-syncs it.
3. Create children with `permission_mode: auto`. A bare child gets `default` and prompts. A child cannot be more permissive than its creator (`bypassPermissions` is refused with "exceeds parent session's plan" while the parent is in plan).
4. Put every permission and the hard stop into the child's first prompt; peer messages cannot grant anything.

## Settings in `~/.claude/settings.json`
- `permissions.defaultMode: "bypassPermissions"` (same as `--dangerously-skip-permissions`) and `skipDangerousModePermissionPrompt: true`: a session started from the phone needs no dialog. Applies to sessions started after the change; a running session keeps its mode.
- `crossSessionInbound: "accept"`: messages from the owner's other sessions arrive without a hold (needs a restart).
- Allow rules: whole `mcp__claude-code-remote` server, `Bash(*)`, `Read`, `Edit`, `Write`, `Agent`, `Skill`, `ToolSearch`, `TaskStop`.
- These settings do not apply to a remote session: its prompts follow its own mode, set at creation.

## Why cards appear
- Plan mode: every `create_session` / `send_message` raises a card on the phone whatever the allow rules say. The mode is signed by the owner's trusted device (`permission_mode_device_proof`); I cannot change it.
- A child in `default` mode shows "Waiting on permission: claude-code-remote - Send Message" for its own replies.
- A tool with no allow rule (list in lessons.md, permission history).
- Inbound messages held by the mode-parity rule before `crossSessionInbound` was set.

## Cannot be fixed from here
- Sessions locked to the owner's trusted device refuse reads and messages with `elevated_session_untrusted_device`: do not retry; use GitHub CI or local helper agents instead.
- Editing settings that change my own permissions is blocked by the safety classifier until the owner says so in chat. Ask once, then do it.

## Still never, even in bypass mode
Force-push to a protected branch; relaxing branch protection; publishing secrets or private data; deleting the owner's data without a backup.
