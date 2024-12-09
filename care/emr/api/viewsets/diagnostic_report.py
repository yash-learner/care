from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.diagnostic_report import DiagnosticReport
from care.emr.models.observation import Observation
from care.emr.resources.diagnostic_report.spec import (
    DiagnosticReportObservationRequest,
    DiagnosticReportReadSpec,
    DiagnosticReportSpec,
)
from care.emr.resources.observation.spec import Performer, PerformerType


@extend_schema_view(
    create=extend_schema(request=DiagnosticReportSpec),
)
class DiagnosticReportViewSet(EMRModelViewSet):
    database_model = DiagnosticReport
    pydantic_model = DiagnosticReportSpec
    pydantic_read_model = DiagnosticReportReadSpec

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
        report.save()

        return Response(
            self.get_read_pydantic_model()
            .serialize(report)
            .model_dump(exclude=["meta"]),
        )
