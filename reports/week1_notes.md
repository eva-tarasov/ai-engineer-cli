## Day 2
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


## Day 3 — Prompt templates

### What I built

- Added `prompts/` directory inside the Python package.
- Added reusable prompt templates:
  - `explain_concept`
  - `explain_code`
  - `compare_options`
  - `summarize`
  - `solve_step_by_step`
  - `create_solution_prompt`
  - `expert_group_solution`
- Added `prompt_templates.py`.
- Added `--template` CLI argument.
- Added `--list-templates` CLI argument.
- Added error handling for missing templates.
- Preserved old CLI behavior without templates.

### Commands tested

- `PYTHONPATH=src python -m ai_engineer_cli.cli --list-templates`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "Dependency injection in iOS" --template explain_concept --format markdown`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "UIKit vs SwiftUI for a legacy iOS app" --template compare_options --format markdown`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "func configure(title: String) { titleLabel.text = title }" --template explain_code --format markdown`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "Test" --template unknown_template`

### Experiment 1: same input, different templates

Input:

`Dependency injection in iOS`

| Template | Result | Notes |
|---|---|---|
| explain_concept | success | Best fit for explaining the topic |
| compare_options | success | Template expects two options, so the result may be less natural |
| summarize | success | Template expects longer text to summarize |

### Experiment 2: solving one task with different prompting strategies

Problem:

`Given an integer array nums, return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i]. Solve it without using division and in O(n) time. Explain the approach and provide a Swift solution.`

| Method | Template | Result | Notes |
|---|---|---|---|
| Direct answer | none | success | Baseline answer |
| Step-by-step | solve_step_by_step | success | More structured explanation |
| Generated prompt | create_solution_prompt + second request | success | Better task framing, but costs two calls |
| Expert group | expert_group_solution | success | More complete review, but may be verbose |

### Comparison

- Did the answers differ?
- Which answer had the clearest algorithm?
- Which answer had the best Swift code?
- Which answer handled edge cases better?
- Which method was too verbose?
- Which method gave the most accurate result?

### Engineering conclusion

Prompt templates are reusable behavioral contracts for LLM calls. They make prompts versionable, testable, and easier to improve.

Different prompting strategies change the quality and structure of the answer. Direct prompts are fast, step-by-step prompts are better for learning, generated prompts can improve task framing, and expert-group prompts are useful for review but may be too verbose for simple tasks.

### Small UX improvements before Day 4

Added:
- `--language ru|en` to control response language.
- Russian is the default response language.
- Visual response separators for better terminal readability.
- `--no-separator` for raw output mode.

Commands tested:

- `PYTHONPATH=src python -m ai_engineer_cli.cli "Explain dependency injection in iOS" --template explain_concept --format markdown --language ru`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "Explain dependency injection in iOS" --template explain_concept --format markdown --language en`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "Explain dependency injection in iOS" --template explain_concept --format markdown --language ru --no-separator`

Conclusion:

Language and output formatting are part of CLI usability. A developer tool should not only produce correct answers, but also make them easy to read and control.