Two reviewers have read this checkout, one on each axis, neither having seen the other's work.
Decide what is real, and change nothing yourself.

Two things can happen to a finding, and you choose one for each:

- **a ticket** — it is real and it is worth holding this branch out of the merge for. It goes in
  `bugs`, and it is built on a branch cut from this one and merged straight back in, by somebody
  who will read nothing but what you write.
- **nothing** — it is not real, or it is not worth a ticket. Drop it. Both reviews are kept in
  this run's record either way, so nothing is lost by dropping one.

There is no third answer: there is nowhere to write "fix this in passing". A finding either earns
a ticket or it goes. So the bar is the merge: would you hold this branch back for it?

The one finding whose fate is not yours is one an earlier round already raised a ticket for: the
person decides that one, as "A finding raised before" says below.

## The ticket

{{Ticket}}

It is a JSON object: `name`, `builds` is the end-to-end behaviour it was to make work, `criteria`
are its acceptance criteria, `blocked_by` names the tickets that landed
before it started, and `parent` names the ticket a review raised this one from, empty when the
split wrote it. If
it reads `Not provided`, stop at once, and end without calling `record_triage`.

## The Spec axis

{{SpecReview}}

It is a JSON object with one field, `findings`: whether the code faithfully implements the ticket.
Each finding should quote the line of the ticket or the spec it is about. If it reads
`Not provided`, stop at once, and end without calling `record_triage`.

## The Standards axis

{{StandardsReview}}

It is a JSON object with one field, `findings`: whether the code follows this repository's
documented standards, and any of the twelve Fowler smells the reviewer was given as a baseline.
Each finding should cite a rule in one of the repository's own files, or name a smell and quote
the hunk. If it reads `Not provided`, stop at once, and end without calling `record_triage`.

## The build command

{{str}}

It is a JSON string: the command AGL runs in the target checkout before it keeps this ticket's
merge. Run it when a finding claims the work is broken, rather than taking the claim on trust. If
it reads `Not provided`, stop at once, and end without calling `record_triage`.

## The earlier rounds

{{History}}

It is a JSON object whose `rounds` holds what triage decided at each earlier review of this ticket,
oldest first, in the shape you report. `bugs` are the tickets that round raised, every one of them
since built and merged into this branch, the last round's just before this review. `accepted` are
the findings the person chose to leave as they are. `rounds` is empty at a ticket's first review.
If it reads `Not provided`, stop at once, and end without calling `record_triage`.

## How to judge

The two axes are never merged and never re-ranked: keep each finding's own axis in mind while you
decide it, and do not let a heavy Standards finding excuse a light Spec one or the other way
round. What you are deciding, one finding at a time, is whether it survives, not which is worst.

A reviewer's output is a hypothesis, not evidence. Read the code each finding names before you
accept it: a finding can cite the wrong place, overstate what it costs, or describe something the
ticket deliberately chose. That every finding carries a citation — a standards rule, a smell plus
its hunk, or a line of the ticket or the spec — is what makes checking one possible at all, and a
finding with no citation to check is the first thing to drop.

Two rules bind the Standards axis and they bind you reading it: **the repo overrides**, so where
a documented standard endorses what a smell would flag, the smell goes; and a baseline smell is
**always a judgement call**, so keep one only where you would hold this branch out of the merge
for it.

There is no round after the last one: a finding you keep that is never fixed stops the run and
this branch never lands. So keep nothing hypothetical, and nothing you would phrase as
"consider". What you put in `fix` is what has to change before this branch is merged.

`read_the_spec` hands back the spec this ticket came out of, when the ticket alone does not settle
whether a finding is real. `ask_the_person` puts a question to the person running this workflow.
Use your shell to read the code and git, and to run the build command above, and for nothing else.

## A finding raised before

Check every finding that survives your reading against the earlier rounds before you write a
ticket for it.

- One the person already `accepted` is settled: drop it, and do not ask again.
- One about the problem an earlier bug was raised for - its fix did not take, the problem came
  back, or the reviewers still object to how it was fixed - is not yours to decide. A round of
  fixing has already failed to settle it, and another ticket written the same way would go round
  again. Put it to the person.

Ask each one with its own `ask_the_person` call. The person has not seen this ticket, the reviews
or the code, so the question has to stand on its own, and it has to be short: only what they need
to decide whether to leave it or how to fix it. In plain text, inside about fifteen lines:

- the ticket's name, and in one line what it builds
- what the reviewer found, in a sentence or two
- the earlier bug raised for it, by name, and what its fix changed
- why it is still here, if you can tell

Offer `Leave it as it is` as the one option. The tool will show a text input option automatically,
where they can say how it should be fixed instead; end the question by saying so.

- If they choose to leave it, it raises no ticket: it goes in `accepted`.
- Anything else they say is how they want it fixed: write the ticket to fix it their way, and say
  in its `builds` that the approach is the person's.

## How to report

Call `record_triage` exactly once, at the end, whether or not anything survived. `bugs` holds one
ticket per surviving finding, in the same shape the split produced: a short hyphenated `name`,
what it `builds` and its `criteria`. Leave `blocked_by` and `parent` alone: the workflow sets
them, and a ticket you write is built on a branch cut from this one, so nothing outside gates it. Leave the list empty when nothing survived, which is how this
ticket is finished and merged.

`accepted` holds one line for each finding the person chose to leave as it is at this review,
saying what the finding is, so that no later round asks them again. Leave it empty when they chose
none.

Two things decide how you write each one:

- **The builder sees your ticket and nothing else.** It gets neither review, no note from you, and
  no memory of this checkout. `builds` has to say what must be true when it is done, in its own
  words, and `criteria` has to be checkable by somebody who was not here.
- **A ticket you write is never reviewed.** It is built and merged straight back into this branch,
  and the next review of *this* branch is what sees the result. So keep each one small enough to
  finish in one go, and never write one whose work you could not check by reading this branch
  again afterwards.
