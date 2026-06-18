# Week 2 — Agent Core Notes

## Day 6 — First Agent

### Goal

Create the first `Agent` abstraction above `LLMClient`.

The main goal of the day was not to make the agent smart yet. The goal was to separate responsibilities:

- `LLMClient` is responsible for low-level API communication.
- `Agent` is responsible for agent-level behavior.
- `CLI` decides which execution mode to use: direct mode or agent mode.

---

### What was implemented

- Added a new `agent` package.
- Added `Message` model.
- Added minimal `Agent` class.
- Added `--agent` CLI flag.
- Connected `Agent` to the existing `LLMClient.ask()` method.
- Preserved the existing direct CLI mode.
- Agent mode returns the same `LLMResponse` type as direct mode.

---

### New files

```text
src/ai_engineer_cli/agent/__init__.py
src/ai_engineer_cli/agent/agent.py
src/ai_engineer_cli/agent/message.py
```

---

### Changed files

```text
src/ai_engineer_cli/cli.py
src/ai_engineer_cli/llm_client.py
reports/week2_notes.md
```

Note: keep `src/ai_engineer_cli/llm_client.py` in this list only if it was actually changed during Day 6.

---

### Current architecture

Before Day 6:

```text
CLI
 └── LLMClient
      └── OpenAI API
```

After Day 6:

```text
CLI
 ├── Direct mode
 │    └── LLMClient
 │         └── OpenAI API
 │
 └── Agent mode
      └── Agent
           └── LLMClient
                └── OpenAI API
```

---

### Important design decision

`Agent` does not replace `LLMClient`.

`LLMClient` remains a low-level API client. It knows how to call the model, pass API parameters, measure duration, read token usage, estimate cost, and return `LLMResponse`.

`Agent` is a higher-level runtime layer. On Day 6 it only prepares a user message and delegates the actual model call to `LLMClient`.

This separation is important because later the agent will be responsible for:

- loading conversation history;
- saving messages;
- building context;
- tracking token usage;
- applying memory strategies;
- compressing old history;
- working with branches.

---

### Message model

Added a basic message model:

```python
@dataclass
class Message:
    role: MessageRole
    content: str
```

Supported roles:

```text
system
user
assistant
```

The message model is intentionally simple for now. It will become the base unit for conversation history on Day 7.

---

### Agent behavior on Day 6

Current flow:

```text
user input
 → Agent.run()
 → create user Message
 → call LLMClient.ask()
 → receive LLMResponse
 → return LLMResponse to CLI
```

The agent does not store history yet.

---

### CLI behavior

The CLI now supports two modes.

Direct mode:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Кратко объясни, что такое JSON validation" --format markdown --language ru
```

Agent mode:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Кратко объясни, что такое agent runtime" --agent --format markdown --language ru
```

The `--agent` flag switches execution from direct `LLMClient.ask()` call to `Agent.run()`.

---

### Test results

Tested direct mode:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Кратко объясни, что такое JSON validation" --format markdown --language ru
```

Result:

```text
Direct mode works.
The model returns a valid response.
Existing Week 1 behavior is preserved.
```

Tested agent mode:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Кратко объясни, что такое agent runtime" --agent --format markdown --language ru
```

Result:

```text
Agent mode works.
The request goes through Agent.
The response is returned and printed correctly.
```

Tested help:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli --help
```

Result:

```text
The --agent flag is available in CLI help.
```

---

### Metadata behavior

Agent mode returns the same `LLMResponse` type as direct mode.

Because of this, existing metadata output still works:

- model;
- duration;
- input tokens;
- output tokens;
- total tokens;
- estimated cost.

This is a good design result because the CLI output layer does not need to know whether the response came from direct mode or agent mode.

---

### What is not implemented yet

The agent does not yet:

- store conversation history;
- restore context after restart;
- count full context tokens;
- manage token budget;
- compress old messages;
- support memory strategies;
- support branching;
- use tools or MCP.

These features are planned for the next days of Week 2.

---

### Key lesson

An agent is not just a single LLM API call.

Even a minimal agent should be a separate runtime layer with its own responsibility. On Day 6 the agent is still simple, but the project now has the correct architectural direction:

```text
LLMClient = how to call the model
Agent = how to manage behavior around the model
```

---

### Next step

Day 7 will add persistent context.

The next goal is to make the agent save and restore conversation history between CLI runs.

## Day 7 — Persistent Context

### Goal

Add persistent conversation history to the Agent runtime.

The agent should save messages after each request, load them after restart, and continue the conversation as if it was not stopped.

---

### What was implemented

- Added `Message.from_dict()`.
- Added `MessageStore`.
- Added JSON-based conversation storage.
- Added `LLMClient.ask_messages()`.
- Updated `Agent` to load and save conversation history.
- Added `--conversation-id` CLI option.
- Added `--clear-history` CLI option.
- Added `.agent_data/` to `.gitignore`.

---

### Storage format

Conversation history is stored in:

```text
.agent_data/conversations/{conversation_id}.json
```

Example:

```json
{
  "conversation_id": "day7-test",
  "messages": [
    {
      "role": "user",
      "content": "Меня зовут Евгений. Я строю проект ai-engineer-cli."
    },
    {
      "role": "assistant",
      "content": "..."
    }
  ]
}
```

---

### Architecture after Day 7

```text
CLI
 └── Agent
      ├── MessageStore
      └── LLMClient
