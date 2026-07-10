from django.urls import reverse
from django.utils import timezone

from care.emr.models.invoice import Invoice
from care.fixtures.constants import build_price_components


class BillingFixturesMixin:
    """Billing fixture helpers for ``CareFixtureBase``.

    Mixed into ``CareFixtureBase``; relies on ``self.post`` / ``self.patch`` /
    ``self.get`` / ``self.fake`` provided by the base class.
    """

    def create_account(self, facility_id, patient_id, **kwargs):
        url = reverse("account-list", kwargs={"facility_external_id": facility_id})
        data = {
            "status": "active",
            "billing_status": "open",
            "name": f"Account {self.fake.last_name()}",
            "service_period": {"start": timezone.now().isoformat()},
            "patient": patient_id,
            **kwargs,
        }
        return self.post(url, data)

    def create_charge_item(
        self,
        facility_id,
        account_id,
        patient_id,
        title,
        quantity=1,
        base_amount=500,
        **kwargs,
    ):
        url = reverse("charge_item-list", kwargs={"facility_external_id": facility_id})
        data = {
            "title": title,
            "status": "billable",
            "quantity": quantity,
            "unit_price_components": build_price_components(base_amount),
            "account": account_id,
            "patient": patient_id,
            **kwargs,
        }
        return self.post(url, data)

    def create_invoice(
        self, facility_id, account_id, charge_items, created_date=None, **kwargs
    ):
        url = reverse("invoice-list", kwargs={"facility_external_id": facility_id})
        data = {
            "status": "draft",
            "account": account_id,
            "charge_items": charge_items,
            **kwargs,
        }
        invoice = self.post(url, data)
        # The API stamps created_date to now; backdate via ORM so the invoice
        # list date-range filter has data spread across known dates.
        if created_date is not None:
            Invoice.objects.filter(external_id=invoice.id).update(
                created_date=created_date
            )
        return invoice

    def update_account(self, facility_id, account, **kwargs):
        url = reverse(
            "account-detail",
            kwargs={"facility_external_id": facility_id, "external_id": account.id},
        )
        data = {
            "status": account.status,
            "billing_status": account.billing_status,
            "name": account.name,
            "service_period": account.service_period,
            **kwargs,
        }
        return self.patch(url, data)

    def issue_invoice(self, facility_id, invoice, issue_date=None):
        url = reverse(
            "invoice-detail",
            kwargs={"facility_external_id": facility_id, "external_id": invoice.id},
        )
        data = {"status": "issued"}
        if issue_date is not None:
            data["issue_date"] = issue_date
        return self.patch(url, data)

    def balance_invoice(self, facility_id, invoice):
        url = reverse(
            "invoice-detail",
            kwargs={"facility_external_id": facility_id, "external_id": invoice.id},
        )
        return self.patch(url, {"status": "balanced"})

    def cancel_invoice(self, facility_id, invoice, reason="cancelled"):
        url = reverse(
            "invoice-cancel-invoice",
            kwargs={"facility_external_id": facility_id, "external_id": invoice.id},
        )
        return self.post(url, {"reason": reason})

    def create_payment_reconciliation(
        self,
        facility_id,
        account_id,
        tendered_amount,
        returned_amount=0,
        target_invoice=None,
        **kwargs,
    ):
        url = reverse(
            "payment_reconciliation-list",
            kwargs={"facility_external_id": facility_id},
        )
        data = {
            "reconciliation_type": "payment",
            "status": "active",
            "kind": "deposit",
            "issuer_type": "patient",
            "outcome": "complete",
            "method": "cash",
            "account": account_id,
            "target_invoice": target_invoice,
            "tendered_amount": tendered_amount,
            "returned_amount": returned_amount,
            **kwargs,
        }
        return self.post(url, data)

    def set_invoice_expression(self, facility_id, expression):
        url = reverse(
            "facility-set-invoice-expression", kwargs={"external_id": facility_id}
        )
        return self.post(url, {"invoice_number_expression": expression})

    def apply_charge_item_defs(self, facility_id, requests):
        url = reverse(
            "charge_item-apply-charge-item-defs",
            kwargs={"facility_external_id": facility_id},
        )
        return self.post(url, {"requests": requests})

    def list_charge_items(self, facility_id, account_id, status="billable"):
        url = reverse("charge_item-list", kwargs={"facility_external_id": facility_id})
        response = self.get(url, params={"account": account_id, "status": status})
        return response.get("results", [])
