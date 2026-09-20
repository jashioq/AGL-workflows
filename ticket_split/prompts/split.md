Break the spec below into a set of **tickets**: tracer-bullet vertical slices, each declaring the
tickets that **block** it. Nothing you write reaches disk: the tickets you record are what the
rest of the run builds.

## The spec

{{Spec}}

It is a JSON object: the problem, the solution, the user stories, the seams the feature is tested
at, the implementation and testing decisions, what is out of scope, the project's glossary in
`terms`, its decision records in `decisions`, and any further notes. If it reads `Not provided`,
stop at once: ask nothing, and end without calling `record_tickets`.

## 1. Explore the codebase

If you have not already explored the codebase, do so to understand the current state of the code.
Ticket names and descriptions should use the project's glossary vocabulary from `terms`, and
respect the decision records in `decisions` in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change
easy, then make the easy change."

## 2. Draft vertical slices

Break the work into **tracer bullet** tickets.

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests):
  vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Each slice is sized to fit in a single fresh context window
- Any prefactoring should be done first

Give each ticket its **blocking edges**: the other tickets that must complete before it can start.
A ticket with no blockers can start immediately.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical
change (rename a column, retype a shared symbol) whose **blast radius** fans across the whole
codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land
green. Don't force it into a tracer bullet; sequence it as **expand-contract**. First expand: add
the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized
by blast radius (per package, per directory), each batch its own ticket blocked by the expand,
keeping CI green batch to batch because the old form still exists. Finally contract: delete the
old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches
can't stay green alone, keep the sequence but let them all block a final integrate-and-verify
ticket; green is promised only there.

Every ticket is built in a checkout of its own, cut from the state its blockers left behind, and
merged back behind this project's build command. So a blocking edge is not a note to a reader: it
is the only thing that stops two tickets being built at the same time. Declare one where a ticket
genuinely cannot start until another has landed, and nowhere else.

## 3. Quiz the user

Present the proposed breakdown with `ask_the_person`, as a numbered list. For each ticket, show:

- **Title**: short descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct: does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?

Offer `Approve` as the one option. Any other answer is a change: make it, keep everything they did
not object to, and show them the breakdown again. Iterate until the user approves the breakdown.

## 4. Record them

Only after they answer `Approve`, call `record_tickets`, once, with every ticket in dependency
order, blockers first. Each ticket is:

- `name` - a short name in lower case with words joined by hyphens. It names a branch and a
  directory, so letters, digits and hyphens only, and no two tickets share one.
- `builds` - the end-to-end behaviour this ticket makes work, from the user's perspective, not a
  layer-by-layer implementation list.
- `criteria` - the acceptance criteria. For each one, name the observation that would show it
  false, and confirm it fails at the commit the implementer starts from. A criterion already true
  before the work begins grades nothing.
- `blocked_by` - the names of the tickets that gate this one, or empty when it can start
  immediately.

Avoid specific file paths or code snippets: they go stale fast. The exception is the one the spec
already makes, a snippet that encodes a decision more precisely than prose can.
