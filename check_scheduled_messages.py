import os
import sys
import json
from supabase import create_client, Client
from datetime import datetime
import argparse

# Default Supabase credentials (will be used if environment variables are not set)
DEFAULT_SUPABASE_URL = "https://aubulhjfeszmsheonmpy.supabase.co"
DEFAULT_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc"


def parse_args():
    parser = argparse.ArgumentParser(description="Check scheduled messages for issues")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument(
        "--supabase-url", help="Supabase URL (overrides environment variable)"
    )
    parser.add_argument(
        "--supabase-key", help="Supabase Key (overrides environment variable)"
    )
    return parser.parse_args()


def check_scheduled_messages(
    verbose=False, json_output=False, supabase_url=None, supabase_key=None
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
        return False, None

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
        return False, None

    if not json_output:
        sys.stderr.write("Checking scheduled messages in database...\n")

    try:
        # First, let's get the table structure to discover the correct column names
        try:
            # Try to get the first row to determine column names
            response = (
                supabase.table("scheduled_messages").select("*").limit(1).execute()
            )
            sample_data = response.data[0] if response.data else {}

            # Identify the due time column based on what exists in the data
            time_related_columns = ["scheduled_at", "due_at", "send_at", "execute_at"]
            due_time_column = next(
                (col for col in time_related_columns if col in sample_data),
                "scheduled_at",
            )

            if not json_output and verbose:
                sys.stderr.write(f"Using '{due_time_column}' as the due time column\n")
        except Exception:
            # If we can't determine the column, default to 'scheduled_at'
            due_time_column = "scheduled_at"
            if not json_output and verbose:
                sys.stderr.write(
                    f"Using default column name '{due_time_column}' for due time\n"
                )

        # Get all scheduled messages
        response = supabase.table("scheduled_messages").select("*").execute()
        messages = response.data
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
        return False, None

    if not messages:
        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "total": 0,
                        "issues": {
                            "missing_metadata": [],
                            "missing_chat_id": [],
                            "failed_messages": [],
                        },
                        "status_counts": {},
                    }
                )
            )
        else:
            sys.stderr.write("No scheduled messages found in the database.\n")
        return False, None

    # Count message status
    status_counts = {}
    for msg in messages:
        status = msg.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    # Identify messages with issues
    missing_metadata = []
    missing_chat_id = []
    failed_messages = []
    past_due_messages = []

    now = datetime.now().isoformat()

    for msg in messages:
        # Check for missing metadata
        if not msg.get("metadata") or msg.get("metadata") == "{}":
            missing_metadata.append(msg.get("id"))

        # Check for missing chat_id
        if not msg.get("chat_id"):
            missing_chat_id.append(msg.get("id"))

        # Check for failed messages
        if msg.get("status") == "failed":
            failed_messages.append(msg.get("id"))

        # Check for past due messages with 'pending' status
        if (
            msg.get("status") == "pending"
            and due_time_column in msg
            and msg[due_time_column]
            and msg[due_time_column] < now
        ):
            past_due_messages.append(msg.get("id"))

    has_issues = (
        len(missing_metadata) > 0
        or len(missing_chat_id) > 0
        or len(failed_messages) > 0
        or len(past_due_messages) > 0
    )

    if json_output:
        result = {
            "success": True,
            "has_issues": has_issues,
            "total": len(messages),
            "status_counts": status_counts,
            "issues": {
                "missing_metadata": missing_metadata,
                "missing_chat_id": missing_chat_id,
                "failed_messages": failed_messages,
                "past_due_messages": past_due_messages,
            },
            "due_time_column": due_time_column,
        }
        print(json.dumps(result))
    else:
        # Print report to stderr
        sys.stderr.write("\nScheduled Messages Status Report:\n")
        sys.stderr.write("---------------------------------\n")
        sys.stderr.write(f"Total messages: {len(messages)}\n")

        for status, count in status_counts.items():
            sys.stderr.write(f"Status '{status}': {count} messages\n")

        if past_due_messages:
            sys.stderr.write(f"\nPast due pending messages: {len(past_due_messages)}\n")
            if verbose:
                id_list = ", ".join(past_due_messages[:5])
                suffix = " ..." if len(past_due_messages) > 5 else ""
                sys.stderr.write(f"IDs: {id_list}{suffix}\n")

        if missing_metadata:
            sys.stderr.write(
                f"\nMessages with missing metadata: {len(missing_metadata)}\n"
            )
            if verbose:
                id_list = ", ".join(missing_metadata[:5])
                suffix = " ..." if len(missing_metadata) > 5 else ""
                sys.stderr.write(f"IDs: {id_list}{suffix}\n")

        if missing_chat_id:
            sys.stderr.write(
                f"\nMessages with missing chat_id: {len(missing_chat_id)}\n"
            )
            if verbose:
                id_list = ", ".join(missing_chat_id[:5])
                suffix = " ..." if len(missing_chat_id) > 5 else ""
                sys.stderr.write(f"IDs: {id_list}{suffix}\n")

        if failed_messages:
            sys.stderr.write(f"\nFailed messages: {len(failed_messages)}\n")
            if verbose:
                id_list = ", ".join(failed_messages[:5])
                suffix = " ..." if len(failed_messages) > 5 else ""
                sys.stderr.write(f"IDs: {id_list}{suffix}\n")

        if has_issues:
            sys.stderr.write(
                "\nFound data quality issues in scheduled messages. Consider running fix_scheduled_messages.py.\n"
            )
        else:
            sys.stderr.write("\nNo data quality issues found in scheduled messages.\n")

        # Only output json data to stdout for parsing
        print(
            json.dumps(
                {
                    "success": True,
                    "has_issues": has_issues,
                    "issues_found": has_issues,
                    "total": len(messages),
                    "past_due_messages": len(past_due_messages),
                    "missing_metadata": len(missing_metadata),
                    "missing_chat_id": len(missing_chat_id),
                    "failed_messages": len(failed_messages),
                    "due_time_column": due_time_column,
                }
            )
        )

    issues_data = {
        "missing_metadata": missing_metadata,
        "missing_chat_id": missing_chat_id,
        "failed_messages": failed_messages,
        "past_due_messages": past_due_messages,
    }

    return has_issues, issues_data


if __name__ == "__main__":
    args = parse_args()
    has_issues, _ = check_scheduled_messages(
        args.verbose, args.json, args.supabase_url, args.supabase_key
    )
    sys.exit(1 if has_issues else 0)
