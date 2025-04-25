import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Load environment variables
load_dotenv()


def check_scheduled_messages() -> Dict[str, Any]:
    """
    Checks for issues in scheduled messages and returns a summary of findings.

    Returns:
        Dict with information about issues found in scheduled messages.
    """
    try:
        # Import here to avoid dependencies if script is used standalone
        from supabase import create_client, Client

        # Get environment variables
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            return {
                "error": "Missing Supabase credentials. Please ensure SUPABASE_URL and SUPABASE_KEY environment variables are set.",
                "issues_found": False,
            }

        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        # Check for past due messages that are still in 'pending' status
        now = datetime.utcnow()
        past_due_result = (
            supabase.table("scheduled_messages")
            .select("id")
            .eq("status", "pending")
            .lte("due_time", now.isoformat())
            .execute()
        )
        past_due_messages = past_due_result.data if past_due_result.data else []

        # Check for messages with missing metadata
        missing_metadata_result = (
            supabase.table("scheduled_messages")
            .select("id")
            .is_("metadata", "null")
            .execute()
        )
        missing_metadata = (
            missing_metadata_result.data if missing_metadata_result.data else []
        )

        # Check for messages stuck in 'processing' status (older than 30 minutes)
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

        # Check for failed messages that could be retried
        failed_result = (
            supabase.table("scheduled_messages")
            .select("id")
            .eq("status", "failed")
            .execute()
        )
        failed_messages = failed_result.data if failed_result.data else []

        # Total number of issues
        total_issues = (
            len(past_due_messages)
            + len(missing_metadata)
            + len(stuck_processing)
            + len(failed_messages)
        )

        # Prepare result summary
        result = {
            "issues_found": total_issues > 0,
            "total_issues": total_issues,
            "past_due_pending": len(past_due_messages),
            "missing_metadata": len(missing_metadata),
            "stuck_processing": len(stuck_processing),
            "failed_messages": len(failed_messages),
            "timestamp": now.isoformat(),
        }

        return result

    except Exception as e:
        return {"error": str(e), "issues_found": False}


def main():
    """Main function to check scheduled messages and print results."""
    result = check_scheduled_messages()

    # Print as JSON for easier integration with PowerShell
    print(json.dumps(result, indent=2))

    if "error" in result:
        sys.exit(1)

    # Return exit code based on issues found
    if result.get("issues_found", False):
        sys.exit(100)  # Custom exit code for issues found
    else:
        sys.exit(0)  # No issues found


if __name__ == "__main__":
    main()