```

Agent flow:

```text
load history
→ add user message
→ send full context to LLM
→ receive assistant response
→ save updated history
→ return response
```

---

### Test scenario

1. Start a new conversation.
2. Tell the agent a fact.
3. Stop the CLI process.
4. Start a new CLI command with the same `conversation-id`.
5. Ask the agent to recall the fact.
6. Confirm that the agent restored context from JSON.

---

### Test commands

First message:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Меня зовут Евгений. Я строю проект ai-engineer-cli." --agent --conversation-id day7-test --format markdown --language ru
```

Second message after restart:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli "Как меня зовут и какой проект я строю?" --agent --conversation-id day7-test --format markdown --language ru
```

Inspect stored history:

```bash
cat .agent_data/conversations/day7-test.json
```

Clear history:

```bash
PYTHONPATH=src python -m ai_engineer_cli.cli --agent --conversation-id day7-test --clear-history
```

---

### Result

- The agent saves conversation history to JSON.
- The agent loads previous messages after CLI restart.
- The agent continues the conversation using previous context.
- The direct mode still works.
- Conversation history is excluded from git.

---

### Limitations

- The full history is sent to the model on every request.
- Token usage grows with each new message.
- There is no token budget yet.
- There is no context compression yet.
- There are no memory strategies yet.
- Long conversations may become expensive or exceed the model context limit.

---

### Key lesson

LLMs are stateless by default.

Persistent agent memory is implemented by the application, not by the model. The agent must explicitly store previous messages and send the relevant context again with every request.

Day 7 turns the agent from a simple wrapper around `LLMClient` into a stateful runtime component.

## Day 8 — Token Tracking

### Goal

Add token tracking to the Agent runtime.

The agent should show how many tokens are used by the current request, stored history, full context, and model response.

---

### What was implemented

- Added `TokenBudget`.
- Added `ContextTokenStats`.
- Added estimated token count for the current request.
- Added estimated token count for conversation history.
- Added estimated token count for full context.
- Reused real API token usage for model input/output/total tokens.
- Added `--show-context-stats`.
- Added `--context-token-limit`.
- Added context overflow warning.

---

### Architecture after Day 8

```text
CLI
 └── Agent
      ├── MessageStore
      ├── TokenBudget
      └── LLMClient
```

---

### Token types

Estimated before API call:

```text
current request tokens
history tokens
full context tokens
```

Reported by API after response:

```text
input tokens
output tokens
total tokens
```

---

### Why estimates and real usage differ

`TokenBudget` uses an approximate character-based estimate.

The OpenAI API returns real token usage after the request is completed.

Because of this, estimated full context tokens and real input tokens may differ.

The estimate is still useful because it allows the agent to inspect context size before sending the request.

---

### Short dialog experiment

Conversation id:

```text
day8-short
```

Commands:

```bash
bear "Меня зовут Евгений. Я строю ai-engineer-cli." --agent --conversation-id day8-short --format markdown --language ru --show-context-stats
```

```bash
bear "Как меня зовут и какой проект я строю?" --agent --conversation-id day8-short --format markdown --language ru --show-context-stats
```

Observation:

```text
The second request contains previous user and assistant messages.
History tokens increased.
Full context tokens increased.
API input tokens increased.
Cost increased.
```

---

### Long dialog experiment

Conversation id:

```text
day8-long
```

The agent was tested with multiple messages about the same project.

Observation:

```text
With every new message, the stored history grows.
The full context sent to the model also grows.
Input tokens and estimated cost increase over time.
The agent can recall previous facts because they are included in the context.
```

---

### Context limit experiment

Command example:

```bash
bear "Проверь, что ты помнишь по проекту." --agent --conversation-id day8-long --format markdown --language ru --show-context-stats --context-token-limit 100
```

Observation:

```text
The agent shows a context warning when estimated full context tokens exceed the configured limit.
```

---

### What breaks when context grows too much

If the context becomes too large, several problems appear:

- requests become more expensive;
- latency increases;
- API input token usage grows;
- the model may eventually reject the request if the context window is exceeded;
- sending full history becomes inefficient.

In Day 8, the project only detects and displays this problem.

The solution will be implemented later through:

- summary compression;
- sliding window;
- sticky facts;
- memory strategies.

---

### Result

The agent now shows how tokens affect behavior and cost.

Day 8 makes the hidden cost of persistent context visible.

---

### Limitations

- Token counting is approximate before API call.
- The current implementation does not yet prevent oversized requests.
- The full history is still sent every time.
- No compression is applied yet.
