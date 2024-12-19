from care.emr.resources.base import EMRResource
from care.users.models import User


class UserSpec(EMRResource):
    __model__ = User
    id: str
    first_name: str
    username: str
    email: str
    last_name: str
    user_type: str
    last_login: str
    read_profile_picture_url: str

    @classmethod
    def perform_extra_serialization(cls, mapping, obj : User):
        mapping["user_type"] = User.REVERSE_MAPPING[obj.user_type]
        mapping["id"] = str(obj.external_id)
        mapping["profile_picture_url"] = obj.read_profile_picture_url()
