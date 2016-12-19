from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from django.conf import settings
import markdown2

from ..links import registry

register = template.Library()


@register.simple_tag(takes_context=True)
def rich_edit_static(context):

    files = [
        "<link href=\"%s\" rel=\"stylesheet\"/>" % static(
            "simplemde/simplemde.min.css"),
        "<script type=\"text/javascript\" src=\"%s\"></script>" % static(
            "simplemde/marked.min.js"),
        "<script type=\"text/javascript\" src=\"%s\"></script>" % static(
            "simplemde/simplemde.min.js"),
        "<script type=\"text/javascript\" src=\"%s\"></script>" % static(
            "simplemde/inline-attachment.min.js"),
        "<script type=\"text/javascript\" src=\"%s\"></script>" % static(
            "simplemde/codemirror.inline-attachment.js"),
        "<script type=\"text/javascript\" src=\"%s\"></script>" % static(
            "simplemde/markdown.js")
    ]
    return mark_safe("\n".join(files))


@register.simple_tag(takes_context=True)
def rich_edit(context, field):
    return field.as_widget(attrs={"class": "form-control markdown"})


@register.filter(name='markdown')
def render_markdown(data):
    html = markdown2.markdown(data, extras=["link-patterns", "tables", "code-friendly"],
                              link_patterns=registry.link_patterns(),
                              safe_mode=settings.MARKDOWN_SAFE_MODE)
    return mark_safe(html)
