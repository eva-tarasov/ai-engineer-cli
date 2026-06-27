# ai-engineer-cli

CLI-инструмент для работы с LLM как с инженерным помощником.

Проект создаётся в рамках 7-недельного курса по LLM/API/агентам/CLI/RAG/MCP/локальным моделям. Идея проекта — постепенно развить простой LLM API client в управляемого developer assistant, который умеет работать с историей диалога, конфигами сессий, стратегиями контекста и инженерными сценариями.

---

## Current status

На конец **Week 2 / Agent Core** проект умеет:

- отправлять prompt в LLM API;
- выбирать модель через `.env` или CLI-флаг `--model`;
- выбирать формат ответа: `text`, `markdown`, `json`;
- валидировать JSON-ответы модели;
- выбирать язык ответа: `ru`, `en`;
- использовать prompt templates;
- задавать ограничение на output tokens;
- добавлять stop instruction;
- управлять `temperature` для моделей, которые это поддерживают;
- выводить metadata по запросу: модель, время, токены, примерная стоимость;
- форматировать ответ в терминале в читаемые блоки;
- запускаться в direct mode или agent mode;
- хранить историю диалога между запусками CLI;
- хранить настройки диалога в conversation config;
- очищать историю диалога, не удаляя config;
- полностью удалять conversation file;
- считать примерное количество токенов текущего запроса, истории и полного контекста;
- предупреждать о превышении заданного context token limit;
- сжимать старую историю в summary;
- хранить summary отдельно от сообщений;
- использовать разные стратегии управления контекстом:
  - `full`;
  - `summary`;
  - `sliding-window`;
  - `sticky-facts`;
  - `branching`;
- извлекать и хранить durable facts в key-value формате;
- создавать и использовать ветки диалога;
- сравнивать разные варианты решения в независимых branches.

---

## Project structure

Основная структура проекта:

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
│       ├── terminal_ui.py
│       ├── prompts/
│       │   ├── compare_options.md
│       │   ├── create_solution_prompt.md
│       │   ├── expert_group_solution.md
│       │   ├── explain_code.md
│       │   ├── explain_concept.md
│       │   ├── extract_facts.md
│       │   ├── solve_step_by_step.md
│       │   ├── summarize.md
│       │   └── summarize_history.md
│       └── agent/
│           ├── __init__.py
│           ├── agent.py
│           ├── conversation_config.py
│           ├── facts_manager.py
│           ├── message.py
│           ├── message_store.py
│           ├── summary_manager.py
│           ├── token_budget.py
│           └── strategies/
│               ├── __init__.py
│               ├── base.py
│               ├── branching.py
│               ├── sliding_window.py
│               └── sticky_facts.py
├── docs/
│   └── runtime-flow.md
├── reports/
│   └── week2_notes.md
├── .env
├── .gitignore
└── README.md
```

> В архиве проекта пакет может лежать сразу как `ai_engineer_cli/`, но в рабочей структуре курса используется путь `src/ai_engineer_cli/`.

---

## Installation

Создать виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Установить зависимости:

```bash
pip install openai python-dotenv
```

Создать `.env` в корне проекта:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5-mini
```

---

## Running the CLI

Базовый запуск через Python:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Кратко объясни, что такое JSON validation"
```

Для удобства можно добавить shell-функцию `bear` в `~/.zshrc`:

```bash
bear() {
  PYTHONPATH=src python -m ai_engineer_cli.cli "$@"
}
```

После этого можно запускать так:

```bash
bear "Кратко объясни, что такое JSON validation"
```

---

## Direct mode

Direct mode — это простой одноразовый запрос к LLM без сохранения истории.

```bash
bear "Кратко объясни, что такое JSON validation" --format markdown --language ru
```

В этом режиме путь выполнения короткий:

```text
cli.py
→ build_system_prompt(...)
→ LLMClient.ask(...)
→ OpenAI Responses API
→ print_cli_response(...)
```

Direct mode подходит для быстрых одноразовых вопросов.

---

## Agent mode

Agent mode включает runtime-слой над `LLMClient`.

```bash
bear "Меня зовут Евгений. Я строю ai-engineer-cli." --agent --conversation-id demo
```

Следующий запрос с тем же `conversation-id` сможет использовать сохранённую историю:

```bash
bear "Как меня зовут и какой проект я строю?" --agent --conversation-id demo
```

В agent mode путь выполнения длиннее:

```text
cli.py
→ MessageStore
→ ConversationConfig
→ Agent.run(...)
→ load history / summary / facts / branch
→ build context
→ LLMClient.ask_messages(...)
→ save updated history
→ print_cli_response(...)
```

---

## Conversation config

Чтобы не передавать много флагов в каждой команде, настройки можно сохранить в config конкретного диалога.

Создание config:

```bash
bear --init-conversation day10-facts-bot \
  --agent \
  --format markdown \
  --language ru \
  --show-context-stats \
  --context-strategy sticky-facts \
  --recent-messages 4
