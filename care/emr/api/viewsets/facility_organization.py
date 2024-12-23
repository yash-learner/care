from django_filters import rest_framework as filters

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.organziation import FacilityOrganization
from care.emr.resources.facility_organization.spec import (
    FacilityOrganizationReadSpec,
    FacilityOrganizationWriteSpec,
)


class FacilityOrganizationFilter(filters.FilterSet):
    parent = filters.UUIDFilter(field_name="parent__external_id")
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    org_type = filters.CharFilter(field_name="org_type", lookup_expr="iexact")


class FacilityOrganizationViewSet(EMRModelViewSet):
    database_model = FacilityOrganization
    pydantic_model = FacilityOrganizationWriteSpec
    pydantic_read_model = FacilityOrganizationReadSpec
    filterset_class = FacilityOrganizationFilter
    filter_backends = [filters.DjangoFilterBackend]
    CREATE_QUESTIONNAIRE_RESPONSE = False

    def clean_create_data(self, request_data):
        request_data["facility"] = self.kwargs["facility_external_id"]
        return request_data

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(facility__external_id=self.kwargs["facility_external_id"])
            .select_related("facility", "parent", "created_by", "updated_by")
        )
