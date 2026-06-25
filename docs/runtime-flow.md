# ai-engineer-cli Runtime Flow

Документ объясняет, что происходит внутри `ai-engineer-cli`, когда пользователь вводит команду в терминале и нажимает Enter.

Цель документа — не просто перечислить файлы, а показать путь данных по проекту: от CLI-команды до запроса в LLM, сохранения истории, подсчёта токенов и вывода ответа.

Документ написан по фактическому коду из архива проекта.

---

## 1. Что такое `ai-engineer-cli`

`ai-engineer-cli` — это CLI-инструмент для работы с LLM как с инженерным ассистентом.

Сейчас проект умеет работать в двух основных режимах:

```text
Direct mode
  один запрос → один ответ модели

Agent mode
  запрос → агент → история/summary/facts/strategy → модель → сохранение истории → ответ
```

В простом режиме инструмент похож на обычный CLI-клиент к LLM. В agent-режиме он становится runtime-системой: хранит диалоги, конфиги, историю, facts, ветки и умеет по-разному собирать контекст.

---

## 2. Главные файлы проекта

```text
ai_engineer_cli/
├── cli.py                         # входная точка CLI
├── config.py                      # загрузка .env и настроек OpenAI
├── llm_client.py                  # низкоуровневый клиент OpenAI API
├── model_pricing.py               # примерная стоимость запросов
├── prompt_templates.py            # загрузка prompt templates
├── response_format.py             # system prompt, формат ответа, язык, JSON validation
├── terminal_ui.py                 # красивый вывод в терминал
├── prompts/                       # markdown-шаблоны и internal prompts
└── agent/
    ├── agent.py                   # runtime агента
    ├── conversation_config.py     # настройки конкретного диалога
    ├── facts_manager.py           # извлечение sticky facts
    ├── message.py                 # модель сообщения
    ├── message_store.py           # хранение config/summary/facts/messages/branches
    ├── summary_manager.py         # сжатие истории в summary
    ├── token_budget.py            # оценка токенов контекста
    └── strategies/
        ├── base.py                # Protocol для context strategy
        ├── sliding_window.py      # Sliding Window strategy
        ├── sticky_facts.py        # Sticky Facts strategy
        └── branching.py           # Branching strategy
```

---

## 3. Самый короткий общий путь выполнения

Когда пользователь вводит команду:

```bash
bear "Объясни, что такое JSON validation" --format markdown --language ru
```

`bear` — это shell-обёртка вокруг запуска Python-модуля. По сути она запускает что-то вроде:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Объясни, что такое JSON validation" --format markdown --language ru
```

Дальше управление попадает в файл:

```text
ai_engineer_cli/cli.py
```

Общий поток:

```text
terminal
  ↓
cli.py / main()
  ↓
argparse разбирает команду
  ↓
загружается conversation config
  ↓
рассчитываются effective settings
  ↓
собирается system prompt
  ↓
создаётся LLMClient
  ↓
выбирается direct mode или agent mode
  ↓
LLMClient вызывает OpenAI API
  ↓
ответ возвращается в cli.py
  ↓
metadata собирается и печатается через terminal_ui.py
```

---

## 4. Точка входа: `cli.py`

Файл:

```text
ai_engineer_cli/cli.py
```

Главная функция:

```python
def main() -> None:
```

В самом низу файла есть стандартная Python-точка входа:

```python
if __name__ == "__main__":
    main()
```

Это значит: когда модуль запускается как программа, вызывается `main()`.

---

## 5. Шаг 1: разбор CLI-аргументов

В начале `main()` создаётся parser:

```python
parser = build_parser()
args = parser.parse_args()
```

Функция `build_parser()` описывает все доступные аргументы:

```text
prompt
--format
--language
--model
--temperature
--agent
--conversation-id
--init-conversation
--show-conversation-config
--delete-conversation
--clear-history
--show-context-stats
--context-strategy
--branch
--create-branch
--list-branches
...
```

После `parse_args()` все значения доступны через `args`.

Например команда:

```bash
bear "Привет" --conversation-id day10-facts-bot
```

даёт примерно:

```text
args.prompt = "Привет"
args.conversation_id = "day10-facts-bot"
args.agent = None
args.format = None
args.language = None
```

Почему многие значения равны `None`? Это важное решение проекта.

---

## 6. Почему многие CLI-флаги имеют `default=None`

В проекте используется config-aware подход.

Это значит, что настройки могут прийти из трёх мест:

```text
1. Явно переданные CLI flags
2. Config конкретного conversation-id
3. Жёсткие defaults в коде
```

Поэтому для многих флагов в `argparse` стоит `default=None`.

Например:

```python
parser.add_argument(
    "--format",
    choices=[item.value for item in ResponseFormat],
    default=None,
)
```

Если бы стояло `default="text"`, CLI не смог бы понять:

```text
пользователь явно передал --format text
или это просто default от argparse
```

А с `None` можно честно объединять настройки.

---

## 7. Шаг 2: быстрые management-команды

Первой обрабатывается команда:

```bash
bear --list-templates
```

В коде:

```python
if args.list_templates:
    templates = list_templates()
    ...
    return
