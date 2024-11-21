from care.emr.resources.care_valueset.care_valueset import CareValueset
from care.emr.resources.valueset.spec import ValueSetStatusOptions

CARE_OBSERVATION_VALUSET = CareValueset(
    "Observation", "system-observation", ValueSetStatusOptions.active.value
)

CARE_OBSERVATION_VALUSET.register_as_system()
