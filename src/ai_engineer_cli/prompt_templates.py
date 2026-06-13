from pathlib import Path


PROMPTS_DIR = Path(__file__).parent / "prompts"


def list_templates() -> list[str]:
    if not PROMPTS_DIR.exists():
        return []

    return sorted(
        template_path.stem
        for template_path in PROMPTS_DIR.glob("*.md")
        if template_path.is_file()
    )


def load_template(template_name: str) -> str:
    template_path = PROMPTS_DIR / f"{template_name}.md"

    if not template_path.exists():
        available_templates = list_templates()
        available_text = ", ".join(available_templates) if available_templates else "none"

        raise ValueError(
            f"Template '{template_name}' not found. "
            f"Available templates: {available_text}"
        )

    return template_path.read_text(encoding="utf-8")


def render_template(template_text: str, user_input: str) -> str:
    if "{{input}}" not in template_text:
        raise ValueError("Template must contain '{{input}}' placeholder.")

    return template_text.replace("{{input}}", user_input)