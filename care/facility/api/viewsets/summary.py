from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import GenericViewSet

class FacilitySummaryFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="created_date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="created_date", lookup_expr="lte")
    facility = filters.UUIDFilter(field_name="facility__external_id")
    district = filters.NumberFilter(field_name="facility__district__id")
    local_body = filters.NumberFilter(field_name="facility__local_body__id")
    state = filters.NumberFilter(field_name="facility__state__id")


class DistrictSummaryFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="created_date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="created_date", lookup_expr="lte")
    district = filters.NumberFilter(field_name="district__id")
    state = filters.NumberFilter(field_name="district__state__id")