```

Важно: `--list-templates` не относится к конкретному диалогу, поэтому `MessageStore` ещё не нужен.

После этого создаётся `conversation_id`:

```python
conversation_id = args.init_conversation or args.conversation_id
```

Логика:

```text
если команда --init-conversation day9-summary → conversation_id = day9-summary
иначе берём --conversation-id
если --conversation-id не передан → default
```

Потом создаётся хранилище:

```python
message_store = MessageStore(conversation_id=conversation_id)
stored_config = message_store.load_config()
```

Даже direct mode сейчас проходит через создание `MessageStore`, но если файл не сохраняется, это не создаёт conversation-файл на диске. Файл создаётся только при операциях сохранения.

---

## 8. Conversation management-команды

После создания `message_store` CLI сначала обрабатывает команды управления диалогом.

### 8.1 `--init-conversation`

Команда:

```bash
bear --init-conversation day10-facts-bot \
  --agent \
  --format markdown \
  --language ru \
  --show-context-stats \
  --context-strategy sticky-facts \
  --recent-messages 4
```

В коде:

```python
if args.init_conversation:
    conversation_config = build_conversation_config_from_args(args)
    message_store.save_config(conversation_config)
    ...
    return
```

Что происходит:

```text
1. Из CLI flags собирается ConversationConfig.
2. Config сохраняется в .agent_data/conversations/{conversation_id}.json.
3. Программа печатает config и завершает работу.
```

### 8.2 `--show-conversation-config`

Команда:

```bash
bear --show-conversation-config --conversation-id day10-facts-bot
```

В коде:

```python
if args.show_conversation_config:
    print_conversation_config(conversation_id, stored_config)
    return
```

CLI просто показывает сохранённый config.

### 8.3 `--delete-conversation`

Команда:

```bash
bear --delete-conversation --conversation-id day10-facts-bot
```

В коде:

```python
if args.delete_conversation:
    message_store.delete()
    print(f"Conversation deleted: {conversation_id}")
    return
```

Удаляется весь файл диалога:

```text
config + summary + facts + messages + branches
```

### 8.4 `--list-branches`

Команда:

```bash
bear --list-branches --conversation-id day10-branching-bot
```

В коде:

```python
if args.list_branches:
    branches = message_store.list_branches()
    ...
    return
```

Показывает список веток из conversation JSON.

### 8.5 `--create-branch`

Команда:

```bash
bear --create-branch aiogram-version --from-branch main --conversation-id day10-branching-bot
```

В коде:

```python
if args.create_branch:
    message_store.create_branch(
        branch_id=args.create_branch,
        from_branch_id=args.from_branch,
    )
    ...
    return
```

Создаёт новую ветку от выбранной ветки.

---

## 9. Хранилище диалога: `MessageStore`

Файл:

```text
ai_engineer_cli/agent/message_store.py
```

`MessageStore` отвечает за JSON-файл диалога.

Путь:

```text
.agent_data/conversations/{conversation_id}.json
```

Пример:

```text
.agent_data/conversations/day10-facts-bot.json
```

Формат файла:

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

`MessageStore` умеет:

```text
load_config / save_config
load_messages / save_messages
load_summary / save_summary
load_facts / save_facts
load_branch_messages / save_branch_messages
create_branch
list_branches
clear
delete
```

Важно различать:

```text
clear()  → очищает runtime state, но оставляет config
delete() → удаляет весь conversation JSON
```

`clear()` очищает:

```text
summary
facts
messages
branches
```

но сохраняет:

```text
config
```

---

## 10. Шаг 3: effective settings

После management-команд `cli.py` вычисляет реальные настройки запуска.

Для этого используется функция:

```python
def pick(cli_value, config_value, default_value):
```

Логика:

```text
если CLI value не None → использовать его
иначе если config value не None → использовать его
иначе использовать default value
```

Пример:

```python
effective_format = pick(
    args.format,
    stored_config.response_format,
    ResponseFormat.TEXT.value,
)
```

Если пользователь вызвал:

```bash
bear "Привет" --conversation-id day10-facts-bot
```

и в config лежит:

```json
"response_format": "markdown"
```

то `effective_format` станет:

```text
markdown
```

Если пользователь временно переопределит:

```bash
bear "Привет" --conversation-id day10-facts-bot --format json
```

то `effective_format` станет:

```text
json
```

Потому что CLI flags имеют приоритет выше config.

---

## 11. Полный список effective settings

В `cli.py` вычисляются:

```text
effective_agent
effective_format
effective_language
effective_show_context_stats
effective_use_summary
effective_summary_every
effective_recent_messages
effective_context_token_limit
effective_model
effective_max_output_tokens
effective_temperature
effective_stop_instruction
effective_context_strategy
effective_branch_id
```

Отдельная логика:

```python
if effective_context_strategy == "summary":
    effective_use_summary = True
