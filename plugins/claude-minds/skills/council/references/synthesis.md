# Dialectical Synthesis

After all council agents return their positions, synthesize using these 7 steps. The synthesis is your voice as orchestrator — opinionated, not neutral. You are rendering judgment, not summarizing.

## Step 1 — Map Consensus

Identify findings where a majority of agents agree: 2/2 in quick mode, 2+/3 in 3-persona councils, 3+/4 in standard mode, 4+/6 in full mode. These are high-confidence conclusions. State them as facts, not as "the agents agreed that..." Attribute only when a specific agent provided unique evidence.

## Step 2 — Identify Tensions

Find points of explicit disagreement between agents. A tension exists when two agents recommend different actions or reach different conclusions about the same aspect. Name the tension concretely: "The Architect recommends X while the Pragmatist recommends Y because of Z."

## Step 3 — Resolve or Frame

For each tension:
- If one side has stronger evidence or reasoning, pick that side and explain why
- If both sides are valid and the choice depends on user priorities, present it as a genuine tradeoff the user must decide
- Never split the difference. Either resolve the tension or name it as a real choice.

## Step 4 — Detect Blind Spots

Identify important aspects of the question that NO agent addressed. Common blind spots:
- Operational concerns (monitoring, debugging, rollback)
- Communication (who needs to know, documentation)
- Edge cases at system boundaries
- Second-order effects on adjacent systems or workflows
- The "who actually does this work" question

Flag blind spots explicitly. Do not fill them with speculation — name them as open questions.

## Step 5 — Build Confidence Map

For each major conclusion in your synthesis, rate confidence:
- **High** — multiple agents agree, evidence is concrete, risks are identified and manageable
- **Medium** — some agreement, evidence is partial, notable uncertainties remain
- **Low** — agents disagree, evidence is thin, or the question is inherently uncertain

## Step 6 — Synthesize Verdict

Write a 1-3 sentence verdict. This is the answer to the user's question. It must be:
- Opinionated — take a position, do not hedge
- Actionable — the user can act on it immediately
- Grounded — supported by the evidence the council surfaced

If the council reached genuine consensus, the verdict reflects that consensus. If there's an unresolved tension, the verdict recommends one side and explains the conditions under which the other side would be better.

## Step 7 — Order Next Steps

List 3-5 concrete next steps, ordered by priority. Each step should be:
- Specific enough to act on (not "think more about X")
- Assigned an urgency: do now / do soon / do later
- Informed by the council's analysis
