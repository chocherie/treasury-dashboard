# Core Beliefs

These are the operating principles for working in this repository. They apply to both human developers and AI agents. When you're unsure how to approach a decision, come back to these.

## On Specifications

**Specs are the source of truth for intent.** Before writing any code, read the relevant spec. If no spec exists for what you're building, write one first. A spec doesn't need to be perfect — it needs to exist so that intent is captured and reviewable.

**Specs are living documents.** If you discover during implementation that the spec is wrong or incomplete, update the spec first, then update the code. Never silently diverge from a spec. The gap between spec and code is where bugs hide.

**Every spec must be verifiable.** A spec that can't be checked against the code is just a wish. Write specs with concrete types, explicit API shapes, and observable behaviors so that verification is mechanical, not subjective.

## On Planning

**Plans before code.** For any work that touches more than one file or takes more than an hour, create a plan. Small changes can use a lightweight plan (a few sentences in the PR description). Complex work requires an ExecPlan in `docs/plans/active/`.

**Plans are self-contained.** A plan must contain everything needed for someone with zero context to pick it up and execute. Don't reference "what we discussed" or "the previous approach." Embed the knowledge directly.

**Plans are living documents.** Update the plan as you make progress, discover surprises, or change direction. The plan should always reflect the current state of the work, not the original vision.

## On Quality

**Verification over trust.** Don't assume code is correct because it compiles or because the tests pass. Use the multi-agent review loop (`.agents/workflows/implement-and-verify.md`) to verify code against specs. Use property-based tests to verify behavior against invariants.

**Observable outcomes over internal attributes.** Define acceptance as behavior a human can verify: "navigate to X, see Y" or "run this command, expect this output." Not "added a struct" or "created a handler."

**Fix the system, not the symptom.** When something fails, the question is not "how do I make this specific thing work?" but "what capability is missing, and how do I make it legible and enforceable?" Invest in the scaffold, not the patch.

## On Context

**Context is a scarce resource.** Don't dump everything into one file or one prompt. Keep `AGENTS.md` slim. Point to deeper docs. Let the agent load only what it needs for the current task.

**The repository is the memory.** Don't rely on conversation history or context windows for important decisions. Write it down in the repo: specs, plans, decision logs, TODO updates. If it's not in a file, it doesn't exist.

**Stale docs are worse than no docs.** A document that says the wrong thing is more dangerous than a gap. Update docs as you go. If you can't update it now, add a note: "STALE — needs update after X."

## On Implementation

**Depth-first, not breadth-first.** Build one thing completely — spec, implementation, tests, verification — before moving to the next. A half-built feature across three systems is worse than one fully built system.

**Small, verifiable steps.** Make changes that can be tested and reviewed independently. Prefer additive changes followed by subtractions. Keep tests passing at every step.

**Idempotent and safe.** Write code and scripts that can be run multiple times without causing damage or drift. If a step is risky, provide a rollback path.

## On Simplicity

**Design for removal.** As tools and models improve, the scaffolding should get simpler, not more complex. Write code and docs that are easy to prune. Don't over-invest in structure that may be obsolete in six months.

**When everything is important, nothing is.** Be selective about what goes into AGENTS.md, what gets a spec, and what becomes a workflow. Not every decision needs a document. Focus documentation on things that are hard to reverse or easy to get wrong.

**Start simple, add complexity only when forced.** The simplest approach that works is the best approach. Add abstraction layers, caching, optimization, and tooling only when you have evidence they're needed.
