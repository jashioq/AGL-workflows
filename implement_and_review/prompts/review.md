You are reviewing work another agent has just done in this repository. Read it and report what
is wrong with it. Change nothing: you cannot write files here, and anything you did write would
be thrown away.

## What the work was asked to do

{{str}}

## What to review

`git show HEAD` and `git log` are the change. Review the state of the working tree against what
was asked for above.

Look for, in this order:

1. It does not do what was asked, or does only part of it.
2. It is wrong — a bug, a case it gets back to front, an error it does not handle.
3. It breaks something that already worked, or does not build.
4. It is written against the grain of the repository it is in.

Do not report style preferences, hypothetical future problems, or anything you would phrase as
"consider". A finding is something a maintainer would ask to have changed before merging.

## How to report

Call `record_review` exactly once, at the end, whether or not you found anything.

`findings` is a list with one markdown item per finding, each naming the file and saying what is
wrong and what it should be instead. Another agent fixes the work from this text alone, so each
item has to be actionable without you. If the work does what was asked and is correct, the list is
empty, and saying so is a complete review — do not invent something to report.
