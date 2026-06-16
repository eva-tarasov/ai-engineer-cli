import shutil
import textwrap


DEFAULT_WIDTH = 80
MIN_WIDTH = 60
MAX_WIDTH = 100


def get_terminal_width() -> int:
    terminal_size = shutil.get_terminal_size(fallback=(DEFAULT_WIDTH, 24))
    return max(MIN_WIDTH, min(terminal_size.columns, MAX_WIDTH))


def print_box(
    title: str,
    content: str,
    width: int | None = None,
) -> None:
    box_width = width or get_terminal_width()
    inner_width = box_width - 4

    top_border = f"╭─ {title} "
    top_border += "─" * max(0, box_width - len(top_border) - 1)
    top_border += "╮"

    bottom_border = "╰" + "─" * (box_width - 2) + "╯"

    print(top_border)

    if not content.strip():
        print(f"│ {'':<{inner_width}} │")
    else:
        for line in content.splitlines():
            wrapped_lines = textwrap.wrap(
                line,
                width=inner_width,
                replace_whitespace=False,
                drop_whitespace=False,
            )

            if not wrapped_lines:
                print(f"│ {'':<{inner_width}} │")

            for wrapped_line in wrapped_lines:
                print(f"│ {wrapped_line:<{inner_width}} │")

    print(bottom_border)


def format_metadata(metadata: dict[str, str]) -> str:
    return "\n".join(f"{key}: {value}" for key, value in metadata.items())


def print_cli_response(
    response: str,
    metadata: dict[str, str] | None = None,
    user_input: str | None = None,
    mode: str | None = None,
    use_boxes: bool = True,
    show_metadata: bool = True,
) -> None:
    if not use_boxes:
        print(response)

        if metadata and show_metadata:
            print()
            print(format_metadata(metadata))

        return

    print()

    if user_input:
        print_box("USER", user_input)
        print()

    if mode:
        print_box("MODE", mode)
        print()

    print_box("AI RESPONSE", response)

    if metadata and show_metadata:
        print()
        print_box("METADATA", format_metadata(metadata))

    print()