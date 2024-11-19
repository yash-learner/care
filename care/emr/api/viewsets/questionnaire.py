from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.resources.questionnaire.spec import QuestionnaireSpec


class QuestionnaireViewSet(EMRModelViewSet):
    database_model = QuestionnaireSpec
    pydantic_model = QuestionnaireSpec

    def get_queryset(self):
        return super().get_queryset().select_related("patient", "encounter")
