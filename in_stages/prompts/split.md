Split the request below into stages. Another agent builds them in this repository, one at a time
and in order, so each stage builds on the ones before it. You only plan: write no files.

## The request

{{str}}

A JSON string: what the person asked for.

## How many stages

{{int}}

Make exactly this many. If either input reads `Not provided`, stop at once without calling
`record_plan`.

Nobody is here to answer questions, so decide what is unclear yourself. Then call `record_plan`
once, with every stage in order.
