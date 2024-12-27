import datetime
from enum import Enum

from django.utils import timezone
from pydantic import UUID4, field_validator, model_validator

from care.emr.models import Organization
from care.emr.models.patient import Patient
from care.emr.resources.base import EMRResource
from care.emr.resources.organization.spec import OrganizationReadSpec
from care.emr.resources.user.spec import UserSpec


class BloodGroupChoices(str, Enum):
    A_negative = "A_negative"
    A_positive = "A_positive"
    B_negative = "B_negative"
    B_positive = "B_positive"
    AB_negative = "AB_negative"
    AB_positive = "AB_positive"
    O_negative = "O_negative"
    O_positive = "O_positive"


class GenderChoices(str, Enum):
    male = "male"
    female = "female"
    non_binary = "non_binary"
    transgender = "transgender"


class PatientBaseSpec(EMRResource):
    __model__ = Patient
    __exclude__ = ["geo_organization"]

    id: UUID4 | None = None
    name: str
    gender: GenderChoices
    phone_number: str
    emergency_phone_number: str | None = None
    address: str
    permanent_address: str
    pincode: int
    date_of_birth: datetime.date
    age: int | None = None
    death_datetime: datetime.datetime | None = None
    blood_group: BloodGroupChoices | None = None


class PatientCreateSpec(PatientBaseSpec):
    geo_organization: UUID4

    @model_validator(mode="after")
    def validate_age(self):
        if not (self.age or self.date_of_birth):
            raise ValueError("Either age or date of birth is required")
        return self

    @field_validator("geo_organization")
    @classmethod
    def validate_geo_organization(cls, geo_organization):
        if not Organization.objects.filter(
            org_type="govt", external_id=geo_organization
        ).exists():
            raise ValueError("Geo Organization does not exist")
        return geo_organization

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            obj.geo_organization = Organization.objects.get(
                external_id=self.geo_organization
            )
            if self.age:
                obj.year_of_birth = timezone.now().date().year - self.age
            else:
                obj.year_of_birth = self.date_of_birth.year


class PatientListSpec(PatientBaseSpec):
    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id


class PatientRetrieveSpec(PatientListSpec):
    geo_organization: dict = {}

    created_by: UserSpec | None = None
    updated_by: UserSpec | None = None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        super().perform_extra_serialization(mapping, obj)
        if obj.geo_organization:
            mapping["geo_organization"] = OrganizationReadSpec.serialize(
                obj.geo_organization
            ).to_json()
        if obj.created_by:
            mapping["created_by"] = UserSpec.serialize(obj.created_by).to_json()
        if obj.updated_by:
            mapping["updated_by"] = UserSpec.serialize(obj.updated_by).to_json()
