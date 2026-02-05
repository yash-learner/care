"""
Management command to load Products from CSV/Google Sheets.

Usage:
    python manage.py load_inventory <csv_file_or_url> --facility <facility_id>
    python manage.py load_inventory --google-sheet <sheet_id> --sheet-name <name> --facility <facility_id>
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand

from care.emr.management.commands.load_emr_utils import (
    load_data,
    write_output_csv,
)
from care.emr.models.charge_item_definition import ChargeItemDefinition
from care.emr.models.location import FacilityLocation
from care.emr.models.organization import Organization
from care.emr.models.product import Product
from care.emr.models.product_knowledge import ProductKnowledge
from care.emr.models.supply_delivery import DeliveryOrder, SupplyDelivery
from care.emr.resources.inventory.inventory_item.create_inventory_item import (
    create_inventory_item,
)
from care.emr.resources.inventory.inventory_item.sync_inventory_item import (
    sync_inventory_item,
)
from care.emr.resources.inventory.supply_delivery.delivery_order import (
    SupplyDeliveryOrderStatusOptions,
    SupplyDeliveryOrderWriteSpec,
)
from care.emr.resources.inventory.supply_delivery.spec import (
    SupplyDeliveryConditionOptions,
    SupplyDeliveryStatusOptions,
    SupplyDeliveryWriteSpec,
)
from care.emr.resources.organization.spec import (
    OrganizationTypeChoices,
    OrganizationWriteSpec,
)
from care.facility.models import Facility

logger = logging.getLogger(__name__)

current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent.parent.parent
default_output_path = root_dir / "outputs" / "product_output.csv"


class Command(BaseCommand):
    """
    Load Products from CSV or Google Sheets.

    Expected CSV columns:
    - product_knowledge_slug (required, slug of ProductKnowledge)
    - charge_item_definition_slug (optional, slug of ChargeItemDefinition)
    - lot_number (optional, lot number string - will be converted to batch format)
    - batch (optional, JSON string for batch information - overrides lot_number if provided)
    - expiration_date (optional, ISO format datetime string)
    - standard_pack_size (optional, integer)
    - extensions (optional, JSON string for extensions)
    - DeliveryOrders Name (required for delivery orders)
    - Supplier (required for delivery orders, Organization name)
    - Destination (required for delivery orders, FacilityLocation name)
    - supplied_item_pack_quantity (optional, integer)
    - supplied_item_pack_size (optional, integer)
    - supplied_item_condition (optional, default: Normal)
    - status (optional, default: Active for products, pending for delivery orders)
    """

    help = "Load Products from CSV or Google Sheets"

    def add_arguments(self, parser):
        parser.add_argument(
            "source",
            type=str,
            nargs="?",
            help="CSV file path or URL",
        )
        parser.add_argument(
            "--google-sheet",
            type=str,
            help="Google Sheet ID",
        )
        parser.add_argument(
            "--sheet-name",
            type=str,
            default="Sheet1",
            help="Sheet name (default: Sheet1)",
        )
        parser.add_argument(
            "--facility",
            type=str,
            required=True,
            help="Facility external ID",
        )
        parser.add_argument(
            "--output",
            type=str,
            help="Output CSV file path",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Batch size for processing (default: 100)",
        )

    def parse_json_field(self, value):
        """Parse JSON field from CSV, return None if empty or invalid."""
        import json

        if not value or not str(value).strip():
            return None
        try:
            return json.loads(str(value).strip())
        except (json.JSONDecodeError, ValueError):
            logger.warning("Invalid JSON field: %s", value)
            return None

    def parse_datetime(self, value):
        """Parse datetime field from CSV, return None if empty or invalid."""
        from django.utils import timezone
        from django.utils.dateparse import parse_date, parse_datetime

        if not value or not str(value).strip():
            return None
        try:
            value_str = str(value).strip()
            # Try parsing as full datetime first
            dt = parse_datetime(value_str)
            if dt:
                return dt

            # If that fails, try parsing as date-only and convert to datetime
            date = parse_date(value_str)
            if date:
                # Convert date to datetime at midnight UTC
                return timezone.make_aware(
                    datetime.combine(date, datetime.min.time()), timezone=UTC
                )

            return None
        except (ValueError, TypeError) as e:
            logger.warning("Invalid datetime field: %s - %s", value, e)
            return None

    def parse_integer(self, value):
        """Parse integer field from CSV, return None if empty or invalid."""
        if not value or not str(value).strip():
            return None
        try:
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            logger.warning("Invalid integer field: %s", value)
            return None

    def get_product_knowledge(self, slug_value: str, facility: Facility):
        """
        Get ProductKnowledge by slug.
        Raises ValueError if not found.
        """
        # Trim trailing dashes from slug
        slug_value = str(slug_value).strip().rstrip("-")

        # Try facility-scoped slug first
        full_slug = ProductKnowledge.calculate_slug_from_facility(
            str(facility.external_id), slug_value
        )
        product_knowledge = ProductKnowledge.objects.filter(
            slug=full_slug, facility=facility
        ).first()

        if product_knowledge:
            return product_knowledge

        # Try instance-scoped slug
        full_slug = ProductKnowledge.calculate_slug_from_instance(slug_value)
        product_knowledge = ProductKnowledge.objects.filter(
            slug=full_slug, facility__isnull=True
        ).first()

        if product_knowledge:
            return product_knowledge

        # Try exact slug match (in case full slug is provided)
        # slug_value already has trailing dashes trimmed
        product_knowledge = ProductKnowledge.objects.filter(slug=slug_value).first()
        if product_knowledge:
            return product_knowledge

        raise ValueError(f"ProductKnowledge not found with slug: {slug_value}")

    def get_charge_item_definition(
        self, slug_value: str, facility: Facility
    ) -> ChargeItemDefinition | None:
        """
        Get ChargeItemDefinition by slug.
        Returns None if slug is empty, raises ValueError if not found.
        """
        if not slug_value or not str(slug_value).strip():
            return None

        # Trim trailing dashes from slug
        slug_value = str(slug_value).strip().rstrip("-")

        # Try facility-scoped slug first
        full_slug = ChargeItemDefinition.calculate_slug_from_facility(
            str(facility.external_id), slug_value
        )
        charge_item = ChargeItemDefinition.objects.filter(
            slug=full_slug, facility=facility
        ).first()

        if charge_item:
            return charge_item

        # Try exact slug match (in case full slug is provided)
        charge_item = ChargeItemDefinition.objects.filter(
            slug=slug_value, facility=facility
        ).first()
        if charge_item:
            return charge_item

        raise ValueError(
            f"ChargeItemDefinition not found with slug: {slug_value} for facility"
        )

    def get_or_create_organization_by_name(self, name: str, created_by=None):
        """Get or create Organization by name with product_supplier type."""
        if not name or not str(name).strip():
            return None

        name = str(name).strip()

        # Try to find existing organization
        org = Organization.objects.filter(
            name__iexact=name,
            org_type=OrganizationTypeChoices.product_supplier.value,
        ).first()

        if org:
            logger.debug("Found existing organization: %s", name)
            return org

        # Create new organization
        logger.info("Creating new supplier organization: %s", name)
        org_data = {
            "name": name,
            "org_type": OrganizationTypeChoices.product_supplier.value,
            "active": True,
            "description": f"Supplier organization: {name}",
        }

        validated = OrganizationWriteSpec.model_validate(org_data)
        org = validated.de_serialize()
        org.created_by = created_by
        org.updated_by = created_by
        org.save()

        logger.debug("Created organization: %s", name)
        return org

    def get_location_by_name(self, name: str, facility: Facility):
        """Get FacilityLocation by name for the facility."""
        if not name or not str(name).strip():
            return None

        name = str(name).strip()
        location = FacilityLocation.objects.filter(
            name__iexact=name,
            facility=facility,
        ).first()

        if not location:
            raise ValueError(
                f"FacilityLocation not found with name: {name} for facility"
            )
        return location

    def get_or_create_delivery_order(
        self,
        name: str,
        supplier_name: str,
        destination_name: str,
        facility: Facility,
        created_by,
    ) -> DeliveryOrder:
        """Get or create a DeliveryOrder."""
        supplier = (
            self.get_or_create_organization_by_name(supplier_name, created_by)
            if supplier_name
            else None
        )
        destination = self.get_location_by_name(destination_name, facility)

        # Check if delivery order already exists
        order = DeliveryOrder.objects.filter(
            name=name,
            destination=destination,
            supplier=supplier,
            status=SupplyDeliveryOrderStatusOptions.pending.value,
        ).first()

        if order:
            return order

        # Create new delivery order
        order_data = {
            "name": name,
            "status": SupplyDeliveryOrderStatusOptions.pending.value,
            "destination": destination.external_id,
        }
        if supplier:
            order_data["supplier"] = supplier.external_id

        validated = SupplyDeliveryOrderWriteSpec.model_validate(order_data)
        order = validated.de_serialize()
        order.created_by = created_by
        order.updated_by = created_by
        order.save()

        logger.debug("Created delivery order: %s", name)
        return order

    def create_supply_delivery(
        self,
        product: Product,
        order: DeliveryOrder,
        pack_quantity: int | None,
        pack_size: int | None,
        condition: str,
        created_by,
    ) -> SupplyDelivery:
        """Create a SupplyDelivery."""
        # Parse condition
        condition_lower = (condition or "Normal").strip().lower()
        if condition_lower == "normal":
            supplied_item_condition = SupplyDeliveryConditionOptions.normal.value
        elif condition_lower == "damaged":
            supplied_item_condition = SupplyDeliveryConditionOptions.damaged.value
        else:
            supplied_item_condition = SupplyDeliveryConditionOptions.normal.value

        # Calculate quantity
        supplied_item_quantity = Decimal(0)
        if pack_quantity and pack_size:
            supplied_item_quantity = Decimal(pack_quantity * pack_size)

        delivery_data = {
            "status": SupplyDeliveryStatusOptions.completed.value,
            "supplied_item": product.external_id,
            "order": order.external_id,
            "supplied_item_quantity": supplied_item_quantity,
            "supplied_item_condition": supplied_item_condition,
        }

        if pack_quantity:
            delivery_data["supplied_item_pack_quantity"] = pack_quantity
        if pack_size:
            delivery_data["supplied_item_pack_size"] = pack_size

        validated = SupplyDeliveryWriteSpec.model_validate(delivery_data)
        delivery = validated.de_serialize()
        delivery.created_by = created_by
        delivery.updated_by = created_by

        # Create inventory item
        if delivery.supplied_item:
            delivery.supplied_inventory_item = create_inventory_item(
                delivery.supplied_item, order.destination
            )

        delivery.save()

        # Sync inventory item
        if delivery.supplied_inventory_item:
            sync_inventory_item(
                location=order.destination,
                product=delivery.supplied_inventory_item.product,
            )

        logger.debug(
            "Created supply delivery for product: %s", product.product_knowledge.slug
        )
        return delivery

    def process_row(self, row: dict, facility: Facility, created_by) -> dict:
        """
        Process a single CSV row into a Product data dict.
        Raises exceptions with descriptive messages on errors.
        """
        try:
            # Required field: product_knowledge_slug
            # Try multiple column name variations
            product_knowledge_slug = (
                row.get("product_knowledge_slug")
                or row.get("Product Knowledge Slug")
                or row.get("product_knowledge")
                or row.get("Product Knowledge")
            )
            if not product_knowledge_slug:
                raise ValueError("Missing required field: product_knowledge_slug")

            # Get ProductKnowledge
            product_knowledge = self.get_product_knowledge(
                str(product_knowledge_slug).strip(), facility
            )

            # Optional field: charge_item_definition_slug
            # Try multiple column name variations
            charge_item_definition_slug = (
                row.get("charge_item_definition_slug")
                or row.get("Charge Item Definition Slug")
                or row.get("charge_item_definition")
                or row.get("Charge Item Definition")
            )
            charge_item_definition = None
            if charge_item_definition_slug:
                charge_item_definition = self.get_charge_item_definition(
                    str(charge_item_definition_slug).strip(), facility
                )

            # Parse optional fields
            # Handle batch: prefer JSON batch field, otherwise use lot_number
            batch = self.parse_json_field(row.get("batch"))
            if not batch:
                # Try multiple column name variations for lot_number
                lot_number = (
                    row.get("lot_number")
                    or row.get("Lot Number")
                    or row.get("lot")
                    or row.get("Lot")
                )
                if lot_number and str(lot_number).strip():
                    batch = {"lot_number": str(lot_number).strip()}

            # Parse expiration_date - try multiple column name variations
            expiration_date = (
                self.parse_datetime(row.get("expiration_date"))
                or self.parse_datetime(row.get("Expiration Date"))
                or self.parse_datetime(row.get("expiration"))
                or self.parse_datetime(row.get("Expiration"))
            )

            standard_pack_size = self.parse_integer(row.get("standard_pack_size"))
            extensions = self.parse_json_field(row.get("extensions")) or {}

            # Store delivery order info for later processing
            delivery_order_name = (
                row.get("DeliveryOrders Name")
                or row.get("Delivery Orders Name")
                or row.get("delivery_orders_name")
            )
            supplier_name = row.get("Supplier") or row.get("supplier")
            destination_name = row.get("Destination") or row.get("destination")
            supplied_item_pack_quantity = self.parse_integer(
                row.get("supplied_item_pack_quantity")
            )
            supplied_item_pack_size = self.parse_integer(
                row.get("supplied_item_pack_size")
            )
            supplied_item_condition = (
                row.get("supplied_item_condition")
                or row.get("Supplied Item Condition")
                or "Normal"
            )

            return {
                "product_knowledge": product_knowledge,
                "charge_item_definition": charge_item_definition,
                "status": "active",  # Always active as per requirement
                "product_type": product_knowledge.product_type,
                "batch": batch,
                "expiration_date": expiration_date,
                "extensions": extensions,
                "standard_pack_size": standard_pack_size,
                "delivery_order_name": delivery_order_name,
                "supplier_name": supplier_name,
                "destination_name": destination_name,
                "supplied_item_pack_quantity": supplied_item_pack_quantity,
                "supplied_item_pack_size": supplied_item_pack_size,
                "supplied_item_condition": supplied_item_condition,
            }

        except (KeyError, ValueError) as e:
            error_message = f"Failed to process row: {e}"
            raise ValueError(error_message) from e
        except Exception as e:
            error_message = f"Unexpected error processing row: {e}"
            raise RuntimeError(error_message) from e

    def create_product(
        self, data: dict, facility: Facility, created_by
    ) -> tuple[Product, bool]:
        """
        Create or update a Product.
        Returns (product, created) tuple.
        Raises exceptions with descriptive messages on errors.
        """
        try:
            # Check if product already exists
            existing = Product.objects.filter(
                facility=facility,
                product_knowledge=data["product_knowledge"],
                charge_item_definition=data["charge_item_definition"],
            ).first()

            if existing:
                logger.debug(
                    "Product already exists: PK=%s, CID=%s",
                    data["product_knowledge"].slug,
                    data["charge_item_definition"].slug
                    if data["charge_item_definition"]
                    else None,
                )
                return existing, False

            # Create new product - only include batch and expiration_date if they have values
            product_kwargs = {
                "facility": facility,
                "product_knowledge": data["product_knowledge"],
                "charge_item_definition": data["charge_item_definition"],
                "status": data["status"],
                "product_type": data["product_type"],
                "extensions": data["extensions"],
                "created_by": created_by,
                "updated_by": created_by,
            }

            # Set batch - use provided batch dict (even if empty)
            # If batch is None, use empty dict (model default)
            batch_value = data.get("batch")
            if batch_value is not None:
                product_kwargs["batch"] = batch_value
            # Otherwise, let model use its default (empty dict)

            # Set expiration_date if provided
            expiration_date_value = data.get("expiration_date")
            if expiration_date_value is not None:
                product_kwargs["expiration_date"] = expiration_date_value

            # Only set standard_pack_size if it has a value
            if data.get("standard_pack_size") is not None:
                product_kwargs["standard_pack_size"] = data["standard_pack_size"]

            product = Product(**product_kwargs)
            product.save()
            logger.debug(
                "Created product: PK=%s",
                data["product_knowledge"].slug,
            )
            return product, True

        except Exception as e:
            product_knowledge_name = (
                data["product_knowledge"].name
                if data.get("product_knowledge")
                else "Unknown"
            )
            error_message = f"Failed to create product '{product_knowledge_name}': {e}"
            raise RuntimeError(error_message) from e

    def handle(self, *args, **options):
        start_time = datetime.now(tz=UTC)

        # Set logging level
        if options["verbosity"] == 0:
            logger.setLevel(logging.ERROR)
        elif options["verbosity"] == 1:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)

        try:
            facility = Facility.objects.get(external_id=options["facility"])
            logger.info("Loading products for facility: %s", facility.name)

            rows = load_data(options)
            logger.info("Loaded %d rows from source", len(rows))

            if not rows:
                self.stdout.write(self.style.WARNING("No rows found in source"))
                return

            batch_size = options["batch_size"]
            total_rows = len(rows)
            created_count = 0
            updated_count = 0
            failed = []
            output_rows = []

            # Group rows by delivery order (Name + Supplier + Destination)
            delivery_order_groups = {}
            processed_products = []

            for i in range(0, total_rows, batch_size):
                batch = rows[i : i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_rows + batch_size - 1) // batch_size

                logger.info(
                    "Processing batch %d/%d (rows %d-%d)",
                    batch_num,
                    total_batches,
                    i + 1,
                    min(i + batch_size, total_rows),
                )

                for row in batch:
                    row_identifier = (
                        row.get("product_knowledge_slug")
                        or row.get("Product Knowledge Slug")
                        or row.get("product_knowledge")
                        or row.get("Product Knowledge")
                        or "Unknown"
                    )

                    try:
                        data = self.process_row(row, facility, None)
                        product, created = self.create_product(data, facility, None)

                        if created:
                            created_count += 1
                            status = "Created"
                        else:
                            updated_count += 1
                            status = "Updated"

                        # Store product data for delivery order processing
                        processed_products.append(
                            {
                                "product": product,
                                "data": data,
                                "row": row,
                            }
                        )

                        # Group by delivery order
                        delivery_order_name = data.get("delivery_order_name")
                        supplier_name = data.get("supplier_name")
                        destination_name = data.get("destination_name")

                        if delivery_order_name and destination_name:
                            group_key = (
                                delivery_order_name,
                                supplier_name or "",
                                destination_name,
                            )
                            if group_key not in delivery_order_groups:
                                delivery_order_groups[group_key] = []
                            delivery_order_groups[group_key].append(
                                {
                                    "product": product,
                                    "data": data,
                                }
                            )

                        output_rows.append(
                            {
                                "product_knowledge_slug": data[
                                    "product_knowledge"
                                ].slug,
                                "charge_item_definition_slug": (
                                    data["charge_item_definition"].slug
                                    if data["charge_item_definition"]
                                    else ""
                                ),
                                "status": status,
                                "error": "",
                            }
                        )

                    except Exception as e:
                        logger.error("Error processing row '%s': %s", row_identifier, e)
                        failed.append(row_identifier)
                        output_rows.append(
                            {
                                "product_knowledge_slug": str(row_identifier),
                                "charge_item_definition_slug": "",
                                "status": "Failed",
                                "error": str(e),
                            }
                        )

            # Create delivery orders and supply deliveries
            delivery_orders_created = 0
            supply_deliveries_created = 0

            for (
                order_name,
                supplier_name,
                destination_name,
            ), products in delivery_order_groups.items():
                try:
                    logger.info(
                        "Creating delivery order: %s (Supplier: %s, Destination: %s)",
                        order_name,
                        supplier_name or "None",
                        destination_name,
                    )
                    order = self.get_or_create_delivery_order(
                        order_name,
                        supplier_name,
                        destination_name,
                        facility,
                        None,
                    )
                    delivery_orders_created += 1

                    # Create supply deliveries for each product
                    for product_data in products:
                        try:
                            product = product_data["product"]
                            data = product_data["data"]

                            self.create_supply_delivery(
                                product,
                                order,
                                data.get("supplied_item_pack_quantity"),
                                data.get("supplied_item_pack_size"),
                                data.get("supplied_item_condition", "Normal"),
                                None,
                            )
                            supply_deliveries_created += 1
                        except Exception as e:
                            logger.error(
                                "Error creating supply delivery for product %s: %s",
                                product.product_knowledge.slug,
                                e,
                            )

                    # Complete the delivery order
                    order.status = SupplyDeliveryOrderStatusOptions.completed.value
                    order.save()

                except Exception as e:
                    logger.error(
                        "Error creating delivery order '%s': %s",
                        order_name,
                        e,
                    )

            output_path = options.get("output") or default_output_path
            if output_path:
                write_output_csv(
                    output_path,
                    output_rows,
                    [
                        "product_knowledge_slug",
                        "charge_item_definition_slug",
                        "status",
                        "error",
                    ],
                )

            self.stdout.write("\n=== Summary ===")
            self.stdout.write(f"Total rows: {total_rows}")
            self.stdout.write(self.style.SUCCESS(f"Products created: {created_count}"))
            self.stdout.write(self.style.SUCCESS(f"Products updated: {updated_count}"))
            self.stdout.write(
                self.style.SUCCESS(
                    f"Delivery orders created: {delivery_orders_created}"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Supply deliveries created: {supply_deliveries_created}"
                )
            )
            self.stdout.write(self.style.ERROR(f"Failed: {len(failed)}"))
            self.stdout.write(f"Time taken: {datetime.now(tz=UTC) - start_time}")
            self.stdout.write(self.style.SUCCESS("Inventory loaded successfully"))

        except Exception as e:
            logger.exception("Error in main process")
            error_message = f"Error in main process: {e}"
            self.stdout.write(self.style.ERROR(error_message))
            raise
