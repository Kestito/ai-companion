import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Load environment variables
load_dotenv()


def fix_scheduled_messages(fix_types: List[str] = None) -> Dict[str, Any]:
    """
    Fixes issues with scheduled messages.

    Args:
        fix_types: List of issues to fix. Options: 'past_due', 'missing_metadata', 'stuck_processing', 'failed'
                  If None, fixes all issues.

    Returns:
        Dict with information about fixes applied.
    """
    if fix_types is None:
        fix_types = ["past_due", "missing_metadata", "stuck_processing", "failed"]

    try:
        # Import here to avoid dependencies if script is used standalone
        from supabase import create_client, Client

        # Get environment variables
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            return {
                "error": "Missing Supabase credentials. Please ensure SUPABASE_URL and SUPABASE_KEY environment variables are set.",
                "fixes_applied": 0,
            }

        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        now = datetime.utcnow()
        fixes_applied = 0
        fixes_by_type = {}

        # Fix past due messages that are still in 'pending' status
        if "past_due" in fix_types:
            past_due_result = (
                supabase.table("scheduled_messages")
                .select("id")
                .eq("status", "pending")
                .lte("due_time", now.isoformat())
                .execute()
            )
            past_due_messages = past_due_result.data if past_due_result.data else []

            if past_due_messages:
                message_ids = [msg["id"] for msg in past_due_messages]
                # Update messages to reset due_time to now + 5 minutes
                new_due_time = (now + timedelta(minutes=5)).isoformat()
                supabase.table("scheduled_messages").update(
                    {"due_time": new_due_time}
                ).in_("id", message_ids).execute()

                fixes_applied += len(past_due_messages)
                fixes_by_type["past_due"] = len(past_due_messages)

        # Fix messages with missing metadata
        if "missing_metadata" in fix_types:
            missing_metadata_result = (
                supabase.table("scheduled_messages")
                .select("id")
                .is_("metadata", "null")
                .execute()
            )
            missing_metadata = (
                missing_metadata_result.data if missing_metadata_result.data else []
            )

            if missing_metadata:
                message_ids = [msg["id"] for msg in missing_metadata]
                # Add empty metadata object
                default_metadata = {"fixed_at": now.isoformat()}
                supabase.table("scheduled_messages").update(
                    {"metadata": default_metadata}
                ).in_("id", message_ids).execute()

                fixes_applied += len(missing_metadata)
                fixes_by_type["missing_metadata"] = len(missing_metadata)

        # Fix messages stuck in 'processing' status
        if "stuck_processing" in fix_types:
            thirty_min_ago = (now - timedelta(minutes=30)).isoformat()
            stuck_processing_result = (
                supabase.table("scheduled_messages")
                .select("id")
                .eq("status", "processing")
                .lte("updated_at", thirty_min_ago)
                .execute()
            )
            stuck_processing = (
                stuck_processing_result.data if stuck_processing_result.data else []
            )

            if stuck_processing:
                message_ids = [msg["id"] for msg in stuck_processing]
                # Reset to pending and set due_time to now + 10 minutes
                new_due_time = (now + timedelta(minutes=10)).isoformat()
                supabase.table("scheduled_messages").update(
                    {
                        "status": "pending",
                        "due_time": new_due_time,
                        "updated_at": now.isoformat(),
                    }
                ).in_("id", message_ids).execute()

                fixes_applied += len(stuck_processing)
                fixes_by_type["stuck_processing"] = len(stuck_processing)

        # Reset failed messages to pending
        if "failed" in fix_types:
            failed_result = (
                supabase.table("scheduled_messages")
                .select("id")
                .eq("status", "failed")
                .execute()
            )
            failed_messages = failed_result.data if failed_result.data else []

            if failed_messages:
                message_ids = [msg["id"] for msg in failed_messages]
                # Reset to pending and set due_time to now + 15 minutes
                new_due_time = (now + timedelta(minutes=15)).isoformat()
                supabase.table("scheduled_messages").update(
                    {
                        "status": "pending",
                        "due_time": new_due_time,
                        "updated_at": now.isoformat(),
                    }
                ).in_("id", message_ids).execute()

                fixes_applied += len(failed_messages)
                fixes_by_type["failed"] = len(failed_messages)

        # Prepare result summary
        result = {
            "fixes_applied": fixes_applied,
            "fixes_by_type": fixes_by_type,
            "timestamp": now.isoformat(),
        }

        return result

    except Exception as e:
        return {"error": str(e), "fixes_applied": 0}


def main():
    """Main function to fix scheduled messages and print results."""
    parser = argparse.ArgumentParser(description="Fix issues with scheduled messages")
    parser.add_argument(
        "--past-due", action="store_true", help="Fix past due pending messages"
    )
    parser.add_argument(
        "--missing-metadata",
        action="store_true",
        help="Fix messages with missing metadata",
    )
    parser.add_argument(
        "--stuck-processing",
        action="store_true",
        help="Fix messages stuck in processing state",
    )
    parser.add_argument(
        "--failed", action="store_true", help="Reset failed messages to pending"
    )
    parser.add_argument("--all", action="store_true", help="Fix all issues (default)")

    args = parser.parse_args()

    # Determine which fixes to apply
    fix_types = []
    if args.past_due:
        fix_types.append("past_due")
    if args.missing_metadata:
        fix_types.append("missing_metadata")
    if args.stuck_processing:
        fix_types.append("stuck_processing")
    if args.failed:
        fix_types.append("failed")

    # If no specific fixes selected or --all specified, fix everything
    if not fix_types or args.all:
        fix_types = None  # None means fix all

    result = fix_scheduled_messages(fix_types)

    # Print as JSON for easier integration with PowerShell
    print(json.dumps(result, indent=2))

    if "error" in result:
        sys.exit(1)
    else:
        sys.exit(0)  # Success


if __name__ == "__main__":
    main()
