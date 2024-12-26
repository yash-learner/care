import datetime
from enum import Enum

from django.utils import timezone
from pydantic import UUID4, model_validator

from care.emr.resources.base import EMRResource
from care.facility.models import PatientRegistration
from care.users.models import District, LocalBody, State, Ward


class GenderChoices(str, Enum):
    Male = 1
    Female = 2
    Non_Binary = 3


class PatientOTPBaseSpec(EMRResource):
    __model__ = PatientRegistration
    __exclude__ = ["state", "district", "local_body", "ward"]
    id: UUID4 = None


class PatientOTPReadSpec(PatientOTPBaseSpec):
    name: str
    gender: str
    phone_number: str
    emergency_phone_number: str
    address: str
    pincode: int
    state: str
    district: str
    local_body: str
    ward: str
    date_of_birth: datetime.date
    year_of_birth: int

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["state"] = obj.state.name if obj.state else None
        mapping["district"] = obj.district.name if obj.district else None
        mapping["local_body"] = obj.local_body.name if obj.local_body else None
        mapping["ward"] = obj.ward.name if obj.ward else None


class PatientOTPWriteSpec(PatientOTPBaseSpec):
    name: str
    gender: GenderChoices
    date_of_birth: datetime.date | None = None
    age: int | None = None
    address: str
    pincode: int
    state: int
    district: int
    local_body: int
    ward: int | None = None

    @model_validator(mode="after")
    def validage_age(self):
        if not (self.age or self.date_of_birth):
            raise ValueError("Either age or date of birth is required")
        return self

    @model_validator(mode="after")
    def validate_governance(self):
        state = State.objects.filter(id=self.state).first()
        if not state:
            raise ValueError("Invalid State")
        district = District.objects.filter(id=self.district, state=self.state).first()
        if not district:
            raise ValueError("Invalid District")
        local_body = LocalBody.objects.filter(
            id=self.local_body, district=self.district
        ).first()
        if not local_body:
            raise ValueError("Invalid Local Body")
        if (
            self.ward
            and not Ward.objects.filter(id=self.ward, local_body=local_body).exists()
        ):
            raise ValueError("Invalid Ward")
        return self

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            obj.state = State.objects.get(id=self.state)
            obj.district = District.objects.get(id=self.district)
            obj.local_body = LocalBody.objects.get(id=self.local_body)
            if self.ward:
                obj.ward = Ward.objects.get(id=self.ward)
            if self.age:
                obj.year_of_birth = timezone.now().date().year - self.age
            else:
                obj.year_of_birth = self.date_of_birth.year
