from datetime import UTC, datetime

from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet, EMRQuestionnaireResponseMixin
from care.emr.models.medication_request import MedicationRequest
from care.emr.registries.system_questionnaire.system_questionnaire import (
    InternalQuestionnaireRegistry,
)
from care.emr.resources.medication.request.spec import (
    MedicationRequestDiscontinueRequest,
    MedicationRequestReadSpec,
    MedicationRequestSpec,
    MedicationRequestStatus,
)
from care.emr.resources.questionnaire.spec import SubjectType


class MedicationRequestFilter(filters.FilterSet):
    encounter = filters.UUIDFilter(field_name="encounter__external_id")
    status = filters.MultipleChoiceFilter(
        field_name="status", choices=MedicationRequestStatus.choices()
    )
    is_prn = filters.BooleanFilter(method="filter_as_needed_boolean")

    def filter_as_needed_boolean(self, queryset, name, value):
        return queryset.filter(
            dosage_instruction__contains=[{"as_needed_boolean": value}]
        )


class MedicationRequestViewSet(EMRQuestionnaireResponseMixin, EMRModelViewSet):
    database_model = MedicationRequest
    pydantic_model = MedicationRequestSpec
    pydantic_read_model = MedicationRequestReadSpec
    questionnaire_type = "medication_request"
    questionnaire_title = "Medication Request"
    questionnaire_description = "Medication Request"
    questionnaire_subject_type = SubjectType.patient.value
    filterset_class = MedicationRequestFilter
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(patient__external_id=self.kwargs["patient_external_id"])
            .select_related("patient", "encounter", "created_by", "updated_by")
        )

    @extend_schema(
        request=MedicationRequestDiscontinueRequest,
        responses={200: MedicationRequestReadSpec},
        tags=["medication_request"],
    )
    @action(detail=True, methods=["POST"])
    def discontinue(self, request, *args, **kwargs):
        data = MedicationRequestDiscontinueRequest(**request.data)
        request: MedicationRequest = self.get_object()

        request.status = MedicationRequestStatus.ended
        request.status_changed = datetime.now(UTC)
        request.status_reason = data.status_reason
        request.save()

        return Response(
            self.get_read_pydantic_model()
            .serialize(request)
            .model_dump(exclude=["meta"]),
        )


InternalQuestionnaireRegistry.register(MedicationRequestViewSet)
