import datetime

from pydantic import UUID4

from care.emr.resources.base import EMRResource
from care.emr.resources.organization.spec import OrganizationReadSpec
from care.emr.resources.user.spec import UserSpec
from care.facility.models import REVERSE_BLOOD_GROUP_CHOICES, PatientRegistration
from care.users.models import REVERSE_GENDER_CHOICES


class PatientBaseSpec(EMRResource):
    __model__ = PatientRegistration
    __exclude__ = []

    id: UUID4


class PatientListSpec(PatientBaseSpec):
    name: str
    gender: str
    phone_number: str
    emergency_phone_number: str
    address: str
    permanent_address: str
    pincode: int
    date_of_birth: datetime.date
    year_of_birth: int
    death_datetime: datetime.datetime
    nationality: str
    passport_no: str | None = None
    blood_group: str
    geo_organization: dict | None = None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["gender"] = REVERSE_GENDER_CHOICES[obj.gender]
        mapping["blood_group"] = REVERSE_BLOOD_GROUP_CHOICES[obj.blood_group]
        if obj.geo_organization:
            mapping["geo_organization"] = OrganizationReadSpec.serialize(
                obj.geo_organization
            ).to_json()


class PatientRetrieveSpec(PatientListSpec):
    created_by: UserSpec | None = None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        super().perform_extra_serialization(mapping, obj)
        if obj.created_by:
            mapping["created_by"] = UserSpec.serialize(obj.created_by).to_json()