```

После этого можно писать коротко:

```bash
bear "Сообщение 1. Я хочу создать Telegram-бота с нуля." --conversation-id day10-facts-bot
```

Посмотреть config:

```bash
bear --show-conversation-config --conversation-id day10-facts-bot
```

Очистить history, summary, facts и branches, но сохранить config:

```bash
bear --clear-history --conversation-id day10-facts-bot
```

Полностью удалить conversation file:

```bash
bear --delete-conversation --conversation-id day10-facts-bot
```

Conversation хранится в одном JSON-файле:

```text
.agent_data/conversations/{conversation_id}.json
```

Пример структуры:

```json
{
  "conversation_id": "day10-facts-bot",
  "config": {
    "agent": true,
    "response_format": "markdown",
    "language": "ru",
    "show_context_stats": true,
    "use_summary": false,
    "summary_every": 10,
    "recent_messages": 4,
    "context_token_limit": null,
    "context_strategy": "sticky-facts",
    "branch_id": "main",
    "model": null,
    "max_output_tokens": null,
    "temperature": null,
    "stop_instruction": null
  },
  "summary": null,
  "facts": {},
  "messages": [],
  "branches": {
    "main": {
      "parent": null,
      "checkpoint_message_index": 0,
      "messages": []
    }
  }
}
```

---

## Config merge order

Runtime settings вычисляются в `cli.py` через функцию `pick(...)`.

Приоритет такой:

```text
1. Явно переданный CLI flag
2. Stored conversation config
3. Hardcoded default
```

Пример: если в config сохранён `language: ru`, но в конкретном запуске передать `--language en`, то один запрос выполнится на английском.

---

## Context strategies

На конец Week 2 агент поддерживает несколько стратегий управления контекстом.

### 1. Full

```bash
bear --init-conversation demo-full \
  --agent \
  --format markdown \
  --language ru \
  --context-strategy full
```

Контекст:

```text
system prompt
+ full history
+ current user message
```

Плюсы:

- максимум деталей;
- хорошая точность на коротких и средних диалогах.

Минусы:

- история постоянно растёт;
- input tokens и стоимость растут;
- можно упереться в context limit.

---

### 2. Summary

```bash
bear --init-conversation demo-summary \
  --agent \
  --format markdown \
  --language ru \
  --context-strategy summary \
  --summary-every 10 \
  --recent-messages 6
```

Контекст:

```text
system prompt
+ conversation summary
+ recent messages
+ current user message
```

Старые сообщения сжимаются через `SummaryManager`, summary хранится отдельно в conversation JSON.

Плюсы:

- меньше токенов на длинных диалогах;
- сохраняет основные цели, решения и ограничения.

Минусы:

- summary может потерять мелкие детали;
- создание summary требует дополнительного LLM-вызова.

---

### 3. Sliding Window

```bash
bear --init-conversation demo-sliding \
  --agent \
  --format markdown \
  --language ru \
  --context-strategy sliding-window \
  --recent-messages 4
```

Контекст:

```text
system prompt
+ last N messages
+ current user message
```

Плюсы:

- просто;
- дёшево;
- хорошо для коротких локальных задач.

Минусы:

- старые факты отбрасываются;
- плохо подходит для длинного сбора требований.

---

### 4. Sticky Facts

```bash
bear --init-conversation demo-facts \
  --agent \
  --format markdown \
  --language ru \
  --show-context-stats \
  --context-strategy sticky-facts \
  --recent-messages 4
