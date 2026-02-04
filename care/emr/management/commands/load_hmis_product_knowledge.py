"""
Management command to load Product Knowledge from CSV/Google Sheets.

Usage:
    python manage.py load_hmis_product_knowledge <csv_file_or_url> --facility <facility_id>
    python manage.py load_hmis_product_knowledge --google-sheet <sheet_id> --sheet-name <name> --facility <facility_id>
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

from django.core.management.base import BaseCommand

from care.emr.management.commands.load_emr_utils import (
    create_slug,
    ensure_category,
    normalize_title,
    read_csv_from_file,
    read_csv_from_google_sheet,
    read_csv_from_url,
    write_output_csv,
)
from care.emr.models.product_knowledge import ProductKnowledge
from care.facility.models import Facility

logger = logging.getLogger(__name__)

current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent.parent.parent
default_output_path = root_dir / "outputs" / "product_knowledge_output.csv"


class Command(BaseCommand):
    """
    Load Product Knowledge from CSV or Google Sheets.

    Expected CSV columns:
    - name (required)
    - product_type (required: medication, nutritional_product, consumable)
    - category (required, category name)
    - display (optional, SNOMED display for code)
    - code (optional, SNOMED code)
    - base_unit (required, UCUM unit code e.g., "{tbl}", "mL")
    - status (optional, default: active)
    - hsn_code (optional, stored as alternate_identifier)
    - alternative_trade_names (optional, comma-separated trade names)
    - preferred_name (optional)
    - original_name (optional)
    - alias_name (optional)
    - note (optional, storage guideline note)
    - duration_value (optional, stability duration value)
    - duration_unit (optional, stability duration unit)
    - dosage_form_display (optional, SNOMED display)
    - dosage_form_code (optional, SNOMED code)
    - route_display (optional, comma-separated SNOMED displays)
    - route_code (optional, comma-separated SNOMED codes)
    """

    help = "Load Product Knowledge from CSV or Google Sheets"

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
            default="Product Knowledge",
            help="Sheet name (default: Product Knowledge)",
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

    def load_data(self, options):
        """Load data from source."""
        if options["google_sheet"]:
            return read_csv_from_google_sheet(
                options["google_sheet"], options["sheet_name"]
            )
        if options["source"]:
            if options["source"].startswith("http"):
                return read_csv_from_url(options["source"])
            return read_csv_from_file(options["source"])
        raise ValueError("Must provide either source file/URL or --google-sheet")

    def parse_code(self, code_value, display_value, system="http://snomed.info/sct"):
        """Parse code into a coded object."""
        if not code_value and not display_value:
            return None
        return {
            "system": system,
            "code": str(code_value).strip() if code_value else "",
            "display": str(display_value).strip() if display_value else "",
        }

    def parse_base_unit(self, unit_code):
        """Parse base unit into UCUM coded object."""
        if not unit_code:
            return None
        code = str(unit_code).strip()
        # Common UCUM unit display mappings
        unit_displays = {
            "{tbl}": "tablets",
            "{cap}": "capsules",
            "mL": "milliliters",
            "L": "liters",
            "g": "grams",
            "mg": "milligrams",
            "kg": "kilograms",
            "{vial}": "vials",
            "{amp}": "ampoules",
            "{pck}": "packs",
            "{unit}": "units",
        }
        return {
            "system": "http://unitsofmeasure.org",
            "code": code,
            "display": unit_displays.get(code, code),
        }

    def parse_names(self, row: dict) -> list:
        """Parse various name fields into names array."""
        names = []

        # Alternative trade names (comma-separated)
        if row.get("alternative_trade_names"):
            trade_names = [
                n.strip()
                for n in str(row["alternative_trade_names"]).split(",")
                if n.strip()
            ]
            for trade_name in trade_names:
                names.append({"name_type": "trade_name", "name": trade_name})

        # Preferred name
        if row.get("preferred_name"):
            names.append({
                "name_type": "preferred",
                "name": str(row["preferred_name"]).strip(),
            })

        # Original name
        if row.get("original_name"):
            names.append({
                "name_type": "original_name",
                "name": str(row["original_name"]).strip(),
            })

        # Alias name
        if row.get("alias_name"):
            names.append({
                "name_type": "alias",
                "name": str(row["alias_name"]).strip(),
            })

        return names

    def parse_storage_guidelines(self, row: dict) -> list:
        """Parse storage guideline fields."""
        if not row.get("note"):
            return []

        guideline = {"note": str(row["note"]).strip()}

        # Add stability duration if provided
        if row.get("duration_value") and row.get("duration_unit"):
            guideline["stability_duration"] = {
                "value": str(row["duration_value"]).strip(),
                "unit": self.parse_base_unit(row["duration_unit"]),
            }

        return [guideline]

    def parse_definitional(self, row: dict) -> dict:
        """Parse definitional fields (dosage form, routes)."""
        definitional = {}

        # Dosage form
        if row.get("dosage_form_code") or row.get("dosage_form_display"):
            definitional["dosage_form"] = self.parse_code(
                row.get("dosage_form_code"),
                row.get("dosage_form_display"),
            )

        # Intended routes (comma-separated)
        if row.get("route_code") or row.get("route_display"):
            route_codes = []
            route_displays = []

            if row.get("route_code"):
                route_codes = [
                    c.strip() for c in str(row["route_code"]).split(",") if c.strip()
                ]
            if row.get("route_display"):
                route_displays = [
                    d.strip() for d in str(row["route_display"]).split(",") if d.strip()
                ]

            # Pair up codes and displays
            max_len = max(len(route_codes), len(route_displays))
            intended_routes = []
            for i in range(max_len):
                code = route_codes[i] if i < len(route_codes) else ""
                display = route_displays[i] if i < len(route_displays) else ""
                if code or display:
                    intended_routes.append(self.parse_code(code, display))

            if intended_routes:
                definitional["intended_routes"] = intended_routes

        return definitional if definitional else {}

    def process_row(self, row: dict, facility: Facility, created_by) -> dict:
        """
        Process a single CSV row into a ProductKnowledge data dict.
        Raises exceptions with descriptive messages on errors.
        """
        try:
            if not row.get("name"):
                raise ValueError("Missing required field: name")

            if not row.get("product_type"):
                raise ValueError("Missing required field: product_type")

            if not row.get("category"):
                raise ValueError("Missing required field: category")

            if not row.get("base_unit"):
                raise ValueError("Missing required field: base_unit")

            # Validate product_type
            valid_product_types = ["medication", "nutritional_product", "consumable"]
            product_type = row["product_type"].strip().lower()
            if product_type not in valid_product_types:
                raise ValueError(
                    f"Invalid product_type: {product_type}. "
                    f"Must be one of: {valid_product_types}"
                )

            # Ensure category exists
            category_name = row["category"].strip()
            try:
                category = ensure_category(
                    category_name,
                    facility,
                    "product_knowledge",
                    created_by,
                )
            except Exception as e:
                error_message = f"Failed to ensure category '{category_name}': {e}"
                raise ValueError(error_message) from e

            name = normalize_title(row["name"])
            slug_value = create_slug(name)
            # Parse code
            code = self.parse_code(row.get("code"), row.get("display"))

            # Parse base unit
            base_unit = self.parse_base_unit(row.get("base_unit"))

            # Parse names array
            names = self.parse_names(row)

            # Parse storage guidelines
            storage_guidelines = self.parse_storage_guidelines(row)

            # Parse definitional
            definitional = self.parse_definitional(row)

            return {
                "name": name,
                "slug_value": slug_value,
                "product_type": product_type,
                "status": (row.get("status") or "").strip().lower() or "active",
                "category": category,
                "code": code,
                "base_unit": base_unit,
                "alternate_identifier": row.get("hsn_code", "").strip() or None,
                "names": names if names else [],
                "storage_guidelines": storage_guidelines if storage_guidelines else [],
                "definitional": definitional if definitional else {},
            }

        except (KeyError, ValueError) as e:
            error_message = f"Failed to process row: {e}"
            raise ValueError(error_message) from e
        except Exception as e:
            error_message = f"Unexpected error processing row: {e}"
            raise RuntimeError(error_message) from e

    def create_or_update_product_knowledge(
        self, data: dict, facility: Facility, created_by
    ) -> tuple[ProductKnowledge, bool]:
        """
        Create or update a ProductKnowledge.
        Returns (product, created) tuple.
        """
        try:
            full_slug = ProductKnowledge.calculate_slug_from_facility(
                str(facility.external_id), data["slug_value"]
            )

            # Update or create by name + facility
            product, created = ProductKnowledge.objects.update_or_create(
                name=data["name"],
                facility=facility,
                defaults={
                    "slug": full_slug,
                    "product_type": data["product_type"],
                    "status": data["status"],
                    "category": data["category"],
                    "code": data["code"],
                    "base_unit": data["base_unit"],
                    "alternate_identifier": data["alternate_identifier"],
                    "names": data["names"],
                    "storage_guidelines": data["storage_guidelines"],
                    "definitional": data["definitional"],
                    "created_by": created_by,
                    "updated_by": created_by,
                },
            )

            if created:
                logger.debug("Created product knowledge: %s", data["name"])
            else:
                logger.debug("Updated product knowledge: %s", data["name"])

            return product, created

        except Exception as e:
            error_message = (
                f"Failed to create/update product knowledge "
                f"'{data.get('name', 'Unknown')}': {e}"
            )
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
            logger.info("Loading product knowledge for facility: %s", facility.name)

            rows = self.load_data(options)
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
                    row_name = row.get("name", "Unknown")

                    try:
                        data = self.process_row(row, facility, None)
                        product, created = self.create_or_update_product_knowledge(
                            data, facility, None
                        )

                        if created:
                            created_count += 1
                            status = "Created"
                        else:
                            updated_count += 1
                            status = "Updated"

                        output_rows.append({
                            "name": data["name"],
                            "slug_value": data["slug_value"],
                            "status": status,
                            "error": "",
                        })

                    except Exception as e:
                        logger.error("Error processing row '%s': %s", row_name, e)
                        failed.append(row_name)
                        output_rows.append({
                            "name": row_name,
                            "slug_value": "",
                            "status": "Failed",
                            "error": str(e),
                        })

            output_path = options.get("output") or default_output_path
            if output_path:
                write_output_csv(
                    output_path,
                    output_rows,
                    ["name", "slug_value", "status", "error"],
                )

            self.stdout.write("\n=== Summary ===")
            self.stdout.write(f"Total rows: {total_rows}")
            self.stdout.write(self.style.SUCCESS(f"Created: {created_count}"))
            self.stdout.write(self.style.SUCCESS(f"Updated: {updated_count}"))
            self.stdout.write(self.style.ERROR(f"Failed: {len(failed)}"))
            self.stdout.write(f"Time taken: {datetime.now(tz=UTC) - start_time}")
            self.stdout.write(
                self.style.SUCCESS("Product knowledge loaded successfully")
            )

        except Exception as e:
            logger.exception("Error in main process")
            error_message = f"Error in main process: {e}"
            self.stdout.write(self.style.ERROR(error_message))
            raise
