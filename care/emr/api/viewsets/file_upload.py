from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models import FileUpload
from care.emr.resources.file_upload.spec import (
    FileUploadCreateSpec,
    FileUploadRetrieveSpec,
    FileUploadUpdateSpec,
)


def file_authorizer(file_type, associating_id, permission):
    return


class FileUploadViewSet(EMRModelViewSet):
    database_model = FileUpload
    pydantic_model = FileUploadCreateSpec
    pydantic_retrieve_model = FileUploadRetrieveSpec
    pydantic_update_model = FileUploadUpdateSpec

    def authorize_create(self, instance):
        pass

    def get_queryset(self):
        if self.action == "list":
            if (
                "file_type" not in self.request.GET
                and "associating_id" not in self.request.GET
            ):
                raise PermissionError("Cannot filter files")
            file_authorizer(
                self.request.GET.get("file_type"),
                self.request.GET.get("associating_id"),
                "read",
            )
            return (
                super()
                .get_queryset()
                .filter(
                    file_type=self.request.GET.get("file_type"),
                    associating_id=self.request.GET.get("associating_id"),
                )
            )
        obj = get_object_or_404(FileUpload, external_id=self.kwargs["external_id"])
        file_authorizer(obj.file_type, obj.associating_id, "read")
        return super().get_queryset()
