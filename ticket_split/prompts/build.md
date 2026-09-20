Implement the work described in the ticket below. This checkout is yours alone and holds only
this ticket's work; other tickets are being built elsewhere at the same time.

## The ticket

{{Ticket}}

It is a JSON object: `name`, `builds` is the end-to-end behaviour to make work, `criteria` are the
acceptance criteria, and `blocked_by` names the tickets that landed before this one started. If it
reads `Not provided`, stop at once and write nothing.

## What triage wants fixed

{{Triage}}

If that reads `Not provided`, this is the first build of this ticket. Otherwise it is a JSON
object. Two reviewers read this checkout, one against the ticket and one against the repository's
standards, and triage judged what they found: `fix` is everything that is real and yours, and it
is what you do in this pass - read the work already here, fix every one of them, and change
nothing else. Its `bugs` are separate tickets, already being built in checkouts of their own:
leave them alone.

## The build command

{{str}}

It is a JSON string: the command this project is built and tested with, and the one AGL runs in
the target checkout before it keeps this ticket's merge. It is the full test suite for the purpose
of the last line of "How to work" below. Run it, and do not finish while it fails: a branch that
fails it is refused at the merge and nobody downstream can fix that for you. If it reads
`Not provided`, stop at once and write nothing.

## What you may read

`read_the_spec` hands back the spec every ticket in this run came out of, as a JSON object: the
problem and solution, the user stories, the seams, the implementation and testing decisions, what
is out of scope, the project's glossary in `terms` and its decision records in `decisions`. Read
it when you need the reasoning behind the ticket, the vocabulary to name something, or the seam
you are meant to be testing at. Use that vocabulary, and respect those decisions.

`ask_the_person` puts a question to the person running this workflow. Use it for something only
they can answer; anything the codebase can answer is yours to find.

## How to work

Use test-driven development where possible, at the seams the spec already agreed. No test is
written at a seam nobody agreed to: if the work needs one the spec does not name, ask.

A **seam** is the public boundary you test at: the interface where you observe behavior without
reaching inside. Tests live at seams, never against internals. Tests verify behavior through
public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good
test reads like a specification: "user can checkout with valid cart" tells you exactly what
capability exists, and it survives refactors because it doesn't care about internal structure.

Rules of the loop:

- **Red before green.** Write the failing test first, then only enough code to pass it. Don't
  anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** It belongs to the review stage, which happens after
  you, not inside the red-green cycle.

Anti-patterns:

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies
  through a side channel (querying the database instead of using the interface). The tell: the
  test breaks when you refactor but behavior hasn't changed.
- **Tautological**: the assertion recomputes the expected value the way the code does, so it
  passes by construction and can never disagree with the code. Expected values must come from an
  independent source of truth: a known-good literal, a worked example, the spec.
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify
  _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests
  go insensitive to real changes, and you commit to test structure before understanding the
  implementation. Work in **vertical slices** instead: one test, one implementation, repeat, each
  test a **tracer bullet** that responds to what the last cycle taught you.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Build what the ticket says and nothing else. Work that belongs to another ticket is that ticket's,
even where you can see how to do it from here.
