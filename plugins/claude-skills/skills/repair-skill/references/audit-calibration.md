# Audit Calibration — Known False-Positive Patterns

Load before running the 7-dimension structural audit. Each entry describes a rule that is
correct in principle but frequently misapplied to look-alike situations that should not
trigger the rule.

---

## D2 / `allowed-tools` absent

`allowed-tools` absent entirely means unrestricted by default — this is NOT a violation
at any severity. The field is an optional restriction mechanism, not a required declaration.
Only flag when a skill has an *existing* `allowed-tools` list that omits a tool the skill
actively uses — a partial restriction creates the problem; absent restriction does not.

**Flag this:** Skill has `allowed-tools: [Read, Write]` but calls AskUserQuestion
→ major violation (restricted list is incomplete).

**Do not flag this:** Skill has no `allowed-tools` field but calls AskUserQuestion
→ no violation; the tool is available by default.

---

## D5 / Orientation content vs routing guidance

Flag as a routing-guidance violation only when the body contains a "When to Use This
Skill" section or explicit language telling the user *when to trigger the skill*. Content
that explains domain concepts *needed during execution* — so the skill can make accurate
decisions — is functional orientation, not routing guidance.

Rate functional orientation as verbosity (minor) only if it exceeds 4–5 lines without
adding decision value that the skill body requires.

**Flag this:** Body has `## When to Use This Skill — use this when you want to create a
new skill` → major violation (routing guidance in always-loaded body, never read by the
routing decision).

**Do not flag this:** Body has `Agents vs Skills — know the difference before generating:
Agents run in isolated context, Skills inject inline` → functional orientation that helps
the skill produce accurate output; not routing guidance.

---

## D4 / Task/Skill invocation prose

Natural language inside a fenced block describing how to call Claude's own tools is the
idiomatic skill instruction format — `Use Task tool with subagent_type=X: "..."` is how
skills correctly instruct Claude. Do not flag this as a vague script reference.

Only flag D4 prose as a violation when it refers to *user-facing scripts or deterministic
CLI operations* (validate.py, init.sh, etc.) without specifying which file, the trigger
condition, and the exact invocation command.

**Flag this:** Body says "run the validation script if needed" with no path, trigger, or
invocation → major violation (deterministic script reference is vague).

**Do not flag this:** Body has a code block:
`Use Task tool with subagent_type=claude-code-guide: "List current frontmatter options"`
→ idiomatic instruction to Claude to use a built-in tool; not a script reference.

