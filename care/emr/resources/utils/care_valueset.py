from care.emr.fhir.resources.valueset import ValueSetResource
from care.emr.fhir.schema.valueset.valueset import (
    ValueSet,
    ValueSetCompose,
    ValueSetInclude,
)
from care.emr.resources.valueset.spec import ValueSetStatusOptions


class CareValueset:
    """
    Care Valueset is a pre-system defined valueset which can be enhanced by plugs
    Eg, A Disease valueset can be system created and used for all system related API's
    This valueset will be initially empty, but plugs can register their values into this valueset
    as they are added. This allows for a pluggable valueset concept

    Valuesets are written to the database using a management command, they can be reset based on this as well.
    These valuesets can then be edited to the admins requirements
    """

    name = None
    status = None

    def __init__(self, name, status):
        self.name = name
        self.status = status
        self.composition = ValueSetCompose(include=[], exclude=[])

    def register_as_system(self):
        SystemValueset.add_system_valueset(self)

    def register_valueset(self, composition: ValueSetCompose):
        """
        Register a valueset to the system
        """
        if composition.include:
            for include in composition.include:
                self.composition.include.append(include)
        if composition.exclude:
            for exclude in composition.exclude:
                self.composition.exclude.append(exclude)

    @property
    def valueset(self):
        return ValueSet(name=self.name, status=self.status, compose=self.composition)

    def search(self, search=""):
        # Create a composition with the same system
        # Query each system
        # Combine and return
        systems = {}
        for include in self.composition.include:
            system = include.system.root
            if system not in systems:
                systems[system] = {"include": []}
            systems[system]["include"].append(include.model_dump(exclude_defaults=True))
        for exclude in self.composition.exclude:
            system = exclude.system.root
            if system not in systems:
                systems[system] = {"exclude": []}
            systems[system]["exclude"].append(exclude.model_dump(exclude_defaults=True))

        results = []

        for system in systems:
            results.extend(
                ValueSetResource()
                .filter(search=search, count=10, **systems[system])
                .search()
            )
        return results


class SystemValueset:
    _valuesets = []

    @classmethod
    def add_system_valueset(cls, valueset: CareValueset):
        cls._valuesets.append(valueset)

    @classmethod
    def get_all_valuesets(cls):
        return cls._valuesets


DISEASE_VALUESET = CareValueset("Disease", ValueSetStatusOptions.active.value)
DISEASE_VALUESET.register_as_system()

DISEASE_VALUESET.register_valueset(
    ValueSetCompose(
        include=[
            ValueSetInclude(
                system="http://snomed.info/sct",
                filter=[{"property": "concept", "op": "is-a", "value": "105590001"}],
            )
        ]
    )
)
DISEASE_VALUESET.register_valueset(
    ValueSetCompose(include=[ValueSetInclude(system="http://loinc.org", filter=[])])
)
