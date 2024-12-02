from drf_spectacular.utils import extend_schema, extend_schema_view

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.allergy_intolerance import AllergyIntolerance
from care.emr.registries.system_questionnaire.system_questionnaire import (
    InternalQuestionnaireRegistry,
)
from care.emr.resources.allergy_intolerance.spec import (
    AllergyIntoleranceSpec,
    AllergyIntrolanceSpecRead,
)
from care.emr.resources.questionnaire.spec import SubjectType


@extend_schema_view(
    create=extend_schema(request=AllergyIntoleranceSpec),
)
class AllergyIntoleranceViewSet(EMRModelViewSet):
    database_model = AllergyIntolerance
    pydantic_model = AllergyIntoleranceSpec
    pydantic_read_model = AllergyIntrolanceSpecRead
    questionnaire_type = "allergy_intolerance"
    questionnaire_title = "Allergy Intolerance"
    questionnaire_description = "Allergy Intolerance"
    questionnaire_subject_type = SubjectType.patient.value

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
            .select_related("patient", "encounter")
        )


InternalQuestionnaireRegistry.register(AllergyIntoleranceViewSet)
