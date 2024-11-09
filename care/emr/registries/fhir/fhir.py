class FHIRRegistry:
    """
    Register an FHIR Resource
    Models inherited from the FHIR Resource base class can be registered here
    The registry is used to power FHIR endpoints for resources
    """

    _registry = {}

    @classmethod
    def _register(cls, resource_class) -> None:
        cls._registry[resource_class.resource_type] = resource_class

    @classmethod
    def register(cls):
        def inner_wrapper(wrapped_class):
            cls._register(wrapped_class)
            return wrapped_class

        return inner_wrapper

    @classmethod
    def get_resources(cls):
        return cls._registry
