from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.condition import Condition
from care.emr.registries.system_questionnaire.system_questionnaire import (
    InternalQuestionnaireRegistry,
)
from care.emr.resources.condition.spec import ConditionSpec, ConditionSpecRead
from care.emr.resources.questionnaire.spec import SubjectType


class ConditionViewSet(EMRModelViewSet):
    database_model = Condition
    pydantic_model = ConditionSpec
    pydantic_read_model = ConditionSpecRead
    questionnaire_type = "condition"
    questionnaire_title = "Condition"
    questionnaire_description = "Condition"
    questionnaire_subject_type = SubjectType.patient.value

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
            .select_related("patient", "encounter")
        )


InternalQuestionnaireRegistry.register(ConditionViewSet)
