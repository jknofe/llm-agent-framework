# New Ideas — For Further Investigation

Collected ideas to develop the framework further. Each needs investigation before becoming part of CONCEPT.md / init_agent.py.

## 1. Karpathy-Modell

Investigate Andrej Karpathy's mental model of LLM systems and what it implies for the framework:

- "LLM as CPU, context window as RAM" — treat context as a scarce resource that the harness manages deliberately (paging facts in/out, not accumulating).
- The "LLM OS" framing: the agent framework as an operating system around the model (scheduler, memory hierarchy, I/O via tools).
- His emphasis on keeping the agent loop small and legible instead of piling on abstraction layers.

**Open questions**
- Which of these framings map onto the current init_agent.py architecture, and where do we contradict them?
- Does the context-as-RAM view suggest a concrete eviction/compaction strategy for our KB injection?

## 2. Understand-Everything

Principle: the agent should build (or be given) full understanding of the relevant system before acting, instead of acting on partial pattern matches.

**Directions to explore**
- A dedicated "understanding phase" before implementation: enumerate affected files, data flow, and invariants; only then edit.
- Persisting that understanding (architecture notes, invariants) into the KB so later sessions don't re-derive it.
- Measuring it: does a forced understanding phase reduce wrong-fix rate in the benchmarks (see benchmarks/)?

**Open questions**
- Where is the cutoff? Full understanding is expensive — when is "enough" understanding reached?
- Prompt-level rule vs. enforced workflow step in the harness?

## 3. More Offloading into Deterministic Python Script

Move more work out of the LLM and into deterministic code (init_agent.py or new scripts): everything that is rule-based should not consume tokens or risk model variance.

**Candidates to evaluate**
- Repo/KB scanning, indexing, and fact extraction done by script, with the model only consuming the digest.
- Validation/verification steps (lint, structure checks, benchmark scoring) run deterministically instead of asked of the model.
- Routine transformations (file moves, boilerplate generation, report assembly) as script functions the agent merely triggers.

**Open questions**
- Which current prompt instructions are actually deterministic rules in disguise?
- Cost/benefit per candidate: token savings + reliability gain vs. added script complexity.

---

Next step: pick one idea, run a small benchmark comparison (as with the existing runs in benchmarks/) to see if it earns a place in the framework.
