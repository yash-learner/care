import datetime
import uuid
from enum import Enum
from types import UnionType

from pydantic import BaseModel

from care.emr.fhir.schema.base import CodeableConcept


class FHIRResource(BaseModel):
    __model__ = None
    __exclude__ = []

    meta: dict = {}
    __questionnaire_cache__ = {}

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
        dump = self.model_dump(exclude_defaults=True)
        for field in dump:
            if field in database_fields and field not in self.__exclude__:
                obj.__setattr__(field, dump[field])
            elif field not in self.__exclude__:
                meta[field] = dump[field]
        obj.meta = meta
        self.perform_extra_deserialization(is_update, obj)
        return obj

    @classmethod
    def questionnaire(cls):
        if cls.__questionnaire_cache__:
            return cls.__questionnaire_cache__
        questionnire_obj = []
        for field in cls.model_fields:
            field_class = cls.model_fields[field]
            field_obj = {"linkId": field}
            if type(field_class.annotation) is UnionType:
                continue
            if issubclass(field_class.annotation, Enum):
                field_obj["type"] = "string"
                field_obj["answerOption"] = [
                    {x.name: x.value} for x in field_class.annotation
                ]
            elif issubclass(field_class.annotation, datetime.datetime):
                field_obj["type"] = "dateTime"
            elif issubclass(field_class.annotation, str):
                field_obj["type"] = "string"
            elif issubclass(field_class.annotation, int):
                field_obj["type"] = "integer"
            elif issubclass(field_class.annotation, uuid.UUID):
                field_obj["type"] = "string"
            elif field_class.annotation is CodeableConcept:
                field_obj["type"] = "coding"
                field_obj["valueset"] = {"slug": field_class.json_schema_extra["slug"]}
            elif issubclass(field_class.annotation, FHIRResource):
                field_obj["type"] = "group"
                field_obj["questions"] = field_class.annotation.questionnaire()
            questionnire_obj.append(field_obj)
        cls.__questionnaire_cache__ = questionnire_obj
        return questionnire_obj
