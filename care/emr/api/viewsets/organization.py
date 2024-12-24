from django_filters import rest_framework as filters

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.organziation import Organization
from care.emr.resources.organization.spec import (
    OrganizationReadSpec,
    OrganizationWriteSpec,
)


class OrganizationFilter(filters.FilterSet):
    parent = filters.UUIDFilter(field_name="parent__external_id")
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    org_type = filters.CharFilter(field_name="org_type", lookup_expr="iexact")


class OrganizationViewSet(EMRModelViewSet):
    database_model = Organization
    pydantic_model = OrganizationWriteSpec
    pydantic_read_model = OrganizationReadSpec
    filterset_class = OrganizationFilter
    filter_backends = [filters.DjangoFilterBackend]

    CREATE_QUESTIONNAIRE_RESPONSE = False

    def get_queryset(self):
        return (
            super().get_queryset().select_related("parent", "created_by", "updated_by")
        )
