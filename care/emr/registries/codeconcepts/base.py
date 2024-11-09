class CodeConcept:
    """
    This class represents a code-able concept in care.
    Different Systems can register themselves for a code-able concept.
    Care maintains a unique URI for all code-able concepts within care.
    """

    CODE = "ohc/care/concept/code"
    PROVIDERS = []

    @classmethod
    def register_provider(cls, provider):
        cls.PROVIDERS.append(provider)


class CodeConceptSystem:
    CODE = ""


class CodeConceptProvider:
    CONCEPT: CodeConcept = None
    SYSTEM: CodeConceptSystem = None
    CODE = None

    BOUNDED: bool = None

    @classmethod
    def concepts(cls):
        return []
