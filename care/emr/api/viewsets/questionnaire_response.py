
from care.emr.api.viewsets.base import EMRModelReadOnlyViewSet
from care.emr.models.questionnaire import QuestionnaireResponse
from care.emr.resources.questionnaire_response.spec import QuestionnaireResponseReadSpec
from django_filters import rest_framework as filters


class QuestionnaireResponseFilters(filters.FilterSet):
    encounter = filters.CharFilter()


class QuestionnaireResponseViewSet(EMRModelReadOnlyViewSet):
    database_model = QuestionnaireResponse
    pydantic_model = QuestionnaireResponseReadSpec
    pydantic_read_model = QuestionnaireResponseReadSpec
    filterset_class = QuestionnaireResponseFilters
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        print("fdgdf")
        queryset = (
            QuestionnaireResponse.objects.filter(
                patient=self.kwargs["patient_external_id"],
            )
            .order_by("-created_date")
            .select_related("questionnaire")
        )
        if "questionnaire_slugs" in self.request.GET:
            questionnaire_slugs = self.request.GET.get(
                "questionnaire_slugs"
            ).split(",")
            queryset = queryset.filter(questionnaire__slug__in=questionnaire_slugs)
        return queryset
