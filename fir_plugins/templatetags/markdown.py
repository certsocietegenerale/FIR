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
            "bootstrap-markdown/css/bootstrap-markdown.min.css"),
        "<script type=\"text/javascript\" src=\"%s\"></script>" % static(
            "bootstrap-markdown/js/marked.min.js"),
        "<script type=\"text/javascript\" src=\"%s\"></script>" % static(
            "bootstrap-markdown/js/bootstrap-markdown.js")
    ]
    language = context['LANGUAGE_CODE'].split('-')[0].lower()
    if language != 'en':
        files.append("<script type=\"text/javascript\" src=\"%s\"></script>" % static(
            "bootstrap-markdown/locale/bootstrap-markdown.%s.js" % language))
    return mark_safe("\n".join(files))


@register.simple_tag(takes_context=True)
def rich_edit(context, field):
    return field.as_widget(attrs={"data-provide": "markdown",
                                  "data-language": context['LANGUAGE_CODE'],
                                  "data-hidden-buttons": "cmdImage cmdCode",
                                  "class": "form-control"})


@register.filter(name='markdown')
def render_markdown(data):
    html = markdown2.markdown(data, extras=["link-patterns"],
                              link_patterns=registry.link_patterns(),
                              safe_mode=settings.MARKDOWN_SAFE_MODE)
    return mark_safe(html)

