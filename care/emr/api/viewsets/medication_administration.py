from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied

from care.emr.api.viewsets.authz_base import EncounterBasedAuthorizationBase
from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.medication_administration import MedicationAdministration
from care.emr.registries.system_questionnaire.system_questionnaire import (
    InternalQuestionnaireRegistry,
)
from care.emr.resources.medication.administration.spec import (
    MedicationAdministrationReadSpec,
    MedicationAdministrationSpec,
)
from care.emr.resources.questionnaire.spec import SubjectType
from care.security.authorization import AuthorizationController


class MedicationAdministrationFilter(filters.FilterSet):
    encounter = filters.UUIDFilter(field_name="encounter__external_id")
    request = filters.UUIDFilter(field_name="request__external_id")
    occurrence_period_start = filters.DateTimeFromToRangeFilter()
    occurrence_period_end = filters.DateTimeFromToRangeFilter()


class MedicationAdministrationViewSet(EncounterBasedAuthorizationBase, EMRModelViewSet):
    database_model = MedicationAdministration
    pydantic_model = MedicationAdministrationSpec
    pydantic_read_model = MedicationAdministrationReadSpec
    questionnaire_type = "medication_administration"
    questionnaire_title = "Medication Administration"
    questionnaire_description = "Medication Administration"
    questionnaire_subject_type = SubjectType.patient.value
    filterset_class = MedicationAdministrationFilter
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        if not AuthorizationController.call(
            "can_view_clinical_data", self.request.user, self.get_patient_obj()
        ):
            raise PermissionDenied("Permission denied to user")
        return (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
            .select_related("patient", "encounter", "created_by", "updated_by")
        )


InternalQuestionnaireRegistry.register(MedicationAdministrationViewSet)
