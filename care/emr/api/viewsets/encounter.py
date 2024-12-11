from rest_framework.decorators import action

from care.emr.api.viewsets.base import EMRBaseViewSet
from care.emr.models.questionnaire import QuestionnaireResponse
from care.emr.resources.questionnaire_response.spec import QuestionnaireResponseReadSpec


class EncounterViewSet(EMRBaseViewSet):
    lookup_field = "external_id"

    @action(detail=True, methods=["GET"])
    def questionnaire_responses(self, request, *args, **kwargs):
        queryset = (
            QuestionnaireResponse.objects.filter(
                encounter=self.kwargs["external_id"],
                patient=self.kwargs["patient_external_id"],
            )
            .order_by("-created_date")
            .select_related("questionnaire")
        )
        if "questionnaire_slugs" in request.query_params:
            questionnaire_slugs = request.query_params.get("questionnaire_slugs").split(
                ","
            )
            queryset = queryset.filter(questionnaire__slug__in=questionnaire_slugs)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        data = [
            QuestionnaireResponseReadSpec.serialize(obj).model_dump() for obj in page
        ]
        return paginator.get_paginated_response(data)
