from datetime import datetime
from enum import Enum

from pydantic import UUID4, Field, field_validator

from care.emr.fhir.schema.base import Annotation, Coding, Period
from care.emr.models.diagnostic_report import DiagnosticReport
from care.emr.models.service_request import ServiceRequest
from care.emr.registries.care_valueset.care_valueset import validate_valueset
from care.emr.resources.base import EMRResource
from care.emr.resources.diagnostic_report.valueset import (
    CARE_DIAGNOSTIC_REPORT_CATEGORY_VALUESET,
    CARE_DIAGNOSTIC_REPORT_CODE_VALUESET,
)
from care.users.models import User


class BaseDiagnosticReportSpec(EMRResource):
    __model__ = DiagnosticReport
    __exclude__ = [
        "subject",
        "based_on",
        "encounter",
        "performer",
        "results_interpreter",
    ]
    id: UUID4 = None


class DiagnosticReportMedia(EMRResource):
    comment: str | None = Field(
        default=None,
        description="A description or comment about the media file",
    )
    link: UUID4 = Field(
        ...,
        description="References the FileUpload object that contains the media file",
    )


class StatusChoices(str, Enum):
    registered = "registered"
    partial = "partial"
    preliminary = "preliminary"
    modified = "modified"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    appended = "appended"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class DiagnosticReportSpec(BaseDiagnosticReportSpec):
    status: StatusChoices | None = Field(
        default=None,
        description="Indicates the status of the report, used internally to track the lifecycle of the report",
    )

    category: Coding | None = Field(
        default=None,
        json_schema_extra={"slug": CARE_DIAGNOSTIC_REPORT_CATEGORY_VALUESET.slug},
        description="Identifies the broad category of service that is to be performed",
    )
    code: Coding = Field(
        ...,
        json_schema_extra={"slug": CARE_DIAGNOSTIC_REPORT_CODE_VALUESET.slug},
        description="Name/Code for this diagnostic report",
    )

    based_on: UUID4 = Field(
        ...,
        description="The resource that this report is based on, this can be a service request, a medication request, or other resource",
    )
    subject: UUID4 = Field(
        ...,
        description="The patient this report is about",
    )
    encounter: UUID4 = Field(
        ...,
        description="The encounter within which this report was created",
    )

    performer: UUID4 | None = Field(
        default=None,
        description="The user that is responsible for the report",
    )
    results_interpreter: UUID4 | None = Field(
        default=None,
        description="The primary result interpreter",
    )

    issued: datetime | None = Field(
        default=None,
        description="The datetime at which the report was issued",
    )
    effective_period: Period | None = Field(
        default=None,
        description="The period during which the report is valid",
    )

    specimen: list[UUID4] = Field(
        default=[],
        description="The specimens on which this report is based",
    )
    result: list[UUID4] = Field(
        default=[],
        description="The observations that are part of this report",
    )

    media: list[DiagnosticReportMedia] = Field(
        default=[],
        description="Media files associated with the report",
    )

    conclusion: str | None = Field(
        default=None,
        description="The clinical conclusion of the report",
    )

    note: list[Annotation] = Field(
        default=[],
        description="Comments made about the service request by the requester, performer, subject, or other participants",
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str):
        return validate_valueset(
            "category", cls.model_fields["category"].json_schema_extra["slug"], value
        )

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str):
        return validate_valueset(
            "code", cls.model_fields["code"].json_schema_extra["slug"], value
        )

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            obj.based_on = ServiceRequest.objects.get(external_id=self.request)
            obj.subject = obj.request.subject
            obj.encounter = obj.request.encounter

            if self.performer:
                obj.performer = User.objects.get(external_id=self.performer)

            if self.results_interpreter:
                obj.results_interpreter = User.objects.get(
                    external_id=self.results_interpreter
                )


class DiagnosticReportReadSpec(BaseDiagnosticReportSpec):
    status: str

    category: Coding | None
    code: Coding

    based_on: UUID4
    subject: UUID4
    encounter: UUID4

    performer: UUID4 | None
    results_interpreter: UUID4 | None

    issued: datetime | None
    effective_period: Period | None

    specimen: list[UUID4]
    result: list[UUID4]

    media: list[DiagnosticReportMedia]

    conclusion: str | None

    note: list[Annotation]
