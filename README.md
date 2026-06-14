# ai-engineer-cli

CLI-инструмент для работы с LLM как с инженерным инструментом.

Проект создаётся в рамках 7-недельного курса по управлению LLM/API/агентами/CLI/RAG/MCP/локальными моделями. Цель — постепенно развить простой LLM API client в developer assistant.

## Current status

На конец Week 1 проект умеет:

- отправлять prompt в LLM API;
- выбирать формат ответа: `text`, `markdown`, `json`;
- выбирать язык ответа: `ru`, `en`;
- использовать prompt templates;
- задавать ограничение на output tokens;
- добавлять инструкцию завершения ответа;
- управлять `temperature` для моделей, которые это поддерживают;
- выбирать модель через CLI;
- выводить metadata по запросу;
- измерять время ответа;
- показывать token usage;
- считать примерную стоимость запроса.

## Project structure

```text
ai-engineer-cli/
├── src/
│   └── ai_engineer_cli/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── llm_client.py
│       ├── model_pricing.py
│       ├── prompt_templates.py
│       ├── response_format.py
│       └── prompts/
│           ├── compare_options.md
│           ├── create_solution_prompt.md
│           ├── expert_group_solution.md
│           ├── explain_code.md
│           ├── explain_concept.md
│           ├── solve_step_by_step.md
│           └── summarize.md
├── reports/
│   └── week1_notes.md
├── README.md
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

Create virtual environment:

```bash
python3 -m venv .venv
```

Activate environment:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment variables

Create `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5-mini
```

`OPENAI_MODEL` is the default model. It can be overridden with `--model`.

`.env` must not be committed to Git.

Use `.env.example` as a safe template:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5-mini
```

## Basic usage

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Объясни, что такое CLI"
```

Example with Markdown output:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Объясни, что такое CLI" --format markdown --language ru
```

## CLI options

```text
--format text|markdown|json
--language ru|en
--template TEMPLATE
--list-templates
--max-output-tokens N
--stop-instruction TEXT
--temperature FLOAT
--model MODEL
--no-separator
--no-metadata
```

### Options description

```text
--format              controls response format
--language            controls response language
--template            applies prompt template
--list-templates      shows available templates
--max-output-tokens   sets hard output token limit
--stop-instruction    adds finish instruction to system prompt
--temperature         controls randomness where supported
--model               overrides default model
--no-separator        prints raw response without visual separators
--no-metadata         hides model/duration/tokens/cost block
```

## Response formats

Plain text:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Explain CLI" --format text
```

Markdown:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Explain CLI" --format markdown
```

JSON:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Explain CLI" --format json
```

For JSON responses, the CLI validates that the model returned valid JSON.

## Response language

Russian:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Explain dependency injection" --language ru
```

English:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Explain dependency injection" --language en
```

Default language is `ru`.

## Prompt templates

Prompt templates are stored in:

```text
src/ai_engineer_cli/prompts/
```

Available templates:

```text
compare_options
create_solution_prompt
expert_group_solution
explain_code
explain_concept
solve_step_by_step
summarize
```

List templates:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli --list-templates
```

Use a template:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Dependency injection in iOS" --template explain_concept --format markdown --language ru
```

Explain code:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "func configure(title: String) { titleLabel.text = title }" --template explain_code --format markdown --language ru
```

Compare options:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "UIKit vs SwiftUI for a legacy iOS app" --template compare_options --format markdown --language ru
```

Solve a programming task step by step:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Given an integer array nums, return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i]. Solve it without using division and in O(n) time. Explain the approach and provide a Swift solution." --template solve_step_by_step --format markdown --language ru
```

## Model selection

Main Week 1 model set:

```text
gpt-5-nano  — cheap / fast / weaker
gpt-5-mini  — balanced default
gpt-5       — stronger / more expensive
```

