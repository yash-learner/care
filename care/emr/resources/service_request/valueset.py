from care.emr.fhir.schema.valueset.valueset import ValueSetCompose, ValueSetInclude
from care.emr.resources.care_valueset.care_valueset import CareValueset
from care.emr.resources.valueset.spec import ValueSetStatusOptions

CARE_LAB_ORDER_CODE_VALUESET = CareValueset(
    "Lab Order", "system-lab-order-code", ValueSetStatusOptions.active
)

CARE_LAB_ORDER_CODE_VALUESET.register_valueset(
    ValueSetCompose(
        include=[
            ValueSetInclude(
                system="http://loinc.org",
                filter=[{"property": "ancestor", "op": "is-a", "value": "LP29693-6"}],
            )
        ]
    )
)

CARE_LAB_ORDER_CODE_VALUESET.register_as_system()

CARE_SERVICE_REQUEST_CATEGORY_VALUESET = CareValueset(
    "Service Request Category",
    "system-service-request-category",
    ValueSetStatusOptions.active,
)

CARE_SERVICE_REQUEST_CATEGORY_VALUESET.register_valueset(
    ValueSetCompose(
        include=[
            ValueSetInclude(
                system="http://snomed.info/sct",
                concept=[
                    {"code": "108252007", "display": "Laboratory procedure"},
                    {"code": "363679005", "display": "Imaging"},
                    {"code": "409063005", "display": "Counselling"},
                    {"code": "409073007", "display": "Education"},
                    {"code": "387713003", "display": "Surgical procedure"},
                ],
            )
        ]
    )
)

CARE_SERVICE_REQUEST_CATEGORY_VALUESET.register_as_system()

CARE_MEDICATION_AS_NEEDED_REASON_VALUESET = CareValueset(
    "Medication As Needed Reason",
    "system-medication-as-needed-reason",
    ValueSetStatusOptions.active,
)

CARE_MEDICATION_AS_NEEDED_REASON_VALUESET.register_valueset(
    ValueSetCompose(
        include=[
            ValueSetInclude(
                system="http://snomed.info/sct",
                filter=[{"property": "concept", "op": "is-a", "value": "404684003"}],
            )
        ]
    )
)

CARE_MEDICATION_AS_NEEDED_REASON_VALUESET.register_as_system()
