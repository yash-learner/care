from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.organziation import FacilityOrganization, FacilityOrganizationUser
from care.emr.resources.facility_organization.facility_orgnization_user_spec import (
    FacilityOrganizationUserReadSpec,
    FacilityOrganizationUserUpdateSpec,
    FacilityOrganizationUserWriteSpec,
)
from care.emr.resources.facility_organization.spec import (
    FacilityOrganizationReadSpec,
    FacilityOrganizationWriteSpec,
)
from care.facility.models import Facility
from care.security.authorization import AuthorizationController


class FacilityOrganizationFilter(filters.FilterSet):
    parent = filters.UUIDFilter(field_name="parent__external_id")
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    org_type = filters.CharFilter(field_name="org_type", lookup_expr="iexact")


class FacilityOrganizationViewSet(EMRModelViewSet):
    database_model = FacilityOrganization
    pydantic_model = FacilityOrganizationWriteSpec
    pydantic_read_model = FacilityOrganizationReadSpec
    filterset_class = FacilityOrganizationFilter
    filter_backends = [filters.DjangoFilterBackend]

    def clean_create_data(self, request_data):
        request_data["facility"] = self.kwargs["facility_external_id"]
        return request_data

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(facility__external_id=self.kwargs["facility_external_id"])
            .select_related("facility", "parent", "created_by", "updated_by")
        )


class FacilityOrganizationUsersViewSet(EMRModelViewSet):
    database_model = FacilityOrganizationUser
    pydantic_model = FacilityOrganizationUserWriteSpec
    pydantic_read_model = FacilityOrganizationUserReadSpec
    pydantic_update_model = FacilityOrganizationUserUpdateSpec

    def get_organization_obj(self):
        import logging

        logging.info(self.kwargs)
        return get_object_or_404(
            FacilityOrganization,
            external_id=self.kwargs["facility_organizations_external_id"],
        )

    def get_facility_obj(self):
        return get_object_or_404(
            Facility, external_id=self.kwargs["facility_external_id"]
        )

    def perform_create(self, instance):
        instance.organization = self.get_organization_obj()
        instance.facility = self.get_facility_obj()
        super().perform_create(instance)

    def authorize_delete(self, instance):
        if instance.org_type == "root":
            raise PermissionDenied("Cannot delete root organization")

    def validate_data(self, instance, model_obj=None):
        if model_obj:
            return
        organization = self.get_organization_obj()
        if (
            FacilityOrganizationUser.objects.filter(
                Q(organization=organization)
                | Q(organization__root_org=organization.root_org)
            )
            .filter(user__external_id=instance.user)
            .exists()
        ):
            raise ValidationError("User association already exists")

    # TODO Add AuthZ, abstract based on organization users, cleanup required.

    def get_queryset(self):
        """
        Only users part of the organization can access its users
        """
        organization = self.get_organization_obj()
        if not AuthorizationController.call(
            "can_list_facility_organization_users_obj", self.request.user, organization
        ):
            raise PermissionDenied(
                "User does not have the required permissions to list users"
            )
        return FacilityOrganizationUser.objects.filter(organization=organization)
