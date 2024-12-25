from django_filters import CharFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend

from care.emr.api.viewsets.base import EMRModelReadOnlyViewSet
from care.emr.resources.patient.spec import PatientListSpec, PatientRetrieveSpec
from care.facility.models import PatientRegistration


class PatientFilters(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    phone_number = CharFilter(field_name="phone_number", lookup_expr="iexact")


class NewPatientViewSet(EMRModelReadOnlyViewSet):
    database_model = PatientRegistration
    pydantic_read_model = PatientListSpec
    pydantic_retrieve_model = PatientRetrieveSpec
    filterset_class = PatientFilters
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        return super().get_queryset().select_related("created_by", "geo_organization")
