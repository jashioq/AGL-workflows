# What finished workflow code looks like

Each rule shows what to keep and what to change, taken from real workflows.

## Comments

Every line a reader would stop at and ask why gets a comment saying why, in one line. The builder
writes none, so each one is added when cleaning. A comment that says what its line does is
deleted, not shortened.

Work the why out from the code and the SDK, which is all the next reader has. A comment explains
the code as it stands, never how it came to be written or who asked for it.

Write them in the voice of the ones people wrote by hand: plain words a colleague would say out
loud, a spaced hyphen where a writer would reach for a dash, and no full stop needed.

    add      # The echoed answer throws off where the terminal redraws from, so old questions stay behind
     above   print("\x1b[2J\x1b[H", end="", file=sys.__stdout__, flush=True)
    keep     # If after MAX_ROUNDS review rounds issues are still found - stop.
    keep     # Both loops are capped because nobody is watching the agents answer each other
    delete   # Review and fix loop
    delete   # Run parameters, supplied by the user
    delete   # Define agents. 'watch' is a callback to display agent's activity string in the terminal.
    cut      # Where the loader check runs, and the same checkout every step of this run works in.
             # There is no `run.verify` on the version this workflow requires, so the address is...
     to one  # Load it in this run's own checkout, so the reviewer starts from a verdict, not a guess

## As few classes as possible

A dataclass with one field is that field.

    collapse   @dataclass(frozen=True, slots=True)
               class Changes:
                   asked: str
       into    str

A class named in `accepts=` collapses the same way. The entry, the placeholder, what the prompt
says about the input, and every step that passes it all change together, and the value handed
over stays the same. Write a builtin bare: `accepts=(list,)`, never `list[str]`, which is
refused. A type already in the tuple cannot be added twice, so that class stays.

    change   accepts=(Design, Changes)   {{<Changes>}}   "a JSON object whose `asked` field..."
             run.step(designing, design, Changes(answer))
       to    accepts=(Design, str)       {{<str>}}       "a JSON string, what they typed"
             run.step(designing, design, answer)

A class stays when the SDK reads it. A payload behind a tool is one: its `describe()` fields are
the schema the model fills in, so the class is the interface. `Parameters` is another, because
`@workflow` reads the flags off it.

    keep   @dataclass(frozen=True, slots=True)
           class Review:
               findings: list[str] = describe(
                   "each finding as one markdown item saying where and what is wrong; empty when there are none"
               )

           record_review = reporting_tool("record_review", "Record this review's findings. ...", Review)

A class the SDK already has is not written again.

    delete   class Loaded: passed: bool; status: int; output: str; truncated: bool
       use   VerifierOutcome, which run.verify already returns

A function with no arguments that returns the same thing every time is a constant, unless the
SDK needs a function there, as `@role` does.

    change   def record_review() -> ReportingTool[Review]:
                 return reporting_tool("record_review", "...", Review)
       to    record_review = reporting_tool("record_review", "...", Review)

## Readable in two seconds

Every function call, class and abstraction costs the reader effort, and each one has to pay for
itself. The plain version wins even when it is one character longer.

    keep     for round_number in range(MAX_ROUNDS):
                 ...
                 if round_number == MAX_ROUNDS - 1:
                     break
    change   for rounds_left in reversed(range(MAX_ROUNDS)):   (backwards, to dodge the - 1)
    change   NOTHING_SAID: Final = Changes("")
             while (answer := await run.terminal.show(approval, design=design)) == NOTHING_SAID:
                 pass
       to    a blank answer the screen simply comes back from, with no sentinel
    change   _AGL: Final = Path(sys.executable).parent / "agl"   (a constant used once)
       to    agl = Path(sys.executable).with_name("agl")        (a local, where it is used)

## Separation of concerns, and no over-splitting

`__init__.py` is the shape, `display.py` is display state and screens, `roles.py` is payloads,
tools and role factories, and `prompts/` is one file per role. Nothing else gets a file of its own.

    change   asking.py, 46 lines around one tool
       to    that tool in roles.py and its screen in display.py

## Rules that hold here too

The cleaner keeps these. It never relaxes them.

- Every model names its effort: `Claude.OPUS(effort=ClaudeEffort.HIGH)`, never a bare
  `Claude.OPUS`.
- No code and no prompt commits, branches, pushes or stages, or asks an agent to. AGL commits.
- Every step that writes passes `commit=`, a few words saying what it did, with the round for
  looped work: `commit=f"fix what review round {round_number + 1} found"`. A step that only
  reports passes none.
- Roles are bound at module level, so `agl workflows <name>` checks each prompt against its
  `accepts=`.
