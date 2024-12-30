from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied

from care.emr.api.viewsets.authz_base import EncounterBasedAuthorizationBase
from care.emr.api.viewsets.base import EMRModelViewSet, EMRQuestionnaireResponseMixin
from care.emr.models.medication_statement import MedicationStatement
from care.emr.registries.system_questionnaire.system_questionnaire import (
    InternalQuestionnaireRegistry,
)
from care.emr.resources.medication.statement.spec import (
    MedicationStatementReadSpec,
    MedicationStatementSpec,
)
from care.emr.resources.questionnaire.spec import SubjectType
from care.security.authorization import AuthorizationController


class MedicationStatementFilter(filters.FilterSet):
    encounter = filters.UUIDFilter(field_name="encounter__external_id")


class MedicationStatementViewSet(
    EncounterBasedAuthorizationBase, EMRQuestionnaireResponseMixin, EMRModelViewSet
):
    database_model = MedicationStatement
    pydantic_model = MedicationStatementSpec
    pydantic_read_model = MedicationStatementReadSpec
    questionnaire_type = "medication_statement"
    questionnaire_title = "Medication Statement"
    questionnaire_description = "Medication Statement"
    questionnaire_subject_type = SubjectType.patient.value
    filterset_class = MedicationStatementFilter
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


InternalQuestionnaireRegistry.register(MedicationStatementViewSet)
