"""
Management command to load Products from CSV/Google Sheets.

Usage:
    python manage.py load_inventory <csv_file_or_url> --facility <facility_id>
    python manage.py load_inventory --google-sheet <sheet_id> --sheet-name <name> --facility <facility_id>
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

from django.core.management.base import BaseCommand

from care.emr.management.commands.load_emr_utils import (
    load_data,
    write_output_csv,
)
from care.emr.models.charge_item_definition import ChargeItemDefinition
from care.emr.models.product import Product
from care.emr.models.product_knowledge import ProductKnowledge
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
    - batch (optional, JSON string for batch information)
    - expiration_date (optional, ISO format datetime string)
    - standard_pack_size (optional, integer)
    - extensions (optional, JSON string for extensions)
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
        from django.utils.dateparse import parse_datetime

        if not value or not str(value).strip():
            return None
        try:
            return parse_datetime(str(value).strip())
        except (ValueError, TypeError):
            logger.warning("Invalid datetime field: %s", value)
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

        slug_value = str(slug_value).strip()

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
            batch = self.parse_json_field(row.get("batch"))
            expiration_date = self.parse_datetime(row.get("expiration_date"))
            standard_pack_size = self.parse_integer(row.get("standard_pack_size"))
            extensions = self.parse_json_field(row.get("extensions")) or {}

            return {
                "product_knowledge": product_knowledge,
                "charge_item_definition": charge_item_definition,
                "status": "active",  # Always active as per requirement
                "product_type": product_knowledge.product_type,
                "batch": batch,
                "expiration_date": expiration_date,
                "extensions": extensions,
                "standard_pack_size": standard_pack_size,
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

            # Create new product
            product = Product(
                facility=facility,
                product_knowledge=data["product_knowledge"],
                charge_item_definition=data["charge_item_definition"],
                status=data["status"],
                product_type=data["product_type"],
                batch=data["batch"],
                expiration_date=data["expiration_date"],
                extensions=data["extensions"],
                standard_pack_size=data["standard_pack_size"],
                created_by=created_by,
                updated_by=created_by,
            )
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
            self.stdout.write(self.style.SUCCESS(f"Created: {created_count}"))
            self.stdout.write(self.style.SUCCESS(f"Updated: {updated_count}"))
            self.stdout.write(self.style.ERROR(f"Failed: {len(failed)}"))
            self.stdout.write(f"Time taken: {datetime.now(tz=UTC) - start_time}")
            self.stdout.write(self.style.SUCCESS("Products loaded successfully"))

        except Exception as e:
            logger.exception("Error in main process")
            error_message = f"Error in main process: {e}"
            self.stdout.write(self.style.ERROR(error_message))
            raise
