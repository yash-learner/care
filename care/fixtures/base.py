from faker import Faker

from care.fixtures.helpers.billing import BillingFixturesMixin
from care.fixtures.helpers.core import CoreFixturesMixin
from care.fixtures.helpers.inventory import InventoryFixturesMixin
from care.fixtures.helpers.lab import LabFixturesMixin
from care.fixtures.helpers.managing_org import ManagingOrgFixturesMixin
from care.fixtures.helpers.reports import ReportFixturesMixin
from care.fixtures.helpers.request import RequestMixin
from care.fixtures.helpers.scheduling import SchedulingFixturesMixin


class CareFixtureBase(
    RequestMixin,
    CoreFixturesMixin,
    LabFixturesMixin,
    InventoryFixturesMixin,
    BillingFixturesMixin,
    SchedulingFixturesMixin,
    ManagingOrgFixturesMixin,
    ReportFixturesMixin,
):
    """Helper class to create fixtures through the API.

    Assembles the per-domain fixture mixins in ``care/fixtures/helpers/``.
    Provides the shared ``client`` / ``user`` / ``fake`` that every mixin
    relies on (``self.post`` / ``self.get`` / ``self.patch`` come from
    ``RequestMixin``).

    Inspired by CareAPITestBase (We should merge these in future).
    """

    fake = Faker("en_IN")

    def __init__(self, client):
        self.client = client
        self.user = None
