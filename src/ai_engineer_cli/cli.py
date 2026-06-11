import argparse
import sys

from ai_engineer_cli.config import load_config
from ai_engineer_cli.llm_client import LLMClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-engineer-cli",
        description="CLI tool for working with LLMs as an engineering assistant.",
    )

    parser.add_argument(
        "prompt",
        type=str,
        help="Prompt to send to the LLM.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = load_config()
        llm_client = LLMClient(config)
        response = llm_client.ask(args.prompt)

        print(response)

    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()