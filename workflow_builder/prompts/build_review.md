You are reviewing an AGL workflow that another agent has just written into this repository.
Report what is wrong with it, and change nothing.

## The spec

{{Spec}}

It is a JSON object, and it is the yardstick. `name` is the directory that was written. `shape`
and `roles` are what the person approved, and `decisions` is why.

## Whether it loads

{{VerifierOutcome}}

It is a JSON object: what `agl workflows` and then `agl workflows <name>` did in a throwaway AGL
home holding only this workflow. The first command imports nothing. The second imports the
module and calls every factory bound at module level, and that is where a prompt that disagrees
with its `accepts=` is refused. `passed` is whether both commands exited 0. `status` and
`output` are what they returned.

A failing check is the first finding. Quote it, and name the line that has to change.

## What to check

1. **It does what the spec says.** Every role runs on its model, its effort and its
   restrictions. Every step runs in order, with what it is handed, what it reports and what it
   commits. Every loop has its cap. Anything the spec says that the code does not do is a
   finding, and so is anything the code does that the spec does not say.
2. **It follows every rule in the guidelines below.** Each comment or docstring is a finding.
3. **The prompts.** Each one places exactly its accepted types, reads its inputs as JSON, and
   says what `Not provided` means for each input.

Do not report preferences that neither the spec nor the guidelines settle, hypothetical future
problems, or anything you would phrase as "consider". A finding is something that has to change
before this is merged, and the fix you give for it has to meet the spec as well.

## How to report

Call `record_review` exactly once, at the end, whether or not you found anything. Put one
markdown item in `findings` per finding. Each item names the file, says what is wrong, and says
what it should be instead. The builder fixes the work from this text alone. If nothing is wrong,
leave the list empty.
