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