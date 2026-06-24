from ai_engineer_cli.agent.message import Message
from ai_engineer_cli.agent.message_store import MessageStore
from ai_engineer_cli.agent.summary_manager import SummaryManager
from ai_engineer_cli.agent.token_budget import ContextTokenStats, TokenBudget
from ai_engineer_cli.llm_client import LLMClient, LLMResponse


class Agent:
    """
    Persistent agent runtime.

    Agent is responsible for:
    - receiving user input;
    - loading conversation history;
    - preparing messages;
    - optionally compressing old history into summary;
    - estimating context token usage;
    - calling LLMClient;
    - saving updated history;
    - returning LLMResponse.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str | None = None,
        message_store: MessageStore | None = None,
        token_budget: TokenBudget | None = None,
        summary_manager: SummaryManager | None = None,
        use_summary: bool = False,
        recent_messages: int = 6,
        summary_every: int = 10,
    ) -> None:
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.message_store = message_store
        self.token_budget = token_budget or TokenBudget()
        self.summary_manager = summary_manager
        self.use_summary = use_summary
        self.recent_messages = recent_messages
        self.summary_every = summary_every
        self.last_context_token_stats: ContextTokenStats | None = None

    def run(
        self,
        user_input: str,
        model: str | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        history = self._load_history()
        summary = self._load_summary()

        if self.use_summary:
            summary, history = self._compress_history_if_needed(
                history=history,
                summary=summary,
                model=model,
                temperature=temperature,
            )

        user_message = Message(
            role="user",
            content=user_input,
        )

        messages_for_llm = self._build_messages_for_llm(
            history=history,
            user_message=user_message,
            summary=summary,
        )

        self.last_context_token_stats = self.token_budget.build_context_stats(
            current_request=user_message,
            history=history,
            full_context=messages_for_llm,
        )

        response = self.llm_client.ask_messages(
            messages=[message.to_dict() for message in messages_for_llm],
            model=model,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )

        assistant_message = Message(
            role="assistant",
            content=response.text,
        )

        updated_history = [
            *history,
            user_message,
            assistant_message,
        ]

        self._save_history(updated_history)

        return response

    def clear_history(self) -> None:
        if self.message_store:
            self.message_store.clear()

    def _load_history(self) -> list[Message]:
        if not self.message_store:
            return []

        return self.message_store.load_messages()

    def _save_history(self, messages: list[Message]) -> None:
        if self.message_store:
            self.message_store.save_messages(messages)

    def _load_summary(self) -> str | None:
        if not self.message_store:
            return None

        return self.message_store.load_summary()

    def _save_summary(self, summary: str | None) -> None:
        if self.message_store:
            self.message_store.save_summary(summary)

    def _compress_history_if_needed(
        self,
        history: list[Message],
        summary: str | None,
        model: str | None,
        temperature: float | None,
    ) -> tuple[str | None, list[Message]]:
        if not self.summary_manager:
            return summary, history

        if len(history) < self.summary_every:
            return summary, history

        if len(history) <= self.recent_messages:
            return summary, history

        messages_to_summarize = history[:-self.recent_messages]
        recent_history = history[-self.recent_messages :]

        updated_summary = self.summary_manager.summarize(
            messages=messages_to_summarize,
            existing_summary=summary,
            model=model,
            max_output_tokens=700,
            temperature=temperature,
        )

        self._save_summary(updated_summary)
        self._save_history(recent_history)

        return updated_summary, recent_history

    def _build_messages_for_llm(
        self,
        history: list[Message],
        user_message: Message,
        summary: str | None,
    ) -> list[Message]:
        messages: list[Message] = []

        if self.system_prompt:
            messages.append(
                Message(
                    role="system",
                    content=self.system_prompt,
                )
            )

        if self.use_summary and summary:
            messages.append(
                Message(
                    role="system",
                    content=f"Conversation summary:\n{summary}",
                )
            )

        messages.extend(history)
        messages.append(user_message)

        return messages