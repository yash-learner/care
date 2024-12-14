import datetime

from pydantic import UUID4

from care.emr.resources.base import EMRResource
from care.facility.models import PatientRegistration


class PatientOTPBaseSpec(EMRResource):
    __model__ = PatientRegistration


class PatientOTPReadSpec(PatientOTPBaseSpec):
    id: UUID4
    name: str
    gender: str
    phone_number: str
    emergency_phone_number: str
    address: str
    date_of_birth: datetime.date
    year_of_birth: int
