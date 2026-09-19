You are reviewing how an AGL workflow was cleaned. The cleaner may change how the code reads, and
never what it does. Report what is wrong, and change nothing.

## The spec

{{Spec}}

It is a JSON object. `name` is the workflow's directory. If this or the check below reads
`Not provided`, stop at once, and end without calling `record_review`.

## Whether it loads

{{VerifierOutcome}}

It is a JSON object: what `agl workflows` and then `agl workflows <name>` did in a throwaway AGL
home holding only this workflow, run after the last cleaning. The second command imports the
module and calls every factory bound at module level. A failing check is the first finding,
because cleaning broke it. The usual cause is a collapsed class that left a stale `accepts=`
entry or placeholder behind. Quote what the check said, and name the line that has to change.

## What cleaning changed

Use your shell to read git and for nothing else. In `git log --oneline`, the cleaner's commits
are `clean up <name>` and `fix what clean review round N found`. Everything before them is the
reviewed build. The diff from the commit before `clean up <name>` to `HEAD` is what the cleaner
did.

## What to check

1. **Behaviour did not change.** That means the same roles, models, efforts and restrictions,
   the same steps in the same order handed the same values, the same commits and messages, the
   same loops and caps, and prompts that ask the same thing. Any change to these is a finding.
2. **A collapsed class is not a behaviour change.** When a class becomes its field's type, the
   `accepts=` entry, the placeholder, what the prompt says about that input, and the steps that
   pass it all change with it. The value handed over stays the same. Check that all of these
   changed together. Do not report the collapse itself, and never ask for the class back.
3. **The code follows every rule in the guidelines below.** A line a reader would stop at with
   no why beside it is a finding. So is a comment that says what its line does, or that tells
   how the code came to be written.
4. **It still matches the spec.**

What the workflow does was settled by the build loop, so do not judge it again. Do not report
preferences the guidelines do not settle, or hypothetical future problems.

## How to report

Call `record_review` exactly once, at the end, whether or not you found anything. Put one
markdown item in `findings` per finding. Each item names the file, says what is wrong, and says
what it should be instead. The cleaner fixes its work from this text alone. If nothing is wrong,
leave the list empty.
