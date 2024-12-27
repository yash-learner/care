from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.settings import api_settings

from care.emr.api.viewsets.base import EMRModelViewSet
from care.emr.models.organziation import Organization, OrganizationUser
from care.emr.resources.organization.organization_user_spec import (
    OrganizationUserReadSpec,
    OrganizationUserUpdateSpec,
    OrganizationUserWriteSpec,
)
from care.emr.resources.organization.spec import (
    OrganizationReadSpec,
    OrganizationTypeChoices,
    OrganizationUpdateSpec,
    OrganizationWriteSpec,
)
from care.security.authorization import AuthorizationController
from care.security.models import PermissionModel, RoleModel, RolePermission
from config.patient_otp_authentication import JWTTokenPatientAuthentication


class OrganizationFilter(filters.FilterSet):
    parent = filters.UUIDFilter(field_name="parent__external_id")
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    org_type = filters.CharFilter(field_name="org_type", lookup_expr="iexact")


class OrganizationViewSet(EMRModelViewSet):
    database_model = Organization
    pydantic_model = OrganizationWriteSpec
    pydantic_read_model = OrganizationReadSpec
    pydantic_update_model = OrganizationUpdateSpec
    filterset_class = OrganizationFilter
    filter_backends = [filters.DjangoFilterBackend]
    authentication_classes = [
        JWTTokenPatientAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]

    def permissions_controller(self, request):
        if self.action in ["list", "retrieve"]:
            # All users including otp users can view the list of organizations
            return True
        if getattr(request.user, "is_alternative_login", False):
            # Deny all other permissions in OTP mode
            return False
        return request.user.is_authenticated

    def authorize_update(self, request_obj, model_instance):
        if not AuthorizationController.call(
            "can_manage_organization_obj", self.request.user, model_instance
        ):
            raise PermissionDenied(
                "User does not have the required permissions to update organizations"
            )

    def authorize_create(self, instance):
        if self.request.user.is_superuser:
            return True
        # Root Organizations can only be created by the superadmin
        if not instance.parent:
            raise PermissionDenied(
                "Root Organizations can only be created by the superadmin"
            )
        # Some types of organization cannot be created by regular users
        if instance.org_type in [
            OrganizationTypeChoices.govt.value,
            OrganizationTypeChoices.role.value,
        ]:
            raise PermissionDenied("Organization Type cannot be created")
        # Organizations can only be created if the parent is accessible by the user
        # Organization creates require the Organization Create Permission

        parent = get_object_or_404(Organization, external_id=instance.parent)

        if not AuthorizationController.call(
            "can_create_organization_obj", self.request.user, parent
        ):
            raise PermissionDenied(
                "User does not have the required permissions to create organizations"
            )
        # TODO Deletes are not allowed if there are child organizations
        return True

    def get_queryset(self):
        queryset = (
            super().get_queryset().select_related("parent", "created_by", "updated_by")
        )
        if "parent" in self.request.GET and not self.request.GET.get("parent"):
            queryset = queryset.filter(parent__isnull=True)
        if "permission" in self.request.GET and (
            not self.request.user.is_superuser
            or not getattr(self.request.user, "is_alternative_login", False)
        ):
            permission = get_object_or_404(
                PermissionModel, slug=self.request.GET.get("permission")
            )
            roles = RolePermission.objects.filter(permission=permission).values_list(
                "role_id", flat=True
            )
            queryset = queryset.filter(
                id__in=OrganizationUser.objects.filter(
                    user=self.request.user, role_id__in=roles
                ).values_list("organization_id", flat=True)
            )
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

    def authorize_update(self, request_obj, model_instance):
        # TODO : This logic is flawed, the users current permissions needs to be checks to understand
        #        if the user is capable of the edit, lower permission person should not move high permission user lower
        self.authorize_create(request_obj)

    # TODO Deletes needs to be authorized, we cannot delete a user higher in prvilage than the user

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
        AuthorizationController.call(
            "can_manage_organization_users_obj", self.request.user, organization
        )
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
        if not AuthorizationController.call(
            "can_list_organization_users_obj", self.request.user, organization
        ):
            raise PermissionDenied(
                "User does not have the required permissions to list users"
            )
        return OrganizationUser.objects.filter(organization=organization)
