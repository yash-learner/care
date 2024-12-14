from pydantic import UUID4

from care.emr.resources.base import EMRResource
from care.facility.models import PatientRegistration


class PatientBaseSpec(EMRResource):
    __model__ = PatientRegistration


class PatientReadSpec(PatientBaseSpec):
    id: UUID4
