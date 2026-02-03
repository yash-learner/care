import logging
from datetime import UTC, datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from care.emr.management.commands.load_emr_utils import load_data, set_logger_level
from care.security.models import PermissionModel, RoleModel, RolePermission

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "script to load hmis data from google sheets"

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
            default="User permission",
            help="Sheet name (default: User permission)",
        )

    def handle(self, *args, **options):
        start_time = datetime.now(tz=UTC)
        set_logger_level(logger, options.get("verbosity", 1))
        roles = {}
        permissions = {perm.name: perm for perm in PermissionModel.objects.all()}
        print(permissions.keys())
        with transaction.atomic():
            rows = load_data(options)
            for row in rows:
                row.pop("No", None)
                # get all columns
                perm_name = row.pop("Permission", "").strip()
                if not perm_name:
                    continue
                for p in row:
                    role_name = p.strip()
                    if role_name not in roles:
                        role, _ = RoleModel.objects.get_or_create(name=role_name)
                        roles[role_name] = role
                    else:
                        role = roles[role_name]
                    permission = permissions.get(perm_name)
                    if not permission:
                        raise ValueError(
                            f"Permission '{perm_name}' not found in database."
                        )

                    if row[p].lower() in ["yes", "y", "true", "1"]:
                        logger.debug(
                            "Assigning permission '%s' to role '%s'",
                            perm_name,
                            role_name,
                        )
                        RolePermission.objects.get_or_create(
                            role=role,
                            permission=permission,
                        )
                    else:
                        RolePermission.objects.filter(
                            role=role,
                            permission=permission,
                        ).delete()

        self.stdout.write("\n=== Summary ===")
        self.stdout.write(self.style.SUCCESS("HMIS permissions loaded successfully"))
        self.stdout.write(f"Total rows: {len(rows)}")
        self.stdout.write(f"Time taken: {datetime.now(tz=UTC) - start_time}")
