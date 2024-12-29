from enum import Enum

from django.contrib.auth.password_validation import validate_password
from pydantic import UUID4, field_validator
from rest_framework.generics import get_object_or_404

from care.emr.models import Organization
from care.emr.resources.base import EMRResource
from care.emr.resources.patient.spec import GenderChoices
from care.users.models import User


class UserTypeOptions(str, Enum):
    doctor = "doctor"
    nurse = "nurse"
    staff = "staff"
    volunteer = "volunteer"


class UserBaseSpec(EMRResource):
    __model__ = User
    __exclude__ = ["geo_organization"]

    id: UUID4 | None = None

    first_name: str
    last_name: str
    phone_number: str


class UserUpdateSpec(UserBaseSpec):
    user_type: UserTypeOptions
    gender: GenderChoices


class UserCreateSpec(UserBaseSpec):
    geo_organization: UUID4
    password: str
    username: str
    email: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password):
        try:
            validate_password(password)
        except Exception as e:
            raise ValueError("Password is too weak") from e
        return password

    def perform_extra_deserialization(self, is_update, obj):
        obj.set_password(self.password)
        obj.geo_organization = get_object_or_404(
            Organization, external_id=self.geo_organization, org_type="govt"
        )


class UserSpec(UserBaseSpec):
    last_login: str
    profile_picture_url: str
    user_type: str
    gender: str

    @classmethod
    def perform_extra_serialization(cls, mapping, obj: User):
        mapping["id"] = str(obj.external_id)
        mapping["profile_picture_url"] = obj.read_profile_picture_url()


class UserRetrieveSpec(UserSpec):
    geo_organization: dict
    created_by: dict

    @classmethod
    def perform_extra_serialization(cls, mapping, obj: User):
        from care.emr.resources.organization.spec import OrganizationReadSpec

        super().perform_extra_serialization(mapping, obj)
        mapping["created_by"] = UserSpec.serialize(obj.created_by).to_json()
        if obj.geo_organization:
            mapping["geo_organization"] = OrganizationReadSpec.serialize(
                obj.geo_organization
            ).to_json()
