from django.urls import reverse

from care.fixtures.helpers.utils import slugify


class InventoryFixturesMixin:
    """Product knowledge, products, request/delivery orders, supply
    requests/deliveries, inventory items, and the composite
    ``create_facility_product``."""

    def create_product_knowledge(self, name, base_unit, facility=None, **kwargs):
        data = {
            "status": "active",
            "product_type": "medication",
            "name": name,
            "base_unit": base_unit,
            "slug_value": slugify(name),
            **kwargs,
        }
        if facility:
            data["facility"] = facility
        return self.post(reverse("product_knowledge-list"), data)

    def create_product(self, facility_id, product_knowledge_slug, **kwargs):
        url = reverse("product-list", kwargs={"facility_external_id": facility_id})
        data = {
            "status": "active",
            "product_knowledge": product_knowledge_slug,
            "extensions": {},
            **kwargs,
        }
        return self.post(url, data)

    def create_request_order(self, facility_id, name, destination, **kwargs):
        url = reverse(
            "request-order-list", kwargs={"facility_external_id": facility_id}
        )
        data = {
            "status": "pending",
            "name": name,
            "destination": destination,
            "intent": "order",
            "category": "central",
            "priority": "routine",
            "reason": "ward_stock",
            **kwargs,
        }
        return self.post(url, data)

    def create_supply_request(self, order, item, quantity, **kwargs):
        data = {
            "status": "active",
            "order": order,
            "item": item,
            "quantity": quantity,
            **kwargs,
        }
        return self.post(reverse("supply_request-list"), data)

    def create_delivery_order(self, facility_id, name, destination, **kwargs):
        url = reverse(
            "delivery-order-list", kwargs={"facility_external_id": facility_id}
        )
        data = {
            "status": "pending",
            "name": name,
            "destination": destination,
            "extensions": {},
            **kwargs,
        }
        return self.post(url, data)

    def create_supply_delivery(self, order, supplied_item_quantity, **kwargs):
        data = {
            "status": "in_progress",
            "order": order,
            "supplied_item_quantity": supplied_item_quantity,
            "extensions": {},
            **kwargs,
        }
        return self.post(reverse("supply_delivery-list"), data)

    def update_supply_delivery(self, delivery_id, **kwargs):
        url = reverse("supply_delivery-detail", kwargs={"external_id": delivery_id})
        return self.patch(url, kwargs)

    def list_inventory_items(self, facility_id, location_id, **params):
        url = reverse(
            "inventory-item-list",
            kwargs={
                "facility_external_id": facility_id,
                "location_external_id": location_id,
            },
        )
        return self.get(url, params=params).get("results", [])

    def create_facility_product(self, facility_id, item, category_slugs):
        """Create a Product (with its ProductKnowledge + ChargeItemDefinition)."""

        product_knowledge = self.create_product_knowledge(
            category=category_slugs["product_knowledge"], **item["product_knowledge"]
        )
        charge_item_definition = self.create_charge_item_definition(
            facility_id,
            category=category_slugs["charge_item_definition"],
            **item["charge_item_definition"],
        )
        product = self.create_product(
            facility_id,
            product_knowledge_slug=product_knowledge.slug,
            charge_item_definition=charge_item_definition.slug,
            **item.get("product_extras", {}),
        )
        return product, product_knowledge
