from drf_spectacular.utils import extend_schema, extend_schema_view

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.diagnostic_report import DiagnosticReport
from care.emr.resources.diagnostic_report.spec import (
    DiagnosticReportReadSpec,
    DiagnosticReportSpec,
)


@extend_schema_view(
    create=extend_schema(request=DiagnosticReportSpec),
)
class DiagnosticReportViewSet(EMRModelViewSet):
    database_model = DiagnosticReport
    pydantic_model = DiagnosticReportSpec
    pydantic_read_model = DiagnosticReportReadSpec
