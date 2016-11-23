from django.forms import Textarea


class MarkdownTextarea(Textarea):
    def __init__(self, attrs=None):
        default_attrs = {"class": "markdown"}
        if attrs:
            default_attrs.update(attrs)
        super(MarkdownTextarea, self).__init__(default_attrs)

    class Media:
        css = {
            'all': ('simplemde/simplemde.min.css',)
        }
        js = (
            "simplemde/marked.min.js",
            "simplemde/simplemde.min.js",
            "simplemde/inline-attachment.min.js",
            "simplemde/codemirror.inline-attachment.js",
            "simplemde/markdown.js",
        )
