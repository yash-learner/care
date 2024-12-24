from django_filters import rest_framework as filters

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.medication_administration import MedicationAdministration
from care.emr.resources.medication.administration.spec import (
    MedicationAdministrationReadSpec,
    MedicationAdministrationSpec,
)


class MedicationAdministrationFilter(filters.FilterSet):
    encounter = filters.UUIDFilter(field_name="encounter__external_id")


class MedicationAdministrationViewSet(EMRModelViewSet):
    database_model = MedicationAdministration
    pydantic_model = MedicationAdministrationSpec
    pydantic_read_model = MedicationAdministrationReadSpec
    filterset_class = MedicationAdministrationFilter
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
            .select_related("patient", "encounter", "created_by", "updated_by")
        )
