# Sprint Triage Reference — Detection Heuristics

This document is a reference for the sprint-triage command. It contains the detection patterns, word lists, and framework details used when assessing story readiness.

## Information Availability Framework

When assessing whether a story has the information needed for implementation, classify each piece of information into one of three categories:

| Category | Definition | Effect on bucket |
|----------|-----------|-----------------|
| **Provided** | The story gives you the information directly (file path named, example attached, spec linked) | Best case — reduces implementation risk |
| **Findable** | The story doesn't provide it, but you can locate it in the codebase. The story describes something specific enough to grep for (a CLI flag name, an error message, a concept that maps to known directory structures) | Acceptable for Act Now — note it in readiness notes |
| **Missing** | You can't start without someone providing this. The information isn't in the story and can't be derived from the codebase (API credentials, unreleased specs, design decisions not yet made, references to external systems without access instructions) | Blocks Act Now — must go to Clarify or Blocked |

**Key distinction:** "Findable" means you can describe a single, specific search that would answer the question. "Grep for `rekor` in ec-cli" is findable — one command, clear result. "Study the CI workflows across two repos to understand the publishing pipeline" is not findable — that's an investigation, and investigations are missing information that someone needs to provide or document.

**How to assess:** Don't passively check whether signals are present. Actively generate questions you'd need answered to start implementing, then try to answer each one. If a story says "follow the existing pattern for X," ask yourself: can I describe that pattern right now? If not, try to figure it out. If that takes more than a quick lookup, the information is missing regardless of how confidently the story references it.

## Ambiguity Word List

These words in acceptance criteria make them non-testable. An LLM cannot objectively verify whether a criterion using these words is met:

**Subjective quality words:**
- appropriate, appropriately
- better, improved, enhanced
- clean, cleaner
- proper, properly
- good, well
- intuitive, user-friendly
- reasonable, sufficient
- elegant, simple (when used as a quality judgment)
- nice, robust

**Open judgment words:**
- as needed, where necessary, when appropriate
- should be easy to, should be straightforward
- clearly, obviously
- looks good, feels right

**Scope-expanding words (in AC):**
- etc., and so on, and more, and similar
- other improvements, additional enhancements
- where applicable, as applicable

When you encounter these in acceptance criteria, flag them in the "What's missing" section with a specific suggestion. Example: "AC #2 says 'appropriate error handling' — replace with specific error scenarios: What errors can occur? What message should each produce? What exit code?"

## Open-Ended Language Patterns

These patterns in story descriptions or scope sections signal unbounded work that may need the Break Down bucket:

**Unbounded verb patterns:**
- "Improve X" without a measurable target (improve what metric? by how much? for which cases?)
- "Optimize X" without a benchmark (optimize from what to what?)
- "Clean up X" without listing what's dirty (which files? which patterns? what does "clean" look like?)
- "Refactor X" without a target architecture (refactor to what pattern? which call sites?)

**Scope creep signals:**
- "and more" / "and other" / "etc." at the end of a list
- "as needed" / "as appropriate" after a task description
- "while we're at it" / "also" introducing secondary objectives
- "any other" / "all related" without bounding what's related
- Lists that end with an ellipsis or imply continuation

**Multi-PR signals:**
- Story describes work across more than 3 distinct areas
- Story has 5+ acceptance criteria spanning different concerns
- Story uses phase language ("first... then... finally...") describing sequential work items
- Estimated scope language ("this is a big one", "multi-sprint")

## Required vs Helpful Signals — Quick Reference

### Required (missing = Clarify)

| Signal | What to check | Example of present | Example of missing |
|--------|--------------|-------------------|-------------------|
| Problem statement | Description explains what's wrong or missing today | "Currently ec validate exits 0 but doesn't include version in output JSON" | "Add version to output" |
| Desired outcome | Description explains what should be true when done | "Output should include evaluatorVersion field" | (implied by title only) |
| Testable AC | At least one criterion verifiable by running a command or reading code | "ec validate --output json includes evaluatorVersion matching --version output" | "Error messages are more descriptive" |
| Unambiguous AC | AC don't use words from the ambiguity list above | (same as above) | "Appropriate error handling is implemented" |

### Helpful (missing = note it, not blocking)

| Signal | What to check | Provided example | Findable example | Missing example |
|--------|--------------|-----------------|-----------------|----------------|
| Entry points | File paths, function names, packages | "Update `internal/evaluator/config.go`" | "Add a flag like `--ignore-sigstore`" (greppable) | "Update the validation logic" |
| I/O examples | Sample input, expected output, data shapes | JSON block showing attestation format | "Uses SLSA Provenance v1.0 format" (linked or already used in codebase) | "Process the attestation" |
| Pattern references | Similar implementations to follow | "Follow the pattern in `slsa_provenance_available.rego`" | "Like the --ignore-sigstore flag" (findable if it exists) | (no analogues mentioned) |
| Domain context | Specs, docs, background knowledge | "SLSA spec: https://slsa.dev/provenance/v1" | Term appears in codebase comments/docs | Jargon with no definition or codebase presence |
| Scope boundaries | What's in/out of scope | "Out of scope: backwards compat with v0.2" | AC is a closed checklist (implicit boundary) | "Improve error handling" (how much? where?) |

## External System Red Flags

Stories that reference systems outside the workspace need special scrutiny. These often look clear to someone who works with those systems daily but are unimplementable for an LLM (or a new team member):

**Check for:**
- API endpoints without full URLs, auth details, or payload schemas
- Dashboard/UI references without access instructions
- CI/CD systems mentioned without explaining how to trigger or access them
- "The team has..." or "They provide..." without concrete access details
- References to Slack conversations, meetings, or verbal agreements as the source of requirements

**These push to Clarify** (not Blocked) unless the story explains how to access the external system, or the system is already configured in the workspace (e.g., the MCP tools, `ec` CLI, `oc` CLI). Missing access information is a clarification gap — someone can answer "how do I access X?" — not a hard dependency like an unmerged PR or an unresolved architecture decision.

## Assessment Checklist

Quick checklist for each story — run through this mentally before assigning a bucket:

1. **Read the title alone.** Do you know what this is about? If not, the summary needs work.
2. **Read the description.** Can you explain the problem and desired outcome in one sentence each? If not, Q1 fails.
3. **Read the AC.** For each criterion, ask: "How would I verify this is done?" If the answer is "I'd look at it and decide," the criterion is subjective. If the answer is "I'd run this command / check this output / read this code," it's testable.
4. **Scan for ambiguity words.** Check the AC against the ambiguity word list above.
5. **Check for entry points.** Are there file paths, function names, or commands? If not, is the concept specific enough to grep for?
6. **Check for external references.** Does the story reference anything outside the workspace? If so, is access explained?
7. **Check scope boundaries.** Does the story have open-ended language? Does it feel like one PR or several?
8. **Check for blockers.** Any "depends on", "waiting for", "TBD", or unmerged upstream work?
