from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator
from copy import deepcopy
from functools import cached_property
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _


class FasterDjangoPaginator(Paginator):
    @cached_property
    def count(self):
        old_queryset = deepcopy(self.object_list)

        # Remove annotations to speed up the SQL query
        for elem in self.object_list.query.annotations.items():
            alias = elem[1].source_expressions[0].alias
            del self.object_list.query.alias_map[alias]
        self.object_list.query.annotations.clear()

        ct = super().count
        self.object_list = old_queryset
        return ct


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"

    def paginate_queryset(self, queryset, request, view=None):
        backup_paginator = False
        backup_get_page_size = False
        backup_page_size = self.page_size

        if type(view).__name__ == "IncidentViewSet":

            # Use user-entered input when counting incidents
            backup_get_page_size = self.get_page_size
            self.get_page_size = self.get_page_size_incidents

            params = view.request.query_params

            # check if 'last_comment_date' annotation is used
            if any(
                [
                    a in params and params[a]
                    for a in ["last_comment_date_before", "last_comment_date_after"]
                ]
            ) or any(
                [
                    a in params.get("ordering", [])
                    for a in ["last_comment_date", "-last_comment_date"]
                ]
            ):
                if params.get("query", False) and params["query"]:
                    # And 'query' argument is present
                    raise ParseError(
                        _(
                            "'query' and 'last_comment_date' parameters are mutually exclusive"
                        )
                    )
            else:
                # if the annotation is not used: remove it during count
                backup_paginator = self.django_paginator_class
                self.django_paginator_class = FasterDjangoPaginator

        ret = super().paginate_queryset(queryset, request, view)

        # Restore altered properties/attributes
        if backup_paginator:
            self.django_paginator_class = backup_paginator
        if backup_get_page_size:
            self.get_page_size = backup_get_page_size
            self.page_size = backup_page_size

        return ret

    def get_page_size_incidents(self, request):
        if hasattr(request.user, "profile") and hasattr(
            request.user.profile, "incident_number"
        ):
            self.page_size = request.user.profile.incident_number
        return super().get_page_size(request)

    # Add "total_pages"
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
