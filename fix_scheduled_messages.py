import os
import sys
import json
import argparse
from supabase import create_client, Client
from datetime import datetime, timedelta

# Default Supabase credentials (will be used if environment variables are not set)
DEFAULT_SUPABASE_URL = "https://aubulhjfeszmsheonmpy.supabase.co"
DEFAULT_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc"


def parse_args():
    parser = argparse.ArgumentParser(description="Fix issues in scheduled messages")
    parser.add_argument(
        "--fix-metadata", action="store_true", help="Fix messages with missing metadata"
    )
    parser.add_argument(
        "--reset-failed",
        action="store_true",
        help="Reset failed messages to pending status",
    )
    parser.add_argument(
        "--fix-past-due",
        action="store_true",
        help="Fix past due messages still in pending status",
    )
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Automatically confirm all fixes"
    )
    parser.add_argument(
        "--supabase-url", help="Supabase URL (overrides environment variable)"
    )
    parser.add_argument(
        "--supabase-key", help="Supabase Key (overrides environment variable)"
    )
    return parser.parse_args()


def fix_scheduled_messages(
    fix_metadata=False,
    reset_failed=False,
    fix_past_due=False,
    json_output=False,
    dry_run=False,
    auto_confirm=False,
    supabase_url=None,
    supabase_key=None,
):
    # Get Supabase credentials from arguments, environment variables, or default values
    supabase_url = (
        supabase_url or os.environ.get("SUPABASE_URL") or DEFAULT_SUPABASE_URL
    )
    supabase_key = (
        supabase_key or os.environ.get("SUPABASE_KEY") or DEFAULT_SUPABASE_KEY
    )

    if not supabase_url or not supabase_key:
        if json_output:
            print(
                json.dumps(
                    {
                        "success": False,
                        "error": "Missing Supabase credentials",
                        "details": "SUPABASE_URL and SUPABASE_KEY must be provided",
                    }
                )
            )
        else:
            sys.stderr.write(
                "Error: Missing Supabase credentials. They must be provided via environment variables or command line arguments.\n"
            )
        return 0

    if not fix_metadata and not reset_failed and not fix_past_due:
        if json_output:
            print(
                json.dumps(
                    {
                        "success": False,
                        "error": "No fix actions specified",
                        "details": "Use --fix-metadata, --reset-failed, or --fix-past-due to specify what to fix",
                    }
                )
            )
        else:
            sys.stderr.write(
                "Error: No fix actions specified. Use --fix-metadata, --reset-failed, or --fix-past-due to specify what to fix.\n"
            )
        return 0

    # Initialize Supabase client
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
    except Exception as e:
        if json_output:
            print(
                json.dumps(
                    {
                        "success": False,
                        "error": "Failed to connect to Supabase",
                        "details": str(e),
                    }
                )
            )
        else:
            sys.stderr.write(f"Error: Failed to connect to Supabase: {str(e)}\n")
        return 0

    # First, let's get the table structure to discover the correct column names
    try:
        # Try to get the first row to determine column names
        response = supabase.table("scheduled_messages").select("*").limit(1).execute()
        sample_data = response.data[0] if response.data else {}

        # Identify the due time column based on what exists in the data
        time_related_columns = ["scheduled_at", "due_at", "send_at", "execute_at"]
        due_time_column = next(
            (col for col in time_related_columns if col in sample_data), "scheduled_at"
        )

        if not json_output:
            sys.stderr.write(f"Using '{due_time_column}' as the due time column\n")
    except Exception:
        # If we can't determine the column, default to 'scheduled_at'
        due_time_column = "scheduled_at"
        if not json_output:
            sys.stderr.write(
                f"Using default column name '{due_time_column}' for due time\n"
            )

    # Get all scheduled messages with issues
    try:
        response = supabase.table("scheduled_messages").select("*").execute()
        all_messages = response.data
    except Exception as e:
        if json_output:
            print(
                json.dumps(
                    {
                        "success": False,
                        "error": "Failed to fetch scheduled messages",
                        "details": str(e),
                    }
                )
            )
        else:
            sys.stderr.write(f"Error: Failed to fetch scheduled messages: {str(e)}\n")
        return 0

    if not all_messages:
        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "message": "No scheduled messages found",
                        "fixed_count": 0,
                    }
                )
            )
        else:
            sys.stderr.write("No scheduled messages found in the database.\n")
        return 0

    # Find messages that need fixing
    messages_to_fix_metadata = []
    failed_messages_to_reset = []
    past_due_messages = []

    now = datetime.now().isoformat()

    for msg in all_messages:
        # Check for missing metadata
        if fix_metadata and (not msg.get("metadata") or msg.get("metadata") == "{}"):
            messages_to_fix_metadata.append(msg)

        # Check for failed messages
        if reset_failed and msg.get("status") == "failed":
            failed_messages_to_reset.append(msg)

        # Check for past due messages with 'pending' status
        if (
            fix_past_due
            and msg.get("status") == "pending"
            and due_time_column in msg
            and msg[due_time_column]
            and msg[due_time_column] < now
        ):
            past_due_messages.append(msg)

    total_to_fix = (
        len(messages_to_fix_metadata)
        + len(failed_messages_to_reset)
        + len(past_due_messages)
    )

    if total_to_fix == 0:
        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "message": "No issues found that need fixing",
                        "fixed_count": 0,
                    }
                )
            )
        else:
            sys.stderr.write("No issues found that need fixing.\n")
        return 0

    if not json_output:
        sys.stderr.write("\nIssues found that need fixing:\n")
        if fix_metadata and messages_to_fix_metadata:
            sys.stderr.write(
                f"- Messages with missing metadata: {len(messages_to_fix_metadata)}\n"
            )
        if reset_failed and failed_messages_to_reset:
            sys.stderr.write(
                f"- Failed messages to reset: {len(failed_messages_to_reset)}\n"
            )
        if fix_past_due and past_due_messages:
            sys.stderr.write(f"- Past due pending messages: {len(past_due_messages)}\n")

        if dry_run:
            sys.stderr.write("\nDRY RUN: No changes will be made to the database.\n")
            return 0

        if not auto_confirm:
            sys.stderr.write(
                "\nDo you want to proceed with fixing these issues? (y/N): "
            )
            sys.stderr.flush()
            confirmation = input().strip()
            if confirmation.lower() != "y":
                sys.stderr.write("Operation cancelled.\n")
                return 0

    fixed_count = 0

    # Fix messages with missing metadata
    if fix_metadata and messages_to_fix_metadata:
        default_metadata = {
            "type": "single",
            "template": "",
            "timezone": "UTC",
            "priority": "normal",
            "retry_count": 0,
        }

        for msg in messages_to_fix_metadata:
            try:
                if not dry_run:
                    supabase.table("scheduled_messages").update(
                        {"metadata": default_metadata}
                    ).eq("id", msg.get("id")).execute()
                fixed_count += 1
            except Exception as e:
                if not json_output:
                    sys.stderr.write(
                        f"Error fixing metadata for message {msg.get('id')}: {str(e)}\n"
                    )

    # Reset failed messages to pending
    if reset_failed and failed_messages_to_reset:
        for msg in failed_messages_to_reset:
            try:
                if not dry_run:
                    # Schedule for 15 minutes from now
                    new_time = (datetime.now() + timedelta(minutes=15)).isoformat()
                    update_data = {
                        "status": "pending",
                        "error": None,
                        due_time_column: new_time,
                    }
                    supabase.table("scheduled_messages").update(update_data).eq(
                        "id", msg.get("id")
                    ).execute()
                fixed_count += 1
            except Exception as e:
                if not json_output:
                    sys.stderr.write(
                        f"Error resetting failed message {msg.get('id')}: {str(e)}\n"
                    )

    # Fix past due pending messages
    if fix_past_due and past_due_messages:
        for msg in past_due_messages:
            try:
                if not dry_run:
                    # Change status to processing or reschedule for 5 minutes from now
                    new_time = (datetime.now() + timedelta(minutes=5)).isoformat()
                    update_data = {due_time_column: new_time}
                    supabase.table("scheduled_messages").update(update_data).eq(
                        "id", msg.get("id")
                    ).execute()
                fixed_count += 1
            except Exception as e:
                if not json_output:
                    sys.stderr.write(
                        f"Error fixing past due message {msg.get('id')}: {str(e)}\n"
                    )

    if json_output:
        print(
            json.dumps(
                {
                    "success": True,
                    "fixed_count": fixed_count,
                    "total_issues": total_to_fix,
                    "fixes": {
                        "metadata_fixed": len(messages_to_fix_metadata)
                        if fix_metadata
                        else 0,
                        "failed_reset": len(failed_messages_to_reset)
                        if reset_failed
                        else 0,
                        "past_due_fixed": len(past_due_messages) if fix_past_due else 0,
                    },
                    "dry_run": dry_run,
                }
            )
        )
    else:
        if dry_run:
            sys.stderr.write(f"\nDRY RUN: Would fix {fixed_count} issues.\n")
        else:
            sys.stderr.write(f"\nSuccessfully fixed {fixed_count} issues.\n")

        # Simple JSON output for PowerShell parsing
        print(
            json.dumps(
                {
                    "success": True,
                    "fixes_applied": fixed_count,
                    "fix_details": {
                        "past_due_fixed": len(past_due_messages) if fix_past_due else 0,
                        "metadata_fixed": len(messages_to_fix_metadata)
                        if fix_metadata
                        else 0,
                        "stuck_processing_fixed": 0,
                        "failed_messages_reset": len(failed_messages_to_reset)
                        if reset_failed
                        else 0,
                    },
                }
            )
        )

    return fixed_count


if __name__ == "__main__":
    args = parse_args()
    fixed_count = fix_scheduled_messages(
        fix_metadata=args.fix_metadata,
        reset_failed=args.reset_failed,
        fix_past_due=args.fix_past_due,
        json_output=args.json,
        dry_run=args.dry_run,
        auto_confirm=args.yes,
        supabase_url=args.supabase_url,
        supabase_key=args.supabase_key,
    )
    sys.exit(0 if fixed_count >= 0 else 1)
