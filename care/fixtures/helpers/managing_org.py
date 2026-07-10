from django.urls import reverse


class ManagingOrgFixturesMixin:
    """Managing organization links and role assignments."""

    def link_managing_org(self, role_org_id, managing_org_id):
        url = reverse(
            "organization-managing-organization",
            kwargs={"external_id": role_org_id},
        )
        return self.post(url, {"organization": managing_org_id, "action": "add"})

    def assign_org_role(self, org_id, user_id, role_id):
        url = reverse(
            "organization-users-list",
            kwargs={"organization_external_id": org_id},
        )
        return self.post(url, {"user": user_id, "role": role_id})

    def get_role_org_roles(self):
        data = self.get(reverse("role-list"), params={"context": "ROLE_ORG"})
        results = data.get("results", data)
        return {r.name: r for r in results}

    def get_user(self, username):
        return self.get(reverse("users-detail", kwargs={"username": username}))