```

То есть стратегия `summary` автоматически включает summary compression.

---

## 12. Валидация настроек

После вычисления effective settings `cli.py` проверяет корректность.

Примеры проверок:

```text
prompt обязателен, кроме management-команд
max_output_tokens должен быть > 0
temperature должен быть от 0 до 2
context_token_limit должен быть > 0
show_context_stats работает только в agent mode
use_summary работает только в agent mode
recent_messages должен быть > 0
summary_every должен быть > 0
recent_messages должен быть меньше summary_every, если включён summary
context_strategy должен быть одним из допустимых значений
--branch можно использовать только со стратегией branching
```

Если что-то не так, выбрасывается `ValueError`, который ловится в конце `main()`:

```python
except Exception as error:
    print(f"Error: {error}", file=sys.stderr)
    sys.exit(1)
```

---

## 13. Шаг 4: сборка system prompt

Файл:

```text
ai_engineer_cli/response_format.py
```

В `cli.py` создаются enum-значения:

```python
response_format = ResponseFormat(effective_format)
response_language = ResponseLanguage(effective_language)
```

Потом вызывается:

```python
system_prompt = build_system_prompt(
    response_format=response_format,
    language=response_language,
    max_output_tokens=effective_max_output_tokens,
    stop_instruction=effective_stop_instruction,
)
```

`build_system_prompt()` собирает инструкцию для модели.

Например для:

```bash
--format markdown --language ru
```

system prompt будет включать идеи:

```text
You are a helpful engineering assistant.
Keep the answer clear, practical, and technically accurate.
Answer in Russian.
Answer in clean Markdown.
```

Если выбран JSON:

```bash
--format json
```

system prompt дополнительно требует:

```text
Return only valid JSON.
Do not include Markdown.
Do not wrap the JSON in code fences.
Use this structure: {"summary": string, "key_points": [string], "example": string}
```

---

## 14. Шаг 5: prompt templates

Файл:

```text
ai_engineer_cli/prompt_templates.py
```

Если пользователь передал:

```bash
--template explain_code
```

то `cli.py` делает:

```python
template_text = load_template(args.template)
prompt = render_template(
    template_text=template_text,
    user_input=args.prompt,
)
```

Шаблоны лежат в:

```text
ai_engineer_cli/prompts/*.md
```

Например:

```text
explain_code.md
explain_concept.md
solve_step_by_step.md
summarize_history.md
extract_facts.md
```

`render_template()` требует, чтобы в шаблоне был placeholder:

```text
{{input}}
```

Если placeholder отсутствует, будет ошибка:

```text
Template must contain '{{input}}' placeholder.
```

---

## 15. Шаг 6: загрузка `.env` и создание LLMClient

Файл:

```text
ai_engineer_cli/config.py
```

`cli.py` вызывает:

```python
config = load_config()
llm_client = LLMClient(config)
```

`load_config()` делает:

```python
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
```

То есть проект ожидает `.env`:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5-mini
```

Если ключа нет, будет ошибка:

```text
OPENAI_API_KEY is missing.
```

`LLMClient` создаёт внутри себя OpenAI client:

```python
self.client = OpenAI(api_key=config.api_key)
```

---

## 16. Дальше развилка: direct mode или agent mode

В `cli.py` есть развилка:

```python
if effective_agent:
    ... agent mode ...
else:
    ... direct mode ...
```

---

# Часть 1. Direct mode

## 17. Direct mode: что происходит

Direct mode используется, если:

```text
effective_agent == False
```

Пример команды:

```bash
bear "Кратко объясни, что такое JSON validation" --format markdown --language ru
```

В direct mode нет истории, facts, summary и branches.

`cli.py` вызывает:

```python
llm_response = llm_client.ask(
    prompt=prompt,
    system_prompt=system_prompt,
    model=effective_model,
    max_output_tokens=effective_max_output_tokens,
    temperature=effective_temperature,
)
```

---

## 18. Что делает `LLMClient.ask()`

Файл:

```text
ai_engineer_cli/llm_client.py
```

Метод:

```python
def ask(...):
```

Он собирает `input_messages`:

```python
input_messages = []

if system_prompt:
    input_messages.append({"role": "system", "content": system_prompt})

input_messages.append({"role": "user", "content": prompt})
```

То есть в direct mode в модель уходит:

```text
system message
user message
```

Потом собираются параметры запроса:

```python
request_params = {
    "model": selected_model,
    "input": input_messages,
}
```

Если есть `max_output_tokens`, добавляется:

```python
request_params["max_output_tokens"] = max_output_tokens
```

Если есть `temperature` и модель его поддерживает, добавляется:

```python
request_params["temperature"] = temperature
```

Важный момент:

```python
def supports_temperature(model: str) -> bool:
    return not model.startswith("gpt-5")
```

То есть для моделей `gpt-5...` temperature не отправляется.

---

## 19. Вызов OpenAI API

`LLMClient` вызывает Responses API:

```python
response = self.client.responses.create(**request_params)
```

Потом достаёт:

```text
response.output_text
response.usage.input_tokens
response.usage.output_tokens
response.usage.total_tokens
```

И считает примерную стоимость через:

```python
estimate_cost_usd(...)
```

Возвращается объект:

```python
LLMResponse(
    text=response.output_text,
    model=selected_model,
    duration_seconds=duration_seconds,
    input_tokens=input_tokens,
    output_tokens=output_tokens,
    total_tokens=total_tokens,
    estimated_cost_usd=estimated_cost_usd,
)
```

---

# Часть 2. Agent mode

## 20. Agent mode: когда включается

Agent mode используется, если:

```text
effective_agent == True
```

Это может произойти двумя способами.

Первый способ — пользователь явно передал:

```bash
--agent
```

Второй способ — в conversation config сохранено:

```json
"agent": true
```

Например после:

```bash
bear --init-conversation day10-facts-bot \
  --agent \
  --format markdown \
  --language ru \
  --show-context-stats \
  --context-strategy sticky-facts \
  --recent-messages 4
```

потом можно писать коротко:

```bash
bear "Сообщение 1. Проектируем Telegram-бота" --conversation-id day10-facts-bot
```

И agent mode включится из config.

---

## 21. Создание managers в agent mode

В `cli.py` перед созданием `Agent` создаются дополнительные менеджеры.

### SummaryManager

```python
summary_manager = SummaryManager(llm_client=llm_client) if effective_use_summary else None
```

Он нужен только если включено summary-сжатие.

### FactsManager

```python
facts_manager = (
    FactsManager(llm_client=llm_client)
    if effective_context_strategy == "sticky-facts"
    else None
)
```

Он нужен только для стратегии `sticky-facts`.

---

## 22. Создание Agent

Файл:

```text
ai_engineer_cli/agent/agent.py
```

В `cli.py` создаётся:

```python
agent = Agent(
    llm_client=llm_client,
    system_prompt=system_prompt,
    message_store=message_store,
    summary_manager=summary_manager,
    facts_manager=facts_manager,
    use_summary=effective_use_summary,
    recent_messages=effective_recent_messages,
    summary_every=effective_summary_every,
    context_strategy=effective_context_strategy,
    branch_id=effective_branch_id,
)
```

`Agent` получает всё, что ему нужно:

```text
LLMClient
system_prompt
MessageStore
SummaryManager или None
FactsManager или None
настройки summary
context_strategy
branch_id
```

---

## 23. Очистка истории в agent mode

Если команда:

```bash
bear --clear-history --conversation-id day10-facts-bot
```

то в `cli.py`:

```python
if args.clear_history:
    agent.clear_history()
    print(f"History cleared for conversation: {conversation_id}")
    return
```

Внутри `Agent`:

```python
def clear_history(self) -> None:
    if self.message_store:
        self.message_store.clear()
```

А `MessageStore.clear()` очищает:

```text
summary
facts
messages
branches
```

но сохраняет:

```text
config
```

---

## 24. Основной запуск агента: `agent.run()`

Если это обычный prompt, `cli.py` вызывает:

```python
llm_response = agent.run(
    user_input=prompt,
    model=effective_model,
    max_output_tokens=effective_max_output_tokens,
    temperature=effective_temperature,
)
```

Дальше всё управление переходит в:

```text
ai_engineer_cli/agent/agent.py
```

---

## 25. Внутри `Agent.run()`: общий flow

Метод `run()` делает такие шаги:

```text
1. загрузить history
2. загрузить summary
3. загрузить facts
4. если включено summary — при необходимости сжать историю
5. создать user_message
6. если strategy == sticky-facts — обновить facts
7. собрать messages_for_llm
8. посчитать context token stats
9. вызвать LLMClient.ask_messages()
10. создать assistant_message
11. сохранить обновлённую историю
12. вернуть LLMResponse
```

В виде схемы:

```text
Agent.run(user_input)
  ↓
_load_history()
_load_summary()
_load_facts()
  ↓
optional summary compression
  ↓
Message(role="user", content=user_input)
  ↓
optional facts update
  ↓
_build_messages_for_llm()
  ↓
TokenBudget.build_context_stats()
  ↓
LLMClient.ask_messages()
  ↓
Message(role="assistant", content=response.text)
  ↓
_save_history()
  ↓
return LLMResponse
```

---

## 26. Сообщение: `Message`

Файл:

```text
ai_engineer_cli/agent/message.py
```

Сообщение — это dataclass:

```python
@dataclass
class Message:
    role: MessageRole
    content: str
```

Допустимые роли:

```python
MessageRole = Literal["system", "user", "assistant"]
```

Каждое сообщение можно превратить в dict:

```python
message.to_dict()
```

Результат:

```json
{
  "role": "user",
  "content": "Привет"
}
```

А можно восстановить из dict:

```python
Message.from_dict(data)
```

Это используется при чтении/записи JSON-файла диалога.

---

## 27. Загрузка истории

В `Agent.run()`:

```python
history = self._load_history()
```

Если strategy обычная:

```python
return self.message_store.load_messages()
```

Если strategy `branching`:

```python
return self.message_store.load_branch_messages(self.branch_id)
```

То есть:

```text
full / summary / sliding-window / sticky-facts
  → используют общий messages

branching
  → использует messages выбранной branch
```

---

## 28. Summary compression

Summary compression включается, если:

```text
self.use_summary == True
```

В `Agent.run()`:

```python
if self.use_summary:
    summary, history = self._compress_history_if_needed(...)
```

Метод `_compress_history_if_needed()` проверяет:

```text
если SummaryManager отсутствует → ничего не делать
если len(history) < summary_every → ничего не делать
если len(history) <= recent_messages → ничего не делать
```

Если история достаточно длинная:

```text
messages_to_summarize = history без последних recent_messages
recent_history = последние recent_messages
```

Потом вызывается:

```python
updated_summary = self.summary_manager.summarize(...)
```

`SummaryManager` делает отдельный LLM-запрос через:

```python
self.llm_client.ask(...)
```

и сохраняет результат:

```python
self._save_summary(updated_summary)
self._save_history(recent_history)
```

Итог:

```text
старые сообщения → summary
последние N сообщений → остаются как обычная история
```

---

## 29. Sticky Facts

Sticky Facts включается, если:

```text
context_strategy == "sticky-facts"
```

В `Agent.run()`:

```python
if self.context_strategy == "sticky-facts":
    facts = self._update_facts(
        facts=facts,
        messages=[user_message],
        model=model,
        temperature=temperature,
    )
```

То есть facts обновляются после каждого user message, до основного LLM-запроса.

`FactsManager` находится в:

```text
ai_engineer_cli/agent/facts_manager.py
```

Он:

```text
1. загружает prompt из prompts/extract_facts.md
2. берёт existing_facts
3. добавляет новые messages
4. просит LLM вернуть JSON
5. пытается распарсить JSON
6. если JSON плохой — возвращает старые facts
7. если JSON хороший — нормализует и возвращает обновлённые facts
```

Важный момент: facts extraction — вспомогательный механизм.

Если модель вернула плохой JSON, проект больше не падает. Код делает:

```python
if parsed is None:
    return existing_facts
```

Это правильно: плохое обновление facts не должно ломать основной пользовательский запрос.

---

## 30. Сборка контекста: `_build_messages_for_llm()`

После загрузки history/summary/facts агент должен собрать список сообщений для LLM.

Метод:

```python
_build_messages_for_llm(...)
```

Он выбирает стратегию по строке:

```text
self.context_strategy
```

Поддерживаются:

```text
full
summary
sliding-window
sticky-facts
branching
```

---

# Часть 3. Context strategies

## 31. Стратегия `full`

Если `context_strategy == "full"`, код попадает в fallback:

```python
return self._build_full_or_summary_context(...)
```

Если `use_summary == False`, в модель уйдёт:

```text
system prompt
+ full history
+ current user message
```

Это самая полная, но самая дорогая стратегия.

Плюсы:

```text
модель видит всю историю
хорошо помнит детали
```

Минусы:

```text
растут input tokens
растёт стоимость
можно упереться в context limit
```

---

## 32. Стратегия `summary`

В CLI есть логика:

```python
if effective_context_strategy == "summary":
    effective_use_summary = True
```

Дальше агент использует тот же метод:

```python
_build_full_or_summary_context(...)
```

Если summary уже есть, в модель уйдёт:

```text
system prompt
+ Conversation summary
+ recent history
+ current user message
```

Summary создаётся не на каждом запросе, а когда история достигает `summary_every`.

---

## 33. Стратегия `sliding-window`

Файл:

```text
ai_engineer_cli/agent/strategies/sliding_window.py
```

Код выбирается здесь:

```python
if self.context_strategy == "sliding-window":
    return SlidingWindowStrategy(...).build_context(...)
```

В модель уходит:

```text
system prompt
+ последние N сообщений
+ current user message
```

Где N — это:

```text
recent_messages
```

Плюсы:

```text
дешево
просто
предсказуемый размер контекста
```

Минусы:

```text
старые важные решения могут потеряться
```

---

## 34. Стратегия `sticky-facts`

Файл:

```text
ai_engineer_cli/agent/strategies/sticky_facts.py
```

В модель уходит:

```text
system prompt
+ Sticky facts
+ последние N сообщений
+ current user message
```

`StickyFactsStrategy` превращает facts dict в system message:

```text
Sticky facts:
- architecture_rule: Handlers must not access the database directly
- goal: Build a Telegram bot from scratch
- stack: Python, PostgreSQL, Docker
```

Плюсы:

```text
хорошо держит цели, ограничения, решения
дешевле полной истории
удобно для проектной работы
```

Минусы:

```text
facts extraction требует дополнительный LLM-запрос
качество зависит от модели
facts могут обновиться неточно
```

---

## 35. Стратегия `branching`

Файлы:

```text
ai_engineer_cli/agent/strategies/branching.py
ai_engineer_cli/agent/message_store.py
```

Branching позволяет иметь несколько независимых веток внутри одного conversation.

Пример:

```text
day10-branching-bot
├── main
├── aiogram-version
└── python-telegram-bot-version
```

Создание ветки:

```bash
bear --create-branch aiogram-version --from-branch main --conversation-id day10-branching-bot
```

Продолжение ветки:

```bash
bear "Развиваем вариант aiogram" \
  --conversation-id day10-branching-bot \
  --context-strategy branching \
  --branch aiogram-version
```

В agent mode при `context_strategy == "branching"` история загружается так:

```python
self.message_store.load_branch_messages(self.branch_id)
```

и сохраняется так:

```python
self.message_store.save_branch_messages(self.branch_id, messages)
```

То есть каждая ветка имеет собственную историю.

---

## 36. Подсчёт токенов контекста

Файл:

```text
ai_engineer_cli/agent/token_budget.py
```

Класс:

```python
TokenBudget
```

Он не считает токены точно через tokenizer. Он оценивает примерно:

```python
chars_per_token = 4.0
```

Для каждого message:

```text
примерные токены текста + role overhead
```

Перед вызовом LLM агент делает:

```python
self.last_context_token_stats = self.token_budget.build_context_stats(
    current_request=user_message,
    history=history,
    full_context=messages_for_llm,
)
```

В результате CLI может вывести:

```text
context messages
history messages
estimated current request tokens
estimated history tokens
estimated full context tokens
```

Реальные токены приходят уже после API-вызова:

```text
input_tokens
output_tokens
total_tokens
```

Их возвращает OpenAI API в `response.usage`.

---

## 37. Вызов модели в agent mode

После сборки `messages_for_llm` агент вызывает:

```python
response = self.llm_client.ask_messages(
    messages=[message.to_dict() for message in messages_for_llm],
    model=model,
    max_output_tokens=max_output_tokens,
    temperature=temperature,
)
```

Отличие от direct mode:

```text
Direct mode использует LLMClient.ask(prompt, system_prompt)
Agent mode использует LLMClient.ask_messages(messages)
```

`ask_messages()` не собирает system/user messages сам. Он получает уже готовый список сообщений.

---

## 38. Сохранение ответа в историю

После ответа модели агент создаёт assistant message:

```python
assistant_message = Message(
    role="assistant",
    content=response.text,
)
```

Потом формирует новую историю:

```python
updated_history = [
    *history,
    user_message,
    assistant_message,
]
```

И сохраняет:

```python
self._save_history(updated_history)
```

Для обычных стратегий это пишет в:

```json
"messages": []
```

Для branching это пишет в:

```json
"branches": {
  "branch-id": {
    "messages": []
  }
}
```

---

# Часть 4. Ответ обратно в CLI

## 39. JSON validation

После direct или agent mode управление возвращается в `cli.py`.

Если выбран формат JSON:

```python
if response_format == ResponseFormat.JSON:
    validate_json_response(llm_response.text)
```

Функция находится в:

```text
ai_engineer_cli/response_format.py
```

Она проверяет:

```text
ответ парсится как JSON
корневой объект — dict/object
```

Если модель вернула невалидный JSON, CLI завершится с ошибкой.

---

## 40. Metadata

`cli.py` собирает metadata:

```python
metadata = {
    "mode": "agent" if effective_agent else "direct",
    "model": llm_response.model,
    "duration": f"{llm_response.duration_seconds:.2f}s",
    "tokens": f"{input} input / {output} output / {total} total",
    "estimated cost": "...",
}
```

Если это agent mode, добавляется:

```text
conversation_id
summary enabled
context strategy
branch
facts enabled
```

Если включены context stats, добавляется:

```text
context messages
history messages
estimated current request tokens
estimated history tokens
estimated full context tokens
```

Если установлен `context_token_limit`, может добавиться warning:

```text
context warning: estimated context tokens exceeded limit (... > ...)
```

---

## 41. Вывод в терминал

Файл:

```text
ai_engineer_cli/terminal_ui.py
```

В конце `cli.py` вызывается:

```python
print_cli_response(
    response=llm_response.text,
    metadata=metadata,
    user_input=prompt,
    mode="agent" if effective_agent else "direct",
    use_boxes=not args.no_separator,
    show_metadata=not args.no_metadata,
)
```

Если `use_boxes=True`, вывод выглядит как блоки:

```text
╭─ USER ─────────────────────────────╮
│ ...                                │
╰────────────────────────────────────╯

╭─ MODE ─────────────────────────────╮
│ agent                              │
╰────────────────────────────────────╯

╭─ AI RESPONSE ──────────────────────╮
│ ...                                │
╰────────────────────────────────────╯

╭─ METADATA ─────────────────────────╮
│ mode: agent                        │
│ model: gpt-5-mini                  │
│ tokens: ...                        │
╰────────────────────────────────────╯
```

Если передать:

```bash
--no-separator
```

то будет сырой вывод без box UI.

Если передать:

```bash
--no-metadata
```

metadata не печатается.

---

# Часть 5. Примеры полных сценариев

## 42. Direct mode пример

Команда:

```bash
bear "Кратко объясни JSON validation" --format markdown --language ru
```

Flow:

```text
cli.py
  → argparse
  → load stored config for default, but agent не включён
  → effective settings
  → build_system_prompt(markdown, ru)
  → load_config()
  → LLMClient.ask()
  → OpenAI API
  → LLMResponse
  → metadata
  → terminal_ui.print_cli_response()
```

Состояние не сохраняется.

---

## 43. Agent mode с conversation config

Сначала создаём config:

```bash
bear --init-conversation day10-facts-bot \
  --agent \
  --format markdown \
  --language ru \
  --show-context-stats \
  --context-strategy sticky-facts \
  --recent-messages 4
```

Потом используем коротко:

```bash
bear "Сообщение 1. Хочу создать Telegram-бота с нуля" --conversation-id day10-facts-bot
```

Flow:

```text
cli.py
  → argparse
  → MessageStore(day10-facts-bot)
  → load_config from .agent_data/conversations/day10-facts-bot.json
  → effective_agent = True
  → effective_context_strategy = sticky-facts
  → build_system_prompt(markdown, ru)
  → load_config() из .env
  → LLMClient
  → FactsManager
  → Agent
  → Agent.run()
      → load messages
      → load summary
      → load facts
      → create user Message
      → update facts through FactsManager
      → build context through StickyFactsStrategy
      → estimate context tokens
      → LLMClient.ask_messages()
      → create assistant Message
      → save messages
  → metadata
  → terminal_ui
```

---

## 44. Branching пример

Создать conversation:

```bash
bear --init-conversation day10-branching-bot \
  --agent \
  --format markdown \
  --language ru \
  --show-context-stats \
  --context-strategy branching \
  --branch main
```

Создать ветки:

```bash
bear --create-branch aiogram-version --from-branch main --conversation-id day10-branching-bot
bear --create-branch python-telegram-bot-version --from-branch main --conversation-id day10-branching-bot
```

Продолжить ветку:

```bash
bear "Развиваем aiogram-вариант" \
  --conversation-id day10-branching-bot \
  --context-strategy branching \
  --branch aiogram-version
```

Flow:

```text
Agent._load_history()
  → context_strategy == branching
  → message_store.load_branch_messages(branch_id)

Agent._save_history()
  → context_strategy == branching
  → message_store.save_branch_messages(branch_id, messages)
```

---

# Часть 6. Что важно новичку

## 45. `LLMClient` не должен знать про агента

`LLMClient` — низкоуровневый слой.

Он знает только:

```text
как вызвать OpenAI API
как передать model/input/max_output_tokens/temperature
как достать usage
как вернуть LLMResponse
```

Он не знает:

```text
что такое conversation
что такое facts
что такое summary
что такое branches
что такое context strategy
```

Это хорошее архитектурное разделение.

---

## 46. `Agent` — это runtime слой

`Agent` знает:

```text
как загрузить историю
как выбрать стратегию
как обновить facts
как сжать summary
как собрать messages_for_llm
как сохранить ответ
```

Но сам он не делает HTTP-запросы к OpenAI напрямую. Для этого он использует `LLMClient`.

---

## 47. `MessageStore` — слой хранения

`MessageStore` отвечает за JSON-файл.

Он не вызывает LLM.

Он не решает, какую стратегию выбрать.

Он просто хранит и отдаёт:

```text
config
summary
facts
messages
branches
```

---

## 48. `ContextStrategy` — слой политики контекста

Стратегии отвечают только за вопрос:

```text
какие сообщения отправить в модель прямо сейчас?
```

Они не должны:

```text
сохранять файлы
вызывать OpenAI API
парсить CLI flags
считать стоимость
```

---

## 49. Summary и Facts — это разные виды памяти

Summary:

```text
сжимает старую историю в текстовый пересказ
```

Facts:

```text
хранит важные durable facts как key-value пары
```

Summary лучше для общего контекста.

Facts лучше для стабильных решений:

```text
цель
ограничения
архитектурные правила
предпочтения
договорённости
```

---

## 50. Почему токены считаются двумя способами

До API-вызова проект может только оценить размер контекста:

```text
TokenBudget → approximate estimate
```

После API-вызова проект получает реальные токены:

```text
response.usage.input_tokens
response.usage.output_tokens
response.usage.total_tokens
```

Поэтому в metadata могут быть оба вида данных:

```text
estimated full context tokens
и
55 input / 516 output / 571 total
```

---

## 51. Карта ответственности файлов

```text
cli.py
  Парсит CLI, объединяет args + config, выбирает direct/agent mode, печатает результат.

config.py
  Загружает OPENAI_API_KEY и OPENAI_MODEL из .env.

llm_client.py
  Вызывает OpenAI API и возвращает LLMResponse.

model_pricing.py
  Считает примерную стоимость по input/output tokens.

response_format.py
  Собирает system prompt и проверяет JSON-ответы.

prompt_templates.py
  Загружает markdown templates из prompts/.

terminal_ui.py
  Красиво печатает USER / MODE / AI RESPONSE / METADATA.

agent/agent.py
  Главный agent runtime.

agent/message.py
  Dataclass для system/user/assistant сообщений.

agent/message_store.py
  JSON-хранилище conversation state.

agent/conversation_config.py
  Dataclass настроек диалога.

agent/summary_manager.py
  Делает LLM-вызов для summary compression.

agent/facts_manager.py
  Делает LLM-вызов для sticky facts extraction.

agent/token_budget.py
  Оценивает размер контекста в токенах.

agent/strategies/*.py
  Собирают контекст по разным стратегиям.
```

---

## 52. Самая важная схема проекта

```text
Пользователь
  ↓
Терминал / bear
  ↓
cli.py
  ↓
argparse
  ↓
ConversationConfig + CLI flags + defaults
  ↓
response_format.build_system_prompt()
  ↓
config.load_config()
  ↓
LLMClient
  ↓
Direct mode или Agent mode
  ↓
Если Direct:
    LLMClient.ask()
  ↓
Если Agent:
    Agent.run()
      ↓
      MessageStore.load_*
      ↓
      SummaryManager / FactsManager при необходимости
      ↓
      ContextStrategy
      ↓
      TokenBudget
      ↓
      LLMClient.ask_messages()
      ↓
      MessageStore.save_*
  ↓
LLMResponse
  ↓
metadata
  ↓
terminal_ui.print_cli_response()
  ↓
Пользователь видит ответ
```

---

## 53. Что можно улучшить дальше

Текущая архитектура уже полезная, но есть явные следующие шаги:

```text
1. Переименовать MessageStore в ConversationStore.
2. Сделать ask_json() в LLMClient для facts extraction и JSON mode.
3. Добавить retry для невалидного JSON.
4. Добавить реальные tokenizer-based token estimates.
5. Разнести Agent на более мелкие сервисы, если он продолжит расти.
6. Добавить tests для ConversationConfig merge logic.
7. Добавить tests для MessageStore branching.
8. Добавить CLI-команду для просмотра facts.
9. Добавить CLI-команду для просмотра summary.
10. Добавить экспорт conversation в markdown.
```

Главная текущая мысль: проект уже перестал быть простым CLI wrapper. Он стал маленьким agent runtime с persistent state, context strategies и session config.
