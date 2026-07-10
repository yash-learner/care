from care.emr.resources.location.spec import (
    FacilityLocationFormChoices,
    FacilityLocationModeChoices,
)
from care.fixtures.constants import INVENTORY_ITEMS, HealthcareServiceInternalType


def load_inventory(base, facility_id, departments, suppliers, transfer_destination):
    pharmacy = departments["Pharmacy"]

    pharmacy_location = base.create_location(
        facility_id,
        name="Pharmacy",
        form=FacilityLocationFormChoices.ro.value,
        mode=FacilityLocationModeChoices.kind.value,
        organizations=[pharmacy.id],
    )

    base.create_healthcare_service(
        facility_id,
        name="Main Pharmacy",
        internal_type=HealthcareServiceInternalType.pharmacy.value,
        styling_metadata={},
        locations=[pharmacy_location.id],
    )

    category_names = {item["category"] for item in INVENTORY_ITEMS}
    categories = {}
    for category_name in category_names:
        categories[category_name] = {
            "product_knowledge": base.create_resource_category(
                facility_id, category_name, "product_knowledge"
            ).slug,
            "charge_item_definition": base.create_resource_category(
                facility_id, category_name, "charge_item_definition"
            ).slug,
        }

    supplier_orders = {}
    for idx, supplier in enumerate(suppliers):
        request_order = base.create_request_order(
            facility_id,
            name=f"Initial Stock Request — {supplier.name}",
            destination=pharmacy_location.id,
            supplier=supplier.id,
        )
        delivery_order = base.create_delivery_order(
            facility_id,
            name=f"Initial Stock Delivery — {supplier.name}",
            destination=pharmacy_location.id,
            supplier=supplier.id,
        )
        supplier_orders[idx] = (request_order, delivery_order)

    transfer_seed = None
    for idx, item in enumerate(INVENTORY_ITEMS):
        request_order, delivery_order = supplier_orders[idx % len(suppliers)]

        product, product_knowledge = base.create_facility_product(
            facility_id,
            item,
            categories[item["category"]],
        )

        supply_request = base.create_supply_request(
            order=request_order.id,
            item=product_knowledge.id,
            quantity=item["stock_quantity"],
        )

        delivery = base.create_supply_delivery(
            order=delivery_order.id,
            supplied_item=product.id,
            supplied_item_quantity=item["stock_quantity"],
            supply_request=supply_request.id,
        )

        base.update_supply_delivery(
            delivery.id, status="completed", order=delivery_order.id
        )

        if transfer_seed is None:
            transfer_seed = (product, item["stock_quantity"])

    if transfer_seed and transfer_destination:
        product, stock_quantity = transfer_seed
        transfer_quantity = max(1, stock_quantity // 4)

        pharmacy_inventory_items = base.list_inventory_items(
            facility_id, pharmacy_location.id
        )
        pharmacy_item = next(
            (
                ii
                for ii in pharmacy_inventory_items
                if ii["product"]["id"] == product.id
            ),
            None,
        )
        if pharmacy_item:
            transfer_request_order = base.create_request_order(
                facility_id,
                name="Ward Top-up Request",
                origin=pharmacy_location.id,
                destination=transfer_destination.id,
            )
            transfer_delivery_order = base.create_delivery_order(
                facility_id,
                name="Ward Top-up Delivery",
                origin=pharmacy_location.id,
                destination=transfer_destination.id,
            )
            transfer_supply_request = base.create_supply_request(
                order=transfer_request_order.id,
                item=product.product_knowledge["id"],
                quantity=transfer_quantity,
            )
            transfer_delivery = base.create_supply_delivery(
                order=transfer_delivery_order.id,
                supplied_inventory_item=pharmacy_item["id"],
                supplied_item_quantity=transfer_quantity,
                supply_request=transfer_supply_request.id,
            )
            base.update_supply_delivery(
                transfer_delivery.id,
                status="completed",
                order=transfer_delivery_order.id,
            )