Use default model from `.env`:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Объясни model selection в LLM API" --format markdown --language ru
```

Override model:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Объясни Product of Array Except Self" --model gpt-5-nano --format markdown --language ru
```

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Объясни Product of Array Except Self" --model gpt-5-mini --format markdown --language ru
```

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Объясни Product of Array Except Self" --model gpt-5 --format markdown --language ru
```

## Metadata output

By default, the CLI prints metadata after the response:

```text
model
duration_seconds
input_tokens
output_tokens
total_tokens
estimated_cost_usd
```

Example:

```text
METADATA
model: gpt-5-mini
duration_seconds: 2.31
input_tokens: 145
output_tokens: 280
total_tokens: 425
estimated_cost_usd: 0.00059625
```

Hide metadata:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Explain CLI" --no-metadata
```

## Output formatting

By default, the CLI prints visual separators around the response and metadata:

```text
────────────────────────────────────────────────────────────
AI RESPONSE
────────────────────────────────────────────────────────────
```

Print raw output without separators:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Explain CLI" --no-separator
```

This is useful when redirecting output to a file:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Explain CLI" --no-separator --no-metadata > output.md
```

## Temperature

Use `--temperature` to control generation randomness where the model supports it.

Examples:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Придумай 7 названий для CLI-инструмента разработчика" --temperature 0
```

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Придумай 7 названий для CLI-инструмента разработчика" --temperature 0.7
```

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Придумай 7 названий для CLI-инструмента разработчика" --temperature 1.2
```

General rule:

```text
temperature = 0    → stable / deterministic
temperature = 0.7  → balanced
temperature = 1.2  → more diverse / less predictable
```

## Important GPT-5 notes

GPT-5 models may not support `temperature` in the current API setup.

The CLI accepts `--temperature`, but `LLMClient` does not send it for GPT-5 models.

Small `max_output_tokens` values can truncate reasoning-heavy responses.

Observed during Week 1:

```text
--max-output-tokens 700 was too low for a code explanation task.
gpt-5-nano and gpt-5 produced no visible answer.
gpt-5-mini produced a truncated answer.
```

Engineering conclusion:

```text
max_output_tokens is a hard limit, not a normal “make answer shorter” control.
For reasoning-heavy tasks, avoid small max_output_tokens values or set a high enough limit.
```

## Cost estimation

Cost is estimated using local values from:

```text
src/ai_engineer_cli/model_pricing.py
```

Current prices are approximate and should be checked against official provider pricing.

Formula:

```text
cost = input_tokens / 1_000_000 * input_price
     + output_tokens / 1_000_000 * output_price
```

Current model pricing table:

```text
gpt-5-nano  input: $0.05 / 1M tokens, output: $0.40 / 1M tokens
gpt-5-mini  input: $0.25 / 1M tokens, output: $2.00 / 1M tokens
gpt-5       input: $1.25 / 1M tokens, output: $10.00 / 1M tokens
```

## Week 1 result

Week 1 built the foundation of `ai-engineer-cli`.

Implemented:

- Python CLI entry point;
- config layer;
- OpenAI API client;
- response formats;
- JSON validation;
- language control;
- output separators;
- prompt templates;
- constrained output experiments;
- temperature control;
- model selection;
- response metadata;
- duration measurement;
- token usage extraction;
- estimated cost calculation.

Important engineering conclusions:

- LLM API should be wrapped behind a client layer.
- Prompt templates are reusable behavioral contracts.
- Response format is part of the interface between model and application.
- JSON output must be validated.
- Not all models support the same parameters.
- GPT-5 models may not support `temperature`.
- Small `max_output_tokens` can break reasoning-heavy outputs.
- Model choice should be measured by quality, latency, token usage, and cost.

## Next steps

Next: Week 2 — Agent Core.

Planned:

- agent loop;
- task decomposition;
- state between steps;
- simple tool-like actions;
- controlled iteration;
- failure handling;
- preparation for tools and MCP.