# Imports
from markupsafe import Markup
import markdown2
import re


# Stripping HTML of Whitespace
def minify_html(html_str: Markup) -> Markup:
    # Remove newlines and excessive spaces between tags
    html_str = re.sub(r'>\s+<', '><', html_str)
    # Optionally remove leading/trailing whitespace
    html_str = html_str.strip()
    return html_str

def markdown_to_html(markdown_str: str) -> Markup:
    return Markup(markdown2.markdown(markdown_str))

def get_html(markdown_str) -> Markup:
    html_str: Markup = markdown_to_html(markdown_str)
    return minify_html(html_str)