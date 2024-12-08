from rest_framework.decorators import action

from care.emr.api.viewsets.base import EMRBaseViewSet
from care.emr.models.questionnaire import QuestionnaireResponse
from care.emr.resources.questionnaire_response.spec import QuestionnaireResponseReadSpec


class EncounterViewSet(EMRBaseViewSet):
    lookup_field = "external_id"

    @action(detail=True, methods=["GET"])
    def questionnaire_responses(self, request, *args, **kwargs):
        queryset = QuestionnaireResponse.objects.filter(
            encounter=self.kwargs["external_id"],
            patient=self.kwargs["patient_external_id"],
        ).order_by("-created_date")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        data = [
            QuestionnaireResponseReadSpec.serialize(obj).model_dump() for obj in page
        ]
        return paginator.get_paginated_response(data)
