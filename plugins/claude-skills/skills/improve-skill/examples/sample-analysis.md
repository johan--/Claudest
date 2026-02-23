# Sample Analysis: create-skill

This is a complete example of an improve-skill effectiveness analysis run against
`create-skill`. Use it to calibrate the expected depth and format.

---

## Skill Purpose (stated in Phase 1)

`create-skill` generates new Claude Code skills or commands from scratch. A user provides
requirements and receives a complete SKILL.md, ready to deliver.

---

## Phase 2 Findings

### 2a — Mental Simulation

Representative request: "Create a skill that reviews pull requests for security issues."

**Stuck point — Phase 0 (fetch docs):** The phase launches a Task with
`subagent_type=claude-code-guide` to check for new frontmatter options. If the subagent
fails or returns nothing new, the phase continues. But there is no instruction for what to
do if the subagent returns conflicting information (e.g., a field has changed its valid
values). Claude has to guess.

**Divergence point — Phase 4 (self-evaluation):** The skill instructs Claude to score the
generated skill on five dimensions against a "9.0/10.0" target. Two different Claudes will
score the same skill differently — the criteria (Clarity, Precision, Efficiency) are named
but not defined. One Claude might score Efficiency as 8/10, another as 7/10, and arrive at
different decisions about whether to refine.

**Dead end — post-delivery:** After the skill is delivered, the user has a SKILL.md but no
path to quality assurance. `repair-skill` exists for this, but `create-skill` never
mentions it. The user who doesn't know about `repair-skill` misses a natural next step.

### 2b — Live Doc Validation

Claim: `context: fork` requires `agent:` to be set.

Verification (via claude-code-guide): Current docs show `agent:` is optional when
`context: fork` is set. The claim in `frontmatter-options.md` (the reference file loaded by
create-skill) overstates the requirement.

**Drift severity: medium** — a user following this instruction wouldn't produce broken output
(setting `agent:` is harmless), but they'd add an unnecessary field.

All other frontmatter field names verified against current docs: ✓

### 2c — Feature Adjacency Scan

**Adjacent (high value):** After generating a skill, suggest running `repair-skill` for a
structural audit. Users who generate skills rarely know to do this separately, and repair
often catches things the generation phase missed. This is a one-sentence addition at the
end of Phase 3. Implementation effort: minimal.

**Complementary (medium value):** Before generating, help the user decide whether they need
a skill vs a command vs a custom agent. The skill currently assumes the user knows the right
artifact type. A one-question disambiguation in Phase 1 ("Is this something you'd trigger
automatically, or invoke manually with /?") would prevent the wrong artifact being generated.
Implementation effort: one AskUserQuestion in Phase 1.

### 2d — UX Flow Review

**Friction:** The Phase 1 interview asks five open-ended questions (Primary objective,
Trigger scenarios, Inputs/outputs, Complexity, Execution needs). A user who doesn't know
skill development best practices doesn't know what a "good" answer looks like. The
interview gathers information but doesn't guide it — a user who says "complexity: high"
because their problem feels hard might not realize this maps to `context: fork`.

**Consequential silent decision:** In Phase 2 Step 5 (delegation check), the skill
instructs Claude to scan for existing resources before finalizing. But if an existing skill
partially covers the requirement, Claude decides silently whether to extend it or create a
new one. This is a significant fork the user would want to weigh in on.

---

## Phase 3 Report

```
SKILL EFFECTIVENESS REPORT: create-skill

NEW FEATURES (capabilities the skill should have but doesn't)
──────────────────────────────────────────────────────────────
HIGH VALUE
  [2c] No post-delivery handoff to repair-skill — users who don't know it exists miss a
       natural quality-assurance step. The skill creates but never validates its output.
       Fix: Add one sentence at the end of Phase 3: "After delivery, suggest running
       repair-skill on the generated skill for a structural quality check."

MEDIUM VALUE
  [2c] No artifact-type disambiguation — skill assumes the user wants a skill, not a
       command or custom agent. Wrong artifact type requires starting over.
       Fix: Add AskUserQuestion in Phase 1: "Is this triggered automatically (skill) or
       invoked by the user via /? (command)" to route before generation begins.

UX IMPROVEMENTS (friction in the current workflow)
────────────────────────────────────────────────────
  [2d] Phase 1 interview asks open-ended questions but doesn't guide what good answers
       look like. Users unfamiliar with skill development give answers that don't map
       to the right frontmatter choices (e.g., complexity ≠ context: fork).
       Fix: Add one example per interview question showing how the answer shapes the
       generated skill.

ACCURACY FIXES (factual drift from current docs)
──────────────────────────────────────────────────
  [2b] frontmatter-options.md states context: fork requires agent: — current docs show
       agent: is optional.
       Fix: Update the claim in references/frontmatter-options.md.

EFFICIENCY GAINS (same outcome with less token cost)
──────────────────────────────────────────────────────
  [2a] Phase 4 self-evaluation scores 5 dimensions with undefined criteria — different
       Claudes score differently, making the 9.0 target arbitrary.
       Fix: Define each dimension's scoring criteria in one sentence, or move the scoring
       rubric to references/ where it can be elaborated without loading every invocation.
```
