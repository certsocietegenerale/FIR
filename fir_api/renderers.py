from rest_framework.renderers import BrowsableAPIRenderer


class FilterButtonBrowsableAPIRenderer(BrowsableAPIRenderer):

    def get_filter_form(self, data, view, request):
        #  Pass an empty list to force the 'filter' HTML button
        #  to be always displayed
        return super().get_filter_form([], view, request)
