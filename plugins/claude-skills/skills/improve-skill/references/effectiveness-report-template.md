# Effectiveness Report Template

Load at Phase 3. Use this exact structure. Omit any section with no findings — do not
include empty headers.

---

## Report Format

```
SKILL EFFECTIVENESS REPORT: <skill-name>

NEW FEATURES (capabilities the skill should have but doesn't)
──────────────────────────────────────────────────────────────
HIGH VALUE
  [2x] <what the gap is> — <why it matters to the user>.
       Fix: <specific change or addition>

MEDIUM VALUE
  [2x] <what the gap is> — <why it matters to the user>.
       Fix: <specific change or addition>

UX IMPROVEMENTS (friction in the current workflow)
────────────────────────────────────────────────────
  [2x] <what the friction is> — <effect on user>.
       Fix: <specific change>

ACCURACY FIXES (factual drift from current docs)
──────────────────────────────────────────────────
  [2x] <what claim is outdated> — <what docs say vs what skill says>.
       Fix: <specific correction>

EFFICIENCY GAINS (same outcome with less token cost)
──────────────────────────────────────────────────────
  [2x] <what the inefficiency is> — <cost to user>.
       Fix: <specific change>
```

## Ordering Rules

- Within each section: HIGH → MEDIUM → LOW value
- Across sections: no required order — lead with the most important findings
- Each entry: sub-analysis code [2a/2b/2c/2d], the gap, why it matters, the fix
- Calibrate HIGH/MEDIUM/LOW using `references/effectiveness-rubric.md`

## Closing

After presenting the report, ask:

> "Apply all improvements? Or select specific ones?"

See `examples/sample-analysis.md` for a complete example of a real analysis output.
