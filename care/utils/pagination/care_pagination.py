from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class CareLimitOffsetPagination(LimitOffsetPagination):
    def get_paginated_response(self, data):
        return Response({"count": self.count, "results": data})
