from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.medication_request import MedicationRequest
from care.emr.registries.system_questionnaire.system_questionnaire import (
    InternalQuestionnaireRegistry,
)
from care.emr.resources.medication.request.spec import MedicationRequestSpec
from care.emr.resources.questionnaire.spec import SubjectType


class MedicationRequestViewSet(EMRModelViewSet):
    database_model = MedicationRequest
    pydantic_model = MedicationRequestSpec
    pydantic_read_model = MedicationRequestSpec
    questionnaire_type = "medication_request"
    questionnaire_title = "Medication Request"
    questionnaire_description = "Medication Request"
    questionnaire_subject_type = SubjectType.patient.value

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(encounter__external_id=self.kwargs["consultation_external_id"])
            .select_related("patient", "encounter")
        )

    def clean_create_data(self, request, *args, **kwargs):
        data = request.data
        data["encounter"] = self.kwargs["consultation_external_id"]
        data["patient"] = None
        return data


InternalQuestionnaireRegistry.register(MedicationRequestViewSet)
