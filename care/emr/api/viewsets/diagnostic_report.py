from django_filters import FilterSet, UUIDFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.diagnostic_report import DiagnosticReport
from care.emr.models.observation import Observation
from care.emr.resources.diagnostic_report.spec import (
    DiagnosticReportObservationRequest,
    DiagnosticReportReadSpec,
    DiagnosticReportReviewRequest,
    DiagnosticReportSpec,
    DiagnosticReportVerifyRequest,
    StatusChoices,
)
from care.emr.resources.observation.spec import Performer, PerformerType


class DiagnosticReportFilters(FilterSet):
    subject = UUIDFilter(field_name="subject__external_id")
    encounter = UUIDFilter(field_name="encounter__external_id")


@extend_schema_view(
    create=extend_schema(request=DiagnosticReportSpec),
)
class DiagnosticReportViewSet(EMRModelViewSet):
    database_model = DiagnosticReport
    pydantic_model = DiagnosticReportSpec
    pydantic_read_model = DiagnosticReportReadSpec
    filter_backends = [DjangoFilterBackend]
    filterset_class = DiagnosticReportFilters

    @extend_schema(
        request=DiagnosticReportObservationRequest,
        responses={200: DiagnosticReportReadSpec},
        tags=["diagnostic_report"],
    )
    @action(detail=True, methods=["POST"])
    def observations(self, request, *args, **kwargs):
        data = DiagnosticReportObservationRequest(**request.data)
        report: DiagnosticReport = self.get_object()

        observations = []
        for observation in data.observations:
            if not observation.performer:
                observation.performer = Performer(
                    type=PerformerType.user,
                    id=str(request.user.external_id),
                )

            observation_instance = observation.de_serialize()
            observation_instance.subject_id = report.subject.id
            observation_instance.encounter = report.encounter
            observation_instance.patient = report.subject

            observations.append(observation_instance)

        observation_instances = Observation.objects.bulk_create(observations)
        report.result.set(observation_instances)
        report.status = StatusChoices.partial
        report.save()

        return Response(
            self.get_read_pydantic_model()
            .serialize(report)
            .model_dump(exclude=["meta"]),
        )

    @extend_schema(
        request=DiagnosticReportVerifyRequest,
        responses={200: DiagnosticReportReadSpec},
        tags=["diagnostic_report"],
    )
    @action(detail=True, methods=["POST"])
    def verify(self, request, *args, **kwargs):
        data = DiagnosticReportVerifyRequest(**request.data)
        report: DiagnosticReport = self.get_object()

        if data.is_approved:
            report.status = StatusChoices.preliminary
        else:
            report.status = StatusChoices.cancelled

        report.save()

        return Response(
            self.get_read_pydantic_model()
            .serialize(report)
            .model_dump(exclude=["meta"]),
        )

    @extend_schema(
        request=DiagnosticReportReviewRequest,
        responses={200: DiagnosticReportReadSpec},
        tags=["diagnostic_report"],
    )
    @action(detail=True, methods=["POST"])
    def review(self, request, *args, **kwargs):
        data = DiagnosticReportReviewRequest(**request.data)
        report: DiagnosticReport = self.get_object()

        if (
            report.results_interpreter
            and report.results_interpreter.external_id != request.user.external_id
        ):
            return Response(
                {"detail": "This report is assigned to a different user for review."},
                status=403,
            )

        if data.is_approved:
            report.status = StatusChoices.final
        else:
            report.status = StatusChoices.cancelled

        report.conclusion = data.conclusion
        report.results_interpreter = request.user
        report.save()

        return Response(
            self.get_read_pydantic_model()
            .serialize(report)
            .model_dump(exclude=["meta"]),
        )
