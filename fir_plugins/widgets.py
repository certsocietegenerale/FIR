from django.forms import Textarea


class MarkdownTextarea(Textarea):
    def __init__(self, attrs=None):
        default_attrs = {"class": "markdown"}
        if attrs:
            default_attrs.update(attrs)
        super(MarkdownTextarea, self).__init__(default_attrs)

    class Media:
        css = {
            'all': ('easymde/easymde.min.css',)
        }
        js = (
            "easymde/marked.min.js",
            "easymde/easymde.min.js",
            "easymde/codemirror.js",
            "easymde/markdown.js",
        )
