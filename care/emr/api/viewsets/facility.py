from django.db.models import Q
from django.utils.decorators import method_decorator
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.organziation import FacilityOrganizationUser, OrganizationUser
from care.emr.resources.facility.spec import FacilityCreateSpec, FacilityReadSpec
from care.facility.api.serializers.facility import FacilityImageUploadSerializer
from care.facility.models import Facility
from care.utils.file_uploads.cover_image import delete_cover_image


class FacilityViewSet(EMRModelViewSet):
    database_model = Facility
    pydantic_model = FacilityCreateSpec
    pydantic_read_model = FacilityReadSpec

    def get_queryset(self):
        # TODO Add Permission checks
        organization_ids = list(
            OrganizationUser.objects.filter(user=self.request.user).values_list(
                "organization_id", flat=True
            )
        )
        return (
            super()
            .get_queryset()
            .filter(
                Q(
                    id__in=FacilityOrganizationUser.objects.filter(
                        user=self.request.user
                    ).values_list("organization__facility_id")
                )
                | Q(geo_organization_cache__overlap=organization_ids)
            )
        )

    @method_decorator(parser_classes([MultiPartParser]))
    @action(methods=["POST"], detail=True)
    def cover_image(self, request, external_id):
        facility = self.get_object()
        serializer = FacilityImageUploadSerializer(facility, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @cover_image.mapping.delete
    def cover_image_delete(self, *args, **kwargs):
        facility = self.get_object()
        delete_cover_image(facility.cover_image_url, "cover_images")
        facility.cover_image_url = None
        facility.save()
        return Response(status=204)
