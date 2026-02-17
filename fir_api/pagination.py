from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.settings import api_settings


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"

    def get_page_size_incidents(self, request):
        self.page_size = api_settings.PAGE_SIZE
        if hasattr(request.user, "profile") and hasattr(
            request.user.profile, "incident_number"
        ):
            self.page_size = request.user.profile.incident_number

        return super().get_page_size(request)

    def paginate_queryset(self, queryset, request, view=None):
        backup = self.get_page_size
        if type(view).__name__ == "IncidentViewSet":
            self.get_page_size = self.get_page_size_incidents

        ret = super().paginate_queryset(queryset, request, view)
        self.get_page_size = backup
        return ret

    # Add "total_pages" to the response
    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
