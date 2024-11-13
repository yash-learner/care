# ruff : noqa : T201 F841

from django.core.management.base import BaseCommand
from rest_framework.viewsets import ModelViewSet

from care.emr.fhir.resources.care_valueset import DISEASE_VALUESET
from care.emr.fhir.resources.code_concept import CodeConceptResource
from care.emr.fhir.resources.code_system import CodeSystemResource
from care.emr.fhir.resources.valueset import ValueSetResource

ModelViewSet

class Command(BaseCommand):
    """ """

    help = ""

    def handle(self, *args, **options):
        code_system = CodeSystemResource().filter(url="http://loinc.org").get()
        code_concept = (
            CodeConceptResource().filter(system=code_system.url, code="8302-2").get()
        )
        valueset = (
            ValueSetResource()
            .filter(
                search="Pressure",
                count=2,
                include=[{"system": code_system.url, "filter": []}],
            )
            .search()
        )
        print(DISEASE_VALUESET.composition)
        for i in DISEASE_VALUESET.search("Blood"):
            print(i)
