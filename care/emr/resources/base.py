from pydantic import BaseModel


class FHIRResource(BaseModel):
    __model__ = None
    __exclude__ = []

    meta: dict = {}

    @classmethod
    def get_database_mapping(cls):
        """
        Mapping of database fields to pydantic object
        """
        database_fields = []
        for field in cls.__model__._meta.fields:  # noqa SLF001
            database_fields.append(field.name)
        return database_fields

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id

    @classmethod
    def serialize(cls, obj: __model__):
        """
        Creates a pydantic object from a database object
        """
        mappings = cls.get_database_mapping()
        constructed = {}
        for mapping in mappings:
            if mapping in cls.model_fields and mapping not in cls.__exclude__:
                constructed[mapping] = getattr(obj, mapping)
        for field in obj.meta:
            if field in cls.model_fields:
                constructed[field] = obj.meta[field]
        cls.perform_extra_serialization(constructed, obj)
        return cls(**constructed)

    def perform_extra_deserialization(self, is_update, obj):
        pass

    def de_serialize(self, obj=None):
        """
        Creates a database object from a pydantic object
        """
        is_update = True
        if not obj:
            is_update = False
            obj = self.__model__()
        database_fields = self.get_database_mapping()
        meta = {}
        for field in self.model_dump():
            if field in database_fields and field not in self.__exclude__:
                obj.__setattr__(field, self.__getattribute__(field))
            elif field not in self.__exclude__:
                meta[field] = self.__getattribute__(field)
        obj.meta = meta
        self.perform_extra_deserialization(is_update, obj)
        return obj
