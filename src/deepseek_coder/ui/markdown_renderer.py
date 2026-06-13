"""
Конвертация markdown в HTML с подсветкой синтаксиса.

Используется в ChatView для финального рендера ответа ассистента.
Стриминг идёт plain text-ом; по завершении весь буфер
прогоняется через эту функцию и вставляется через insertHtml.
"""

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

_code_style: str = "monokai"
_TEXT_COLOR_ASSISTANT = "#ECEFF1"  # рядом с _CODE_STYLE


def _highlight_code(code: str, lang: str, _attrs: str) -> str:
    """
    Callback для markdown-it: подсветка одного code block через Pygments.
    Если язык не распознан — возвращаем пустую строку,
    markdown-it отрендерит блок как plain <pre> без подсветки.
    """
    try:
        lexer = get_lexer_by_name(lang)
    except ClassNotFound:
        return ""
    formatter = HtmlFormatter(noclasses=True, style=_code_style)
    return highlight(code, lexer, formatter)


_md = MarkdownIt("commonmark", {"highlight": _highlight_code})


def markdown_to_html(text: str) -> str:
    html = _md.render(text)
    return f'<div style="color: {_TEXT_COLOR_ASSISTANT}">{html}</div>'


def configure(code_style: str) -> None:
    """Настроить стиль подсветки, вызвать один раз при старте"""
    global _code_style
    _code_style = code_style
