from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.organziation import Organization, OrganizationUser
from care.emr.resources.organization.organization_user_spec import (
    OrganizationUserReadSpec,
    OrganizationUserWriteSpec, OrganizationUserUpdateSpec,
)
from care.emr.resources.organization.spec import (
    OrganizationReadSpec,
    OrganizationWriteSpec,
)
from care.security.models import RoleModel


class OrganizationFilter(filters.FilterSet):
    parent = filters.UUIDFilter(field_name="parent__external_id")
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    org_type = filters.CharFilter(field_name="org_type", lookup_expr="iexact")


class OrganizationViewSet(EMRModelViewSet):
    database_model = Organization
    pydantic_model = OrganizationWriteSpec
    pydantic_read_model = OrganizationReadSpec
    filterset_class = OrganizationFilter
    filter_backends = [filters.DjangoFilterBackend]

    def authorize_create(self, instance):
        """
        - Root Organizations can only be created by the superadmin
        - Organizations can only be created if the parent is accessible by the user
        - Organization creates require the Organization Create Permission
        - Certain types of Organizations like geo, user role etc.. can only be
            maintained by the superadmin
        - Deletes are not allowed if there are child organizations
        """
        if not instance.parent and not self.request.user.is_superuser:
            raise PermissionDenied(
                "Root Organizations can only be created by the superadmin"
            )

    def get_queryset(self):
        queryset = (
            super().get_queryset().select_related("parent", "created_by", "updated_by")
        )
        if "parent" in self.request.GET and not self.request.GET.get("parent"):
            queryset = queryset.filter(parent__isnull=True)
        return queryset

    @action(detail=False, methods=["GET"])
    def mine(self, request, *args, **kwargs):
        orgusers = OrganizationUser.objects.filter(user=request.user).select_related(
            "organization"
        )
        data = [
            self.get_read_pydantic_model().serialize(orguser.organization).to_json()
            for orguser in orgusers
        ]
        return Response({"count": len(data), "results": data})


class OrganizationUsersViewSet(EMRModelViewSet):
    database_model = OrganizationUser
    pydantic_model = OrganizationUserWriteSpec
    pydantic_read_model = OrganizationUserReadSpec
    pydantic_update_model = OrganizationUserUpdateSpec

    def get_organization_obj(self):
        return get_object_or_404(
            Organization, external_id=self.kwargs["organization_external_id"]
        )

    def perform_create(self, instance):
        instance.organization = self.get_organization_obj()

        super().perform_create(instance)

    def validate_data(self, instance, model_obj=None):
        if model_obj:
            return
        organization = self.get_organization_obj()
        if (
            OrganizationUser.objects.filter(
                Q(organization=organization)
                | Q(organization__root_org=organization.root_org)
            )
            .filter(user__external_id=instance.user)
            .exists()
        ):
            raise ValidationError("User association already exists")

    def authorize_create(self, instance):
        """
        - Creates are only allowed if the user is part of the organization
        - The role applied to the new user must be equal or lower in privilege to the user created
        - Maintain a permission to add users to an organization
        """
        if self.request.user.is_superuser:
            return
        organization = self.get_organization_obj()
        organization_parents = [*organization.parent_cache, organization.id]
        if not OrganizationUser.objects.filter(
            organization__in=organization_parents, user=self.request.user
        ).exists():
            raise PermissionDenied("User does not have access to organization")
        user_roles = RoleModel.objects.filter(
            id__in=OrganizationUser.objects.filter(
                organization_id__in=organization_parents, user=self.request.user
            ).values("role_id")
        )
        merged_permissions = set()
        for role in user_roles:
            merged_permissions = merged_permissions.union(
                set(role.get_permission_sk_for_role())
            )
        requested_role = RoleModel.objects.filter(external_id=instance.role).first()
        if not requested_role:
            raise Exception("Role does not exist")
        requested_role = set(requested_role.get_permission_sk_for_role())
        # Confirm if requested role's permission are the subset of the users roles
        if not requested_role.issubset(merged_permissions):
            raise PermissionDenied(
                "User does not have the required permissions to assign the role"
            )

        ## Check for duplicates

    def get_queryset(self):
        """
        Only users part of the organization can access its users
        """
        organization = self.get_organization_obj()
        organization_parents = [*organization.parent_cache, organization.id]
        if (
            not self.request.user.is_superuser
            and not OrganizationUser.objects.filter(
                organization_id__in=organization_parents, user=self.request.user
            ).exists()
        ):
            raise PermissionDenied("User does not have access to organization")
        return OrganizationUser.objects.filter(organization=organization)
