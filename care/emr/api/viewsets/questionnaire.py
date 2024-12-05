from django.db import transaction
from pydantic import UUID4, BaseModel
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.fhir.schema.base import Coding
from care.emr.models import Questionnaire
from care.emr.models.questionnaire import QuestionnaireResponse
from care.emr.registries.system_questionnaire.system_questionnaire import (
    InternalQuestionnaireRegistry,
)
from care.emr.resources.questionnaire.spec import (
    QuestionnaireReadSpec,
    QuestionnaireSpec,
)
from care.emr.resources.questionnaire.utils import handle_response
from care.emr.resources.questionnaire_response.spec import QuestionnaireResponseReadSpec


class QuestionnaireSubmitResultValue(BaseModel):
    value: str
    value_code: Coding = None


class QuestionnaireSubmitResult(BaseModel):
    question_id: UUID4
    body_site: Coding = None
    method: Coding = None
    value: QuestionnaireSubmitResultValue
    values: list[QuestionnaireSubmitResultValue] = []
    note: str = None


class QuestionnaireSubmitRequest(BaseModel):
    resource_id: UUID4
    encounter: UUID4
    results: list[QuestionnaireSubmitResult]


class QuestionnaireViewSet(EMRModelViewSet):
    database_model = Questionnaire
    pydantic_model = QuestionnaireSpec
    pydantic_read_model = QuestionnaireReadSpec

    def get_queryset(self):
        queryset = super().get_queryset()
        if "search" in self.request.GET:
            queryset = queryset.filter(title__icontains=self.request.GET.get("search"))
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = [
            self.get_read_pydantic_model().serialize(obj).model_dump(exclude=["meta"])
            for obj in queryset
        ]
        response = InternalQuestionnaireRegistry.search_questionnaire(
            request.GET.get("search", "")
        )
        response.extend(data)
        return Response({"results": response})

    @action(detail=True, methods=["POST"])
    def submit(self, request, *args, **kwargs):
        request_params = QuestionnaireSubmitRequest(**request.data)
        questionnaire = self.get_object()
        with transaction.atomic():
            response = handle_response(questionnaire, request_params, request.user)
        return Response(response)

    @action(detail=True, methods=["GET"])
    def past_responses(self, request, *args, **kwargs):
        obj = self.get_object()
        queryset = QuestionnaireResponse.objects.filter(questionnaire=obj).order_by(
            "-created_date"
        )
        if "encounter" in self.request.GET:
            queryset = queryset.filter(encounter=self.request.GET["encounter"])
        elif "patient" in self.request.GET:
            queryset = queryset.filter(patient=self.request.GET["patient"])
        else:
            pass
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        data = [
            QuestionnaireResponseReadSpec.serialize(obj).model_dump() for obj in page
        ]
        return paginator.get_paginated_response(data)
