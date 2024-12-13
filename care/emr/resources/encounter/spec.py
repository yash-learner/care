# Not Being used
import datetime
from enum import Enum

from pydantic import UUID4, BaseModel

from care.emr.resources.base import EMRResource


class EncounterSpecBase(EMRResource):
    __model__ = None
    id: UUID4 = None


class StatusChoices(str, Enum):
    planned = "planned"
    in_progress = "in_progress"
    on_hold = "on_hold"
    discharged = "discharged"
    completed = "completed"
    cancelled = "cancelled"
    discontinued = "discontinued"
    entered_in_error = "entered_in_error"
    unknown = "unknown"


class ClassChoices(str, Enum):
    imp = "imp"
    amb = "amb"
    obsenc = "obsenc"
    emer = "emer"
    vr = "vr"
    hh = "hh"


class PeriodSpec(BaseModel):
    start: datetime.datetime
    end: datetime.datetime

    # TODO Add validation


class HospitalizationSpec(BaseModel):
    pass


class EncounterSpec(EncounterSpecBase):
    status: StatusChoices
    encounter_class: ClassChoices
    patient: UUID4
    period: PeriodSpec
    organization: UUID4 | None = None
    appointment: UUID4 | None = None
    hospitalization: HospitalizationSpec | None = None


class EncounterReadSpec(EncounterSpecBase):
    status_history: list = list
    class_history: list = list
    is_closed: bool = False
    length: int = 0
