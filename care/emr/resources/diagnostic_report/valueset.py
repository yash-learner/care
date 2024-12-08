from care.emr.fhir.schema.valueset.valueset import ValueSetCompose, ValueSetInclude
from care.emr.registries.care_valueset.care_valueset import CareValueset
from care.emr.resources.valueset.spec import ValueSetStatusOptions

CARE_DIAGNOSTIC_REPORT_CATEGORY_VALUESET = CareValueset(
    "Diagnostic Report Category",
    "system-diagnostic-report-category",
    ValueSetStatusOptions.active,
)

CARE_DIAGNOSTIC_REPORT_CATEGORY_VALUESET.register_valueset(
    ValueSetCompose(
        include=[
            ValueSetInclude(
                system="http://terminology.hl7.org/CodeSystem/v2-0074",
            )
        ]
    )
)

CARE_DIAGNOSTIC_REPORT_CATEGORY_VALUESET.register_as_system()

CARE_DIAGNOSTIC_REPORT_CODE_VALUESET = CareValueset(
    "Diagnostic Report Code",
    "system-diagnostic-report-code",
    ValueSetStatusOptions.active,
)

CARE_DIAGNOSTIC_REPORT_CODE_VALUESET.register_valueset(
    ValueSetCompose(
        include=[
            ValueSetInclude(
                system="http://loinc.org",
            )
        ]
    )
)

CARE_DIAGNOSTIC_REPORT_CODE_VALUESET.register_as_system()
