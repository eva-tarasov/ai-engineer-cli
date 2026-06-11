### Experiment: unconstrained vs constrained response

Prompt:

`Explain what dependency injection is and why it is useful in iOS development.`

| Test | Format | Max output tokens | Stop instruction | Result       | Notes |
|---|---|---:|---|--------------|---|
| 1 | text | none | none | success      | Free-form answer |
| 2 | markdown | none | none | success      | More readable |
| 3 | json | none | none | success      | Machine-readable if valid |
| 4 | markdown | 120 | none | success & fail | Shorter answer |
| 5 | markdown | 120 | Finish with END | success & fail  | Checks instruction following |
| 6 | json | 160 | Keep JSON compact | success & fail  | Tests structured output under token limit |