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

## Day 9 — Summary Compression

### Goal

Add summary-based context compression to the Agent runtime.

The agent should keep the last N messages as-is, compress older messages into a summary, store the summary separately, and send summary + recent messages instead of full history.

---

### What was implemented

- Added `SummaryManager`.
- Added summary prompt in `src/ai_engineer_cli/prompts/summarize_history.md`.
- Updated `MessageStore` to store `summary` together with messages.
- Updated `Agent` to support summary-based context compression.
- Added `--use-summary`.
- Added `--recent-messages`.
- Added `--summary-every`.
- Added summary mode metadata.

---

### Architecture after Day 9

```text
CLI
 └── Agent
      ├── MessageStore
      ├── SummaryManager
      ├── TokenBudget
      └── LLMClient
```

---

### Context without compression

```text
system prompt
+ full history
+ current user message
```

---

### Context with summary compression

```text
system prompt
+ conversation summary
+ last N messages
+ current user message
```

---

### Storage format

Conversation data is stored in:

```text
.agent_data/conversations/{conversation_id}.json
```

Example:

```json
{
  "conversation_id": "day9-summary",
  "summary": "User is Evgenii. He is building ai-engineer-cli...",
  "messages": [
    {
      "role": "user",
      "content": "Recent message..."
    },
    {
      "role": "assistant",
      "content": "Recent response..."
    }
  ]
}
```

---

### Test setup

Full history conversation:

```text
day9-full
```

Summary compression conversation:

```text
day9-summary
```

Summary settings used for testing:

```text
--use-summary --summary-every 6 --recent-messages 4
```

---

### Quality comparison

Full history mode:

```text
Keeps all details exactly as they were.
Provides stronger recall of precise wording.
Uses more input tokens as the conversation grows.
```

Summary mode:

```text
Keeps main goals, decisions, constraints, and progress.
Uses fewer context tokens after compression.
May lose small details or exact wording.
Requires an additional LLM call to create/update the summary.
```

---

### Token comparison

Observed fields:

```text
estimated full context tokens
input tokens
total tokens
estimated cost
```

Result:

```text
Summary mode reduces the amount of old history sent to the model.
The longer the conversation, the more useful summary compression becomes.
```

---

### Important tradeoff

Summary compression is not free.

It saves tokens in future requests, but creating the summary requires an additional LLM call.

This strategy is useful for long-running conversations, not for very short ones.

---

### Result

The agent can now compress old conversation history into summary and continue the conversation using:

```text
summary + recent messages
```

This makes persistent context cheaper and more scalable.

---

### Limitations

- Summary quality depends on the model.
- Important details may be lost during compression.
- The compression threshold is message-count based, not token-budget based.
- There is no manual summary editing yet.
- There are no multiple context strategies yet.

## Day 9.5 — Conversation Config

### Goal

Reduce CLI friction by storing conversation-level settings in the same JSON file as messages and summary.

Instead of passing many flags on every request, the user can initialize a conversation once and then continue it using only `--conversation-id`.

---

### What was implemented

- Added `ConversationConfig`.
- Stored `config`, `summary`, and `messages` in one JSON file per conversation.
- Added config-aware CLI flag merging.
- Changed config-aware argparse defaults to `None`.
- Added `--init-conversation`.
- Added `--show-conversation-config`.
- Added `--delete-conversation`.
- Changed `--clear-history` to preserve config and clear only messages and summary.

---

### Storage format

One file stores one conversation:

```text
.agent_data/conversations/{conversation_id}.json
```

Example:

```json
{
  "conversation_id": "day9-summary",
  "config": {
    "agent": true,
    "response_format": "markdown",
    "language": "ru",
    "show_context_stats": true,
    "use_summary": true,
    "summary_every": 6,
    "recent_messages": 4,
    "context_token_limit": null,
    "model": null,
    "max_output_tokens": null,
    "temperature": null,
    "stop_instruction": null
  },
  "summary": null,
  "messages": []
}
```

---

### Config merge order

Effective runtime settings are resolved using this priority:

```text
1. Explicit CLI flags
2. Stored conversation config
3. Hardcoded defaults
```

This allows a conversation to have persistent settings while still allowing one-off CLI overrides.

---

### Example

Initialize conversation:

```bash
bear --init-conversation day9-summary \
  --agent \
  --format markdown \
  --language ru \
  --show-context-stats \
  --use-summary \
  --summary-every 6 \
  --recent-messages 4
```

Continue conversation:

```bash
bear "Кратко перечисли, что ты помнишь обо мне и проекте." --conversation-id day9-summary
```

Show config:

```bash
bear --show-conversation-config --conversation-id day9-summary
```

Clear runtime state but preserve config:

```bash
bear --clear-history --conversation-id day9-summary
```

Delete full conversation:

```bash
bear --delete-conversation --conversation-id day9-summary
```

---

### Result

Conversation settings are now persistent.

The CLI becomes easier to use for long-running agent sessions, and the project moves closer to a real agent runtime instead of a one-shot command wrapper.

## Day 10 — Context Strategies

### Goal

Add multiple context management strategies to the Agent runtime and allow switching between them.

Implemented strategies:

- Sliding Window
- Sticky Facts / Key-Value Memory
- Branching

---

### What was implemented

- Added `ContextStrategy` interface.
- Added `SlidingWindowStrategy`.
- Added `StickyFactsStrategy`.
- Added `BranchingStrategy`.
- Added `FactsManager`.
- Added facts extraction prompt.
- Added facts storage to conversation JSON.
- Added branch storage to conversation JSON.
- Added `--context-strategy`.
- Added `--branch`.
- Added `--create-branch`.
- Added `--from-branch`.
- Added `--list-branches`.

---

### Strategy 1 — Sliding Window

Context structure:

```text
system prompt
+ last N messages
+ current user message
```

Result:

```text
Cheap and predictable, but old facts can be lost.
```

---

### Strategy 2 — Sticky Facts

Context structure:

```text
system prompt
+ sticky facts
+ last N messages
+ current user message
```

Facts example:

```json
{
  "project": "ai-engineer-cli",
  "goal": "Build a CLI developer assistant",
  "architecture_rule": "LLMClient must remain a low-level API client"
}
```

Result:

```text
Better long-term stability than sliding window.
Good for goals, decisions, constraints, and project memory.
```

---

### Strategy 3 — Branching

Context structure:

```text
system prompt
+ selected branch messages
+ current user message
```

Branches example:

```text
main
json-storage
sqlite-storage
```

Result:

```text
Useful for comparing alternative solutions without mixing their histories.
```

---

### Comparison

| Strategy | Quality | Stability | Token usage | UX |
|---|---|---|---|---|
| Sliding Window | Good for short local tasks | Weak for old facts | Low | Simple |
| Sticky Facts | Good for project memory | Medium/High | Medium | Convenient |
| Branching | Good for alternatives | High per branch | Depends on branch length | Powerful but explicit |

---

### Key lesson

There is no universal best context strategy.

Different workflows need different context policies:

- Sliding Window is good for short, cheap interactions.
- Sticky Facts is good for long-running project memory.
- Branching is good for comparing alternative implementation paths.

Day 10 turns the agent from a single-context runtime into a configurable context management system.