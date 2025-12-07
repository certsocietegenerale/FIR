from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.settings import api_settings


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"

    def get_page_size(self, request):
        self.page_size = api_settings.PAGE_SIZE
        if hasattr(request.user, "profile") and hasattr(
            request.user.profile, "incident_number"
        ):
            self.page_size = request.user.profile.incident_number

        return super().get_page_size(request)

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
