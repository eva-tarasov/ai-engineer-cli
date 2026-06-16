from ai_engineer_cli.agent.message import Message
from ai_engineer_cli.llm_client import LLMClient, LLMResponse


class Agent:
    """
    Minimal agent runtime.

    Agent is responsible for:
    - receiving user input;
    - preparing agent-level context;
    - calling LLMClient;
    - returning LLMResponse.

    It does not store history yet.
    Persistent memory will be added on Day 7.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.system_prompt = system_prompt

    def run(
        self,
        user_input: str,
        model: str | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        user_message = Message(
            role="user",
            content=user_input,
        )

        response = self.llm_client.ask(
            prompt=user_message.content,
            system_prompt=self.system_prompt,
            model=model,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )

        return response