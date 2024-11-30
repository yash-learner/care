from care.emr.fhir.schema.valueset.valueset import ValueSetCompose, ValueSetInclude
from care.emr.resources.care_valueset.care_valueset import CareValueset
from care.emr.resources.valueset.spec import ValueSetStatusOptions

CARE_SPECIMEN_TYPE_VALUESET = CareValueset(
    "Specimen Type", "system-specimen-type", ValueSetStatusOptions.active
)  # https://nrces.in/ndhm/fhir/r4/ValueSet/ndhm-specimen-types

CARE_SPECIMEN_TYPE_VALUESET.register_valueset(
    ValueSetCompose(
        include=[
            ValueSetInclude(
                system="http://snomed.info/sct",
                filter=[{"property": "concept", "op": "is-a", "value": "123038009"}],
            )
        ]
    )
)

CARE_SPECIMEN_TYPE_VALUESET.register_as_system()

CARE_SPECIMEN_PROCESSING_METHOD_VALUESET = CareValueset(
    "Specimen Processing Method",
    "system-specimen-processing-method",
    ValueSetStatusOptions.active,
)

CARE_SPECIMEN_PROCESSING_METHOD_VALUESET.register_valueset(
    ValueSetCompose(
        include=[
            ValueSetInclude(
                system="http://snomed.info/sct",
                filter=[{"property": "concept", "op": "is-a", "value": "9265001"}],
            )
        ]
    )
)

CARE_SPECIMEN_PROCESSING_METHOD_VALUESET.register_as_system()
