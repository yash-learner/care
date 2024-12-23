from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel, Field, field_validator

from care.emr.fhir.schema.base import Annotation, Coding, Period
from care.emr.models.diagnostic_report import DiagnosticReport
from care.emr.models.service_request import ServiceRequest
from care.emr.models.specimen import Specimen
from care.emr.registries.care_valueset.care_valueset import validate_valueset
from care.emr.resources.base import EMRResource
from care.emr.resources.diagnostic_report.valueset import (
    CARE_DIAGNOSTIC_REPORT_CATEGORY_VALUESET,
    CARE_DIAGNOSTIC_REPORT_CODE_VALUESET,
)
from care.emr.resources.observation.spec import ObservationSpec
from care.emr.resources.service_request.spec import ServiceRequestReadSpec
from care.emr.resources.specimen.spec import SpecimenReadSpec
from care.facility.api.serializers.patient import PatientDetailSerializer
from care.facility.api.serializers.patient_consultation import (
    PatientConsultationSerializer,
)
from care.users.api.serializers.user import UserBaseMinimumSerializer
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
    status: StatusChoices = Field(
        default=StatusChoices.registered,
        description="Indicates the status of the report, used internally to track the lifecycle of the report",
    )

    category: Coding | None = Field(
        default=None,
        json_schema_extra={"slug": CARE_DIAGNOSTIC_REPORT_CATEGORY_VALUESET.slug},
        description="Identifies the broad category of service that is to be performed",
    )
    code: Coding = Field(
        default=None,
        json_schema_extra={"slug": CARE_DIAGNOSTIC_REPORT_CODE_VALUESET.slug},
        description="Name/Code for this diagnostic report",
    )

    based_on: UUID4 = Field(
        ...,
        description="The resource that this report is based on, this can be a service request, a medication request, or other resource",
    )
    subject: UUID4 = Field(
        default=None,
        description="The patient this report is about",
    )
    encounter: UUID4 = Field(
        default=None,
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

    note: list[Annotation] = Field(
        default=[],
        description="Comments made about the service request by the requester, performer, subject, or other participants",
    )
    conclusion: str | None = Field(
        default=None,
        description="The clinical conclusion of the report",
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
            obj.based_on = ServiceRequest.objects.get(external_id=self.based_on)
            obj.subject = obj.based_on.subject
            obj.encounter = obj.based_on.encounter

            if not obj.code:
                obj.code = obj.based_on.code

            if self.performer:
                obj.performer = User.objects.get(external_id=self.performer)

            if self.results_interpreter:
                obj.results_interpreter = User.objects.get(
                    external_id=self.results_interpreter
                )

            obj.save()

            if self.specimen:
                specimens = Specimen.objects.filter(external_id__in=self.specimen)
                if specimens.count() != len(self.specimen):
                    message = "One or more specimens are not found in the database"
                    raise ValueError(message)
                obj.specimen.set(specimens)


class DiagnosticReportReadSpec(BaseDiagnosticReportSpec):
    __exclude__ = []

    status: str

    category: Coding | None
    code: Coding

    based_on: ServiceRequestReadSpec
    subject: dict
    encounter: dict

    performer: dict | None
    results_interpreter: dict | None

    issued: datetime | None
    effective_period: Period | None

    specimen: list[SpecimenReadSpec]
    result: list[ObservationSpec]

    media: list[DiagnosticReportMedia]

    note: list[Annotation]
    conclusion: str | None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["based_on"] = ServiceRequestReadSpec.serialize(obj.based_on).model_dump(
            exclude=["meta"]
        )
        mapping["id"] = obj.external_id

        mapping["subject"] = PatientDetailSerializer(obj.subject).data
        mapping["encounter"] = PatientConsultationSerializer(obj.encounter).data

        if obj.performer:
            mapping["performer"] = UserBaseMinimumSerializer(obj.performer).data

        if obj.results_interpreter:
            mapping["results_interpreter"] = UserBaseMinimumSerializer(
                obj.results_interpreter
            ).data

        mapping["specimen"] = [
            SpecimenReadSpec.serialize(specimen).model_dump(exclude=["meta"])
            for specimen in obj.specimen.all()
        ]
        mapping["result"] = [
            ObservationSpec.serialize(observation).model_dump(exclude=["meta"])
            for observation in obj.result.all()
        ]


class DiagnosticReportObservationRequest(BaseModel):
    observations: list[ObservationSpec] = Field(
        default=[],
        description="List of observations that are part of the diagnostic report",
    )


class DiagnosticReportVerifyRequest(BaseModel):
    is_approved: bool = Field(
        ...,
        description="Indicates whether the diagnostic report is approved or rejected",
    )


class DiagnosticReportReviewRequest(BaseModel):
    is_approved: bool = Field(
        ...,
        description="Indicates whether the diagnostic report is approved or rejected",
    )
    conclusion: str | None = Field(
        default=None,
        description="Additional notes about the review",
    )
