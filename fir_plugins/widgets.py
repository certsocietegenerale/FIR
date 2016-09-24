from django.forms import Textarea


class MarkdownTextarea(Textarea):
    def __init__(self, attrs=None):
        default_attrs = {'data-provide': 'markdown', 'data-hidden-buttons': 'cmdImage cmdCode'}
        if attrs:
            default_attrs.update(attrs)
        super(MarkdownTextarea, self).__init__(default_attrs)

    class Media:
        css = {
            'all': ('bootstrap-markdown/css/bootstrap-markdown.min.css',)
        }
        js = ('bootstrap-markdown/js/marked.min.js',
              'bootstrap-markdown/js/bootstrap-markdown.js')
