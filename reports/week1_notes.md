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

## Day 4 — Temperature and generation control

### What I built

- Added `--temperature` CLI argument.
- Passed `temperature` from CLI to `LLMClient`.
- Added validation: temperature must be between 0 and 2.
- Preserved existing CLI parameters:
  - `--format`
  - `--language`
  - `--max-output-tokens`
  - `--stop-instruction`
  - `--template`
  - `--list-templates`
  - `--no-separator`

### Commands tested

- `PYTHONPATH=src python -m ai_engineer_cli.cli --help`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "Test" --temperature -1`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "Test" --temperature 3`

### Experiment 1: creative task

Prompt:

`Придумай 7 названий для CLI-инструмента разработчика, который помогает работать с LLM, prompt templates, логами и анализом кода.`

| Temperature | Accuracy | Creativity | Diversity | Notes |
|---:|---|---|---|---|
| 0 | high/medium/low | high/medium/low | high/medium/low | TODO |
| 0.7 | high/medium/low | high/medium/low | high/medium/low | TODO |
| 1.2 | high/medium/low | high/medium/low | high/medium/low | TODO |

### Experiment 2: technical explanation

Prompt:

`Объясни, почему для Product of Array Except Self нельзя использовать деление, если в массиве есть нули.`

| Temperature | Accuracy | Creativity | Diversity | Notes |
|---:|---|---|---|---|
| 0 | high/medium/low | high/medium/low | high/medium/low | TODO |
| 0.7 | high/medium/low | high/medium/low | high/medium/low | TODO |
| 1.2 | high/medium/low | high/medium/low | high/medium/low | TODO |

### Practical conclusions

- `temperature = 0` is best for code review, JSON output, technical instructions, deterministic explanations, and tasks where stability matters.
- `temperature = 0.7` is good for balanced explanations, learning, documentation drafts, and idea generation with reasonable control.
- `temperature = 1.2` is better for brainstorming and creative exploration, but it may reduce precision and produce less practical answers.

### Engineering conclusion

Temperature controls variability, not intelligence. For developer tools, low temperature should be the default for correctness-sensitive tasks. Higher temperature can be useful for brainstorming, naming, and alternative ideas, but outputs need stronger review.

## Day 5 — Model selection and response metrics

### Theory notes

Model selection is an engineering trade-off between quality, latency, cost, and reliability.

For this experiment I used `gpt-5-nano`, `gpt-5-mini`, and `gpt-5` because they belong to the same provider family and represent a clear weak/medium/strong progression. This keeps the experiment controlled: same API, same prompt, same parameters, different model tier.

Small models are usually better for simple, frequent, low-risk tasks. Medium models are useful as default balanced options. Strong models are better for complex reasoning, architecture review, code analysis, and tasks where wrong answers are expensive.

Token usage matters because API cost is usually calculated from input and output tokens. Duration matters because CLI tools should feel responsive.

### GPT-5 temperature compatibility note

During testing, GPT-5 models returned an API error when `temperature` was passed:

`Unsupported parameter: 'temperature' is not supported with this model.`

I updated `LLMClient` to send `temperature` only for models that support it. For GPT-5 models, the CLI accepts `--temperature`, but the parameter is not sent to the API.

Engineering conclusion: model capabilities differ, so CLI parameters must be provider/model-aware.

### What I built

- Updated default model to `gpt-5-mini`.
- Added `--model` CLI argument.
- Added model override on top of `OPENAI_MODEL`.
- Added `LLMResponse` dataclass.
- Added duration measurement.
- Added token usage extraction.
- Added estimated cost calculation.
- Added metadata output.
- Added `--no-metadata`.

### Commands tested

- `PYTHONPATH=src python -m ai_engineer_cli.cli --help`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "Кратко объясни, что такое model selection в LLM API" --format markdown --language ru --temperature 0`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "Кратко объясни, что такое model selection в LLM API" --format markdown --language ru --temperature 0 --model gpt-5-nano`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "Кратко объясни, что такое model selection в LLM API" --format markdown --language ru --temperature 0 --model gpt-5-mini`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "Кратко объясни, что такое model selection в LLM API" --format markdown --language ru --temperature 0 --model gpt-5`
- `PYTHONPATH=src python -m ai_engineer_cli.cli "Кратко объясни, что такое model selection в LLM API" --format markdown --language ru --model gpt-5-mini --no-metadata`

### GPT-5 max_output_tokens observation

During testing, `--max-output-tokens 700` was too low for the Product of Array Except Self task.

Observed result:

| Model | Result with max_output_tokens=700 |
|---|---|
| gpt-5-nano | no visible answer |
| gpt-5-mini | truncated answer |
| gpt-5 | no visible answer |

Reasoning models may use part of the output token budget for internal reasoning. If the token budget is too small, the response can become incomplete before visible text is produced.

Engineering conclusion: `max_output_tokens` should not be used as a normal “make answer shorter” control for reasoning-heavy tasks. It is a hard safety limit. For model comparison, it is better to remove it or set it high enough.

### Experiment1: weak vs medium vs strong model

Prompt:

`Объясни, как работает задача Product of Array Except Self. Дай Swift-решение, сложность, edge cases и короткое ревью возможных ошибок.`

Fixed parameters:

- format: markdown
- language: ru
- temperature: 0

| Model | Tier | Duration | Input tokens | Output tokens | Total tokens | Estimated cost | Quality notes |
|---|---|---:|---:|---:|---:|---:|---|
| gpt-5-nano | weak | 22.56 | 79 | 2817 | 2896 | 0.00113075 | Good |
| gpt-5-mini | medium | 21.62 | 79 | 1928 | 2007 | 0.00387575 | Good |
| gpt-5 | strong | 23.22 | 79 | 2176 | 2255 | 0.02185875 | Very good |

### Experiment2: medium vs strong model

Prompt:

`Explain how the “Product of Array Except Self” problem works. Provide a Swift solution, the complexity, edge cases, and a brief review of potential errors.`

Fixed parameters:

- format: markdown
- language: en
- temperature: 0

| Model | Tier | Duration | Input tokens | Output tokens | Total tokens | Estimated cost | Quality notes |
|---|---|---:|---:|---:|---:|---:|---|
| gpt-5-mini | medium | 22.66 | 77 | 1573 | 1650 | 0.00316525 | Good |
| gpt-5 | strong | 23.05 | 77 | 1964 | 2041 | 0.01973625 | good |

### Quality checklist

| Criterion | gpt-5-nano | gpt-5-mini | gpt-5 |
|---|---|---|---|
| No division | yes/no | yes/no | yes/no |
| Prefix/suffix algorithm | yes | yes | yes |
| Swift code quality | high | high | high |
| Complexity explanation | partial | good | good |
| Handles one zero | yes/no | yes/no | yes/no |
| Handles two zeros | yes/no | yes/no | yes/no |
| Useful error review | good | good | good |

### Engineering conclusion

Model choice should depend on the task. Cheap models can be enough for simple explanations and repetitive tasks. Medium models are good default candidates. Strong models are better for complex code review and reasoning, but they cost more and may be slower.

For `ai-engineer-cli`, model selection should be explicit and measurable, not based on vague impressions.