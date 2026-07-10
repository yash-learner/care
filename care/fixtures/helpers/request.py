from rest_framework import status as http_status

from care.fixtures.helpers.utils import FixtureError, to_attr_dict


class RequestMixin:
    """HTTP verbs over the DRF ``APIClient``.

    ``self.client`` is provided by ``CareFixtureBase``. Every other fixture
    mixin builds request payloads and calls ``self.post`` / ``self.patch`` /
    ``self.get`` from here.
    """

    def post(self, url, data):
        response = self.client.post(url, data, format="json")
        if response.status_code not in (
            http_status.HTTP_200_OK,
            http_status.HTTP_201_CREATED,
        ):
            msg = f"POST {url} failed ({response.status_code}): {response.data}"
            raise FixtureError(msg)
        return to_attr_dict(response.data)

    def patch(self, url, data):
        response = self.client.patch(url, data, format="json")
        if response.status_code not in (
            http_status.HTTP_200_OK,
            http_status.HTTP_201_CREATED,
        ):
            msg = f"PATCH {url} failed ({response.status_code}): {response.data}"
            raise FixtureError(msg)
        return to_attr_dict(response.data)

    def get(self, url, params=None):
        response = self.client.get(url, params or {}, format="json")
        if response.status_code != http_status.HTTP_200_OK:
            msg = f"GET {url} failed ({response.status_code}): {response.data}"
            raise FixtureError(msg)
        return to_attr_dict(response.data)
