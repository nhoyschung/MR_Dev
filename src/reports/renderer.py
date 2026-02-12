"""Base Jinja2 template renderer."""

from jinja2 import Environment, FileSystemLoader

from src.config import TEMPLATES_DIR


_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_template(template_name: str, **context) -> str:
    """Render a Jinja2 template with the given context."""
    tmpl = _env.get_template(template_name)
    return tmpl.render(**context)
