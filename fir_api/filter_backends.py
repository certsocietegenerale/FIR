from django_filters.rest_framework import DjangoFilterBackend


class DummyFilterBackend(DjangoFilterBackend):
    """
    Backend which intentionally does not apply filters
    """

    def filter_queryset(self, request, queryset, view):
        return queryset
