You are working in a checkout of a repository. Make the change that is asked for below, in
the working tree, and leave it there — do not commit, do not branch, do not push. AGL commits
your work for you when the step ends.

## What was asked for

{{str}}

## Findings from the last review

{{Review}}

If that section says `Not provided`, no review has happened yet: this is the first pass, so
implement what was asked for.

Otherwise it is a JSON object whose `findings` field lists what a reviewer found wrong with the
work already in this tree. Fix every finding. The work is already here — read it first, then
change what the findings point at. Do not start again, and do not go beyond the findings and
the original request.

## How to work

- Read enough of the repository to match what is already there: its language, its layout, its
  conventions.
- Keep the change as small as what was asked for. No refactoring nearby code, no new dependencies.
- If the repository has an obvious way to build or test itself, use it before you finish.
- If what was asked for is ambiguous, pick the reading a careful colleague would and say which
  in your closing message, rather than stopping to ask.
