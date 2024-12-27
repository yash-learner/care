from enum import Enum


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


COMPLETED_CHOICES = [
    StatusChoices.completed.value,
    StatusChoices.cancelled.value,
    StatusChoices.entered_in_error.value,
    StatusChoices.discontinued.value,
    StatusChoices.discharged.value,
]


class ClassChoices(str, Enum):
    imp = "imp"
    amb = "amb"
    obsenc = "obsenc"
    emer = "emer"
    vr = "vr"
    hh = "hh"


class AdmitSourcesChoices(str, Enum):
    hosp_trans = "hosp-trans"
    emd = "emd"
    outp = "outp"
    born = "born"
    gp = "gp"
    mp = "mp"
    nursing = "nursing"
    psych = "psych"
    rehab = "rehab"
    other = "other"


class DischargeDispositionChoices(str, Enum):
    home = "home"
    alt_home = "alt-home"
    other_hcf = "other-hcf"
    hosp = "hosp"
    long = "long"
    aadvice = "aadvice"
    exp = "exp"
    psy = "psy"
    rehab = "rehab"
    snf = "snf"
    oth = "oth"


class DietPreferenceChoices(str, Enum):
    vegetarian = "vegetarian"
    diary_free = "diary-free"
    nut_free = "nut-free"
    gluten_free = "gluten-free"
    vegan = "vegan"
    halal = "halal"
    kosher = "kosher"
    none = "none"


class EncounterPriorityChoices(str, Enum):
    A = "ASAP"
    CR = "callback results"
    CS = "callback for scheduling"
    EL = "elective"
    EM = "emergency"
    P = "preop"
    PRN = "as needed"
    R = "routine"
    RR = "rush reporting"
    S = "stat"
    T = "timing critical"
    UD = "use as directed"
    UR = "urgent"
