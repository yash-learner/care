from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied

from care.emr.api.viewsets.authz_base import EncounterBasedAuthorizationBase
from care.emr.api.viewsets.base import EMRModelViewSet, EMRQuestionnaireResponseMixin
from care.emr.models.medication_request import MedicationRequest
from care.emr.registries.system_questionnaire.system_questionnaire import (
    InternalQuestionnaireRegistry,
)
from care.emr.resources.medication.request.spec import (
    MedicationRequestReadSpec,
    MedicationRequestSpec,
)
from care.emr.resources.questionnaire.spec import SubjectType
from care.security.authorization import AuthorizationController


class MedicationRequestFilter(filters.FilterSet):
    encounter = filters.UUIDFilter(field_name="encounter__external_id")


class MedicationRequestViewSet(
    EncounterBasedAuthorizationBase, EMRQuestionnaireResponseMixin, EMRModelViewSet
):
    database_model = MedicationRequest
    pydantic_model = MedicationRequestSpec
    pydantic_read_model = MedicationRequestReadSpec
    questionnaire_type = "medication_request"
    questionnaire_title = "Medication Request"
    questionnaire_description = "Medication Request"
    questionnaire_subject_type = SubjectType.patient.value
    filterset_class = MedicationRequestFilter
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


InternalQuestionnaireRegistry.register(MedicationRequestViewSet)
