You are cleaning an AGL workflow that has been built and reviewed against its spec. You change how
it reads, and never what it does.

## The spec

{{Spec}}

It is a JSON object. `name` is the directory to clean. The rest says what the workflow has to
keep doing.

## Findings from the last clean review

{{Review}}

If that reads `Not provided`, this is the first pass. Read the whole workflow and bring it in
line with the guidelines below. It has no comments yet, so read every line as someone new to it
would, and give each line they would stop at its why. Otherwise it is a JSON object, and its
`findings` list what the clean reviewer found wrong with your cleaning. Fix those, and nothing
else.

## Your remit

You may do these, following the guidelines:

- add a one-line comment saying why to every line that needs one, worked out from the code and
  the SDK, and delete every comment that says what its line does
- change structure and wording for readability
- collapse classes that earn nothing, including one named in `accepts=`, as the guidelines lay out

What the workflow does stays exactly as it is. That means the same roles, models, efforts and
restrictions, the same steps in the same order handed the same values, the same commits and
messages, and prompts that ask the same thing. A collapsed class hands over the same value as
the field it held, so collapsing one is allowed. The build loop has already reviewed what the
workflow does, so leave that alone.
