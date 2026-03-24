# Council Output Format

Three templates based on council size. Use the matching template for the number of perspectives dispatched.

---

## Quick Format (2 perspectives)

```
## Council Verdict

[1-3 sentence opinionated verdict]

**Question type:** [classified type]
**Council:** [Persona 1], [Persona 2]
**Confidence:** [H/M/L]

### Agreement
[Points where both perspectives align]

### Disagreement
[Points where they diverge, with your resolution]

### Next Step
[Single most important action]
```

---

## Standard Format (3-4 perspectives)

```
## Council Verdict

[1-3 sentence opinionated verdict]

**Question type:** [classified type]
**Council:** [Persona 1], [Persona 2], [Persona 3], [Persona 4]

### Consensus
[Findings where majority agrees — state as conclusions, not attributions]

### Key Tensions
[Each tension named, framed, and either resolved or presented as a tradeoff]

### Blind Spots
[What no agent addressed — flagged as open questions]

### Confidence Map
| Conclusion | Confidence | Basis |
|-----------|------------|-------|
| [conclusion] | H/M/L | [why] |

### Next Steps
1. **[do now]** — [specific action]
2. **[do soon]** — [specific action]
3. **[do later]** — [specific action]
```

---

## Full Format (5-6 perspectives)

Use the Standard Format above, plus append individual perspective summaries in collapsible sections:

```
### Individual Perspectives

<details>
<summary>[Persona Name] — [one-line position summary] (Confidence: H/M/L)</summary>

[2-3 paragraph summary of this agent's analysis, key evidence, and position]

</details>

<details>
<summary>[Persona Name] — [one-line position summary] (Confidence: H/M/L)</summary>

[2-3 paragraph summary]

</details>

[...repeat for each persona]
```

If any agent dissented strongly from the verdict, add after individual perspectives:

```
### Dissenting View
[Name the dissenter, their position, and why the verdict overruled them]
```
