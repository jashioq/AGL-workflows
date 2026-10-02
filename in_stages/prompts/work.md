Build one stage of the request below in this repository. The stages before yours are already
built here, and other agents build the later ones after you, so build your stage and nothing
else. Do not commit: AGL commits your work when you finish.

## The request

{{str}}

A JSON string: what the person asked for.

## Every stage

{{Plan}}

A JSON object whose `stages` lists every stage in order.

## Your stage

{{Stage}}

A JSON object: `name`, and `builds` is what to build. If any input reads `Not provided`, stop at
once and write nothing.

Nobody is here to answer questions, so decide what is unclear yourself.
