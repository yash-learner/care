from datetime import UTC, datetime
from enum import Enum

from pydantic import UUID4, Field, field_validator

from care.emr.fhir.schema.base import Annotation, Coding, Timing
from care.emr.models.service_request import ServiceRequest
from care.emr.registries.care_valueset.care_valueset import validate_valueset
from care.emr.resources.base import EMRResource
from care.emr.resources.service_request.valueset import (
    CARE_LAB_ORDER_CODE_VALUESET,
    CARE_MEDICATION_AS_NEEDED_REASON_VALUESET,
    CARE_SERVICE_REQUEST_CATEGORY_VALUESET,
)
from care.facility.api.serializers.patient import PatientDetailSerializer
from care.facility.api.serializers.patient_consultation import (
    PatientConsultationSerializer,
)
from care.facility.models.ambulance import User
from care.facility.models.patient_consultation import PatientConsultation
from care.users.api.serializers.user import UserBaseMinimumSerializer


class BaseServiceRequestSpec(EMRResource):
    __model__ = ServiceRequest
    __exclude__ = ["subject", "encounter", "requester"]
    id: UUID4 = None


class StatusChoices(str, Enum):
    draft = "draft"
    active = "active"
    on_hold = "on-hold"
    revoked = "revoked"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class IntentChoices(str, Enum):
    proposal = "proposal"
    plan = "plan"
    directive = "directive"
    order = "order"


class PriorityChoices(str, Enum):
    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class ServiceRequestSpec(BaseServiceRequestSpec):
    status: StatusChoices = Field(
        default=StatusChoices.draft,
        description="Indicates the status of the request, used internally to track the lifecycle of the request",
    )
    intent: IntentChoices = Field(
        default=IntentChoices.order,
        description="Indicates the level of authority/intentionality associated with the request",
    )
    priority: PriorityChoices = Field(
        default=PriorityChoices.routine,
        description="Indicates the urgency of the request",
    )

    category: Coding | None = Field(
        default=None,
        json_schema_extra={"slug": CARE_SERVICE_REQUEST_CATEGORY_VALUESET.slug},
        description="Identifies the broad category of service that is to be performed",
    )
    code: Coding = Field(
        ...,
        json_schema_extra={
            "slug": CARE_LAB_ORDER_CODE_VALUESET.slug
        },  # TODO: consider using a broader value set (https://build.fhir.org/valueset-procedure-code.html)
        description="Identifies the service or product to be supplied",
    )

    do_not_perform: bool = Field(
        default=False,
        description="If true indicates that the service/procedure should NOT be performed",
    )

    subject: UUID4 = Field(
        ...,
        description="The patient for whom the service/procedure is being requested",
    )
    encounter: UUID4 = Field(
        ...,
        description="The encounter within which this service request was created",
    )

    occurrence_datetime: datetime | None = Field(
        default=None,
        description="The datetime at which the requested service should occur",
    )
    occurrence_timing: Timing | None = Field(
        default=None,
        description="The timing schedule for the requested service, used when the occurrence repeats",
    )
    as_needed: bool = Field(
        default=False,
        description="If true indicates that the service/procedure can be performed as needed",
    )
    as_needed_for: Coding | None = Field(
        default=None,
        json_schema_extra={"slug": CARE_MEDICATION_AS_NEEDED_REASON_VALUESET.slug},
        description="The condition under which the service/procedure should be performed",
    )

    authored_on: datetime = Field(
        default=datetime.now(UTC),
        description="The date when the request was made",
    )
    requester: UUID4 = Field(
        ...,
        description="The individual who initiated the request and has responsibility for its activation",
    )

    location: UUID4 | None = Field(
        default=None,
        description="The location where the service will be performed",
    )

    note: list[Annotation] = Field(
        default=[],
        description="Comments made about the service request by the requester, performer, subject, or other participants",
    )
    patient_instruction: str = Field(
        default="",
        description="Instructions for the patient on how the service should be performed",
    )

    replaces: UUID4 | None = Field(
        None,
        description="The request that is being replaced by this request, used in the case of re-orders",
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

    @field_validator("as_needed_for")
    @classmethod
    def validate_as_needed_for(cls, value: str):
        return validate_valueset(
            "as_needed_for",
            cls.model_fields["as_needed_for"].json_schema_extra["slug"],
            value,
        )

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            obj.encounter = PatientConsultation.objects.get(external_id=self.encounter)
            obj.subject = obj.encounter.patient
            obj.requester = User.objects.get(external_id=self.requester)


class ServiceRequestReadSpec(BaseServiceRequestSpec):
    __exclude__ = []
    external_id: (
        UUID4  # TODO: remove this field and do a model dump when accessing any models
    )

    status: str
    intent: str
    priority: str

    category: Coding | None
    code: Coding

    do_not_perform: bool

    subject: dict
    encounter: dict

    occurrence_datetime: datetime | None
    occurrence_timing: Timing | None
    as_needed: bool
    as_needed_for: Coding | None

    authored_on: datetime
    requester: dict

    location: dict | None

    note: list[Annotation]
    patient_instruction: str

    replaces: dict | None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id

        mapping["subject"] = PatientDetailSerializer(obj.subject).data
        mapping["encounter"] = PatientConsultationSerializer(obj.encounter).data

        mapping["requester"] = UserBaseMinimumSerializer(obj.requester).data

        mapping["replaces"] = (
            ServiceRequestReadSpec.serialize(obj.replaces).model_dump(exclude=["meta"])
            if obj.replaces
            else None
        )