```

Контекст:

```text
system prompt
+ sticky facts
+ last N messages
+ current user message
```

Facts — это key-value память, которая хранится в conversation JSON:

```json
"facts": {
  "project": "telegram_bot",
  "goal": "Build a Telegram bot from scratch without no-code builders",
  "architecture_rule": "Handlers must not access the database directly"
}
```

`FactsManager` обновляет facts после каждого user message. Если модель вернула невалидный JSON при извлечении facts, агент не падает, а продолжает работу со старыми facts.

Плюсы:

- хорошо сохраняет цели, ограничения, предпочтения и архитектурные решения;
- удобен для проектной памяти;
- дешевле полной истории на длинной дистанции.

Минусы:

- facts extraction требует дополнительного LLM-вызова;
- качество зависит от модели;
- facts могут быть неполными или устаревшими.

---

### 5. Branching

```bash
bear --init-conversation demo-branching \
  --agent \
  --format markdown \
  --language ru \
  --show-context-stats \
  --context-strategy branching \
  --branch main
```

Создать ветки:

```bash
bear --create-branch json-storage --from-branch main --conversation-id demo-branching
bear --create-branch sqlite-storage --from-branch main --conversation-id demo-branching
```

Продолжить одну ветку:

```bash
bear "Развиваем вариант JSON storage." \
  --conversation-id demo-branching \
  --context-strategy branching \
  --branch json-storage
```

Продолжить другую ветку:

```bash
bear "Развиваем вариант SQLite storage." \
  --conversation-id demo-branching \
  --context-strategy branching \
  --branch sqlite-storage
```

Посмотреть ветки:

```bash
bear --list-branches --conversation-id demo-branching
```

Плюсы:

- удобно сравнивать архитектурные варианты;
- ветки не смешивают историю;
- подходит для исследования альтернатив.

Минусы:

- требует явного управления branches;
- сложнее, чем обычный линейный диалог.

---

## Token tracking

Агент умеет показывать примерную статистику контекста:

```bash
bear "Что ты помнишь по проекту?" \
  --conversation-id demo-facts \
  --show-context-stats
```

Вывод в metadata может содержать:

```text
context messages: 6
history messages: 4
estimated current request tokens: 18
estimated history tokens: 120
estimated full context tokens: 190
```

Важно:

- `TokenBudget` даёт примерную оценку до запроса;
- реальные `input_tokens`, `output_tokens`, `total_tokens` приходят из API после ответа;
- стоимость считается через `model_pricing.py`.

Можно задать warning limit:

```bash
bear "Проверь контекст" \
  --conversation-id demo-facts \
  --context-token-limit 1000
