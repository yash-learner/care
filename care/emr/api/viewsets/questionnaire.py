from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models import Questionnaire
from care.emr.resources.questionnaire.spec import (
    QuestionnaireReadSpec,
    QuestionnaireSpec,
)
from care.emr.resources.questionnaire.utils import handle_response
from care.emr.resources.questionnaire_response.spec import (
    QuestionnaireResponseReadSpec,
    QuestionnaireSubmitRequest,
)


class QuestionnaireViewSet(EMRModelViewSet):
    database_model = Questionnaire
    pydantic_model = QuestionnaireSpec
    pydantic_read_model = QuestionnaireReadSpec
    lookup_field = "slug"
    CREATE_QUESTIONNAIRE_RESPONSE = False

    def get_queryset(self):
        queryset = super().get_queryset()
        if "search" in self.request.GET:
            queryset = queryset.filter(title__icontains=self.request.GET.get("search"))
        return queryset.select_related("created_by", "updated_by")

    @action(detail=True, methods=["POST"])
    def submit(self, request, *args, **kwargs):
        request_params = QuestionnaireSubmitRequest(**request.data)
        questionnaire = self.get_object()
        with transaction.atomic():
            response = handle_response(questionnaire, request_params, request.user)
        return Response(
            QuestionnaireResponseReadSpec.serialize(response).model_dump(mode="json")
        )
