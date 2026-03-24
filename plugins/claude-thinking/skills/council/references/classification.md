# Question Classification

Map the user's question to a type, then select personas in the listed priority order. Take the top N based on council size (quick=2, standard=4, full=6). Advocate is always included unless explicitly excluded.

## Classification Rules

Match by keywords and intent. If multiple types match, pick the one that best captures the user's primary concern. Default to General/Mixed when ambiguous.

## Question Types

### Architecture / Design
**Keywords:** structure, dependency, coupling, module, interface, boundary, schema, API design, refactor, separation of concerns, pattern
**Persona order:** Architect, Skeptic, Pragmatist, Strategist, Advocate, Innovator

### Strategy / Direction
**Keywords:** direction, roadmap, priority, invest, bet, focus, positioning, competitive, growth, vision, long-term
**Persona order:** Strategist, Skeptic, Innovator, Advocate, Architect, Pragmatist

### Risk Assessment
**Keywords:** risk, failure, security, vulnerability, what could go wrong, downside, exposure, compliance, audit, incident
**Persona order:** Skeptic, Architect, Strategist, Pragmatist, Advocate, Innovator

### UX / Developer Experience
**Keywords:** user experience, developer experience, onboarding, documentation, error message, workflow, friction, confusion, discoverability, accessibility
**Persona order:** Advocate, Pragmatist, Innovator, Architect, Skeptic, Strategist

### Innovation / Alternatives
**Keywords:** alternative, different approach, rethink, creative, novel, unconventional, what if, explore options, brainstorm approaches
**Persona order:** Innovator, Architect, Skeptic, Strategist, Pragmatist, Advocate

### Planning / Sequencing
**Keywords:** order, sequence, phase, milestone, timeline, deadline, dependency chain, rollout, migration, incremental, ship
**Persona order:** Strategist, Pragmatist, Architect, Skeptic, Innovator, Advocate

### General / Mixed
**Default type when no strong keyword signal.**
**Persona order:** Architect, Skeptic, Pragmatist, Advocate, Strategist, Innovator

## Selection Algorithm

1. Classify the question into one type
2. Take the top N personas from that type's priority order
3. If Advocate is not in the top N, replace the last persona with Advocate (unless `--exclude advocate`)
4. Apply `--include` overrides: add named personas, bumping the list to N+extras
5. Apply `--exclude` overrides: remove named personas
6. Enforce minimum floor: if fewer than 2 personas remain, backfill from the next-ranked personas in the priority order until the council has 2