```

Если estimated full context tokens превышает лимит, в metadata появится предупреждение.

---

## Prompt templates

Посмотреть доступные шаблоны:

```bash
bear --list-templates
```

Использовать шаблон:

```bash
bear "Что такое dependency injection?" --template explain_concept --format markdown --language ru
```

Шаблоны лежат в:

```text
src/ai_engineer_cli/prompts/
```

---

## JSON response mode

Запросить JSON:

```bash
bear "Объясни dependency injection" --format json --language ru
```

В этом режиме `response_format.py` добавляет в system prompt требование вернуть валидный JSON, а затем CLI вызывает:

```python
validate_json_response(llm_response.text)
```

Если модель вернёт невалидный JSON, CLI завершится с ошибкой.

---

## Metadata

По умолчанию CLI выводит ответ и metadata.

Пример metadata:

```text
mode: agent
model: gpt-5-mini
duration: 7.04s
tokens: 55 input / 516 output / 571 total
estimated cost: $0.00104575
conversation_id: day10-facts-bot
summary enabled: False
context strategy: sticky-facts
facts enabled: True
```

Отключить metadata:

```bash
bear "Ответь коротко" --no-metadata
```

Вывести без визуальных box-разделителей:

```bash
bear "Ответь коротко" --no-separator
```

---

## Runtime flow

Подробный runtime flow вынесен в отдельный документ:

```text
docs/runtime-flow.md
```

Он объясняет путь выполнения команды от терминала до ответа модели:

```text
user command
→ cli.py
→ argparse
→ conversation config
→ effective settings
→ direct mode or agent mode
→ context strategy
→ LLMClient
→ OpenAI API
→ save state
→ terminal output
```

---

## Key files

### `cli.py`

Главная точка входа CLI.

Отвечает за:

- парсинг аргументов;
- conversation management commands;
- config merge;
- validation;
- выбор direct или agent mode;
- сбор metadata;
- вывод результата.

### `llm_client.py`

Низкоуровневый клиент для OpenAI API.

Отвечает за:

- вызов Responses API;
- поддержку single prompt и message list;
- измерение duration;
- извлечение token usage;
- подсчёт estimated cost.

### `agent/agent.py`

Agent runtime.

Отвечает за:

- загрузку истории;
- загрузку summary и facts;
- выбор context strategy;
- сбор сообщений для LLM;
- вызов `LLMClient.ask_messages(...)`;
- сохранение обновлённой истории.

### `agent/message_store.py`

JSON-хранилище conversation state.

Хранит:

- config;
- summary;
- facts;
- messages;
- branches.

### `agent/conversation_config.py`

Модель настроек диалога.

### `agent/token_budget.py`

Оценка токенов текущего запроса, истории и полного контекста.

### `agent/summary_manager.py`

Создаёт и обновляет summary старой истории.

### `agent/facts_manager.py`

Извлекает durable facts в key-value формате.

### `agent/strategies/`

Содержит стратегии управления контекстом:

- `SlidingWindowStrategy`;
- `StickyFactsStrategy`;
- `BranchingStrategy`.

---

## Week 1 result

Week 1 превратил проект в управляемый LLM API client.

Ключевые результаты:

- CLI умеет отправлять prompt в LLM;
- поддерживает форматы ответа;
- поддерживает языки ответа;
- поддерживает templates;
- умеет ограничивать output tokens;
- умеет работать с model selection;
- показывает metadata, token usage и estimated cost.

---

## Week 2 result

Week 2 превратил проект из stateless CLI client в agent runtime.

Ключевые результаты:

- появился `Agent` как отдельный слой над `LLMClient`;
- появилась модель `Message`;
- появилась persistent history;
- появился `MessageStore`;
- появился `ConversationConfig`;
- появился token tracking;
- появилась summary compression;
- появились sticky facts;
- появились branches;
- появились context strategies;
- CLI стал поддерживать long-running sessions.

Главная архитектурная идея Week 2:

```text
LLMClient = how to call the model
Agent = how to manage context around the model
```

---

## Current limitations

На конец Week 2 проект ещё имеет ограничения:

- token counting до запроса приблизительный;
- summary compression основана на количестве сообщений, а не на реальном token budget;
- facts extraction зависит от качества ответа модели;
- branches пока реализованы просто через JSON;
- нет полноценного retry/repair механизма для structured JSON;
- нет RAG;
- нет tool calling;
- нет MCP;
- нет локальных моделей;
- нет автоматических тестов runtime-сценариев.

---

## Next steps

Дальше по курсу логично двигаться в сторону Week 3 — Controlled Assistant.

Возможные следующие задачи:

- добавить task state machine;
- добавить инварианты состояния;
- добавить controlled execution flow;
- добавить stricter JSON/structured output layer;
- добавить tests для Agent runtime;
- добавить evaluation сценарии для context strategies;
- подготовить основу для tools и MCP.

---

## Example commands

Direct mode:

```bash
bear "Кратко объясни, что такое runtime в iOS" --format markdown --language ru
```

Agent session:

```bash
bear --init-conversation ios-prep \
  --agent \
  --format markdown \
  --language ru \
  --show-context-stats \
  --context-strategy sticky-facts \
  --recent-messages 6

bear "Готовлюсь к iOS-собеседованию. Начнём с ARC." --conversation-id ios-prep
bear "Что ты уже знаешь о моей подготовке?" --conversation-id ios-prep
```

Telegram bot engineering scenario:

```bash
bear --init-conversation telegram-bot-spec \
  --agent \
  --format markdown \
  --language ru \
  --show-context-stats \
  --context-strategy sticky-facts \
  --recent-messages 4

bear "Я хочу с нуля создать Telegram-бота без конструкторов." --conversation-id telegram-bot-spec
bear "Нужны архитектура, PostgreSQL, Docker, деплой и тесты." --conversation-id telegram-bot-spec
bear "Собери пошаговое ТЗ." --conversation-id telegram-bot-spec
```
