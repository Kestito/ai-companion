import asyncio
import logging
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Try to import Supabase client directly
try:
    from supabase import create_client, Client

    # Hardcoded Supabase credentials from settings.py
    SUPABASE_URL = "https://aubulhjfeszmsheonmpy.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc"

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

except ImportError as e:
    logger.error(f"Failed to import Supabase client: {e}")
    supabase = None


async def test_supabase_direct():
    """Direct test of Supabase connection and data retrieval."""
    logger.info("Testing direct Supabase connection...")

    if not supabase:
        logger.error("Supabase client not available")
        return

    test_patient_ids = [
        "ee0b625d-a5d7-4c6d-8179-28a9c1b548fc",
        "38592401-8cc1-4559-9a14-ef146e1aa4ea",
    ]

    try:
        # Test a basic query first
        try:
            logger.info("Testing basic query...")
            result = supabase.table("short_term_memory").select("id").limit(1).execute()
            logger.info(f"Basic query result: {result.data}")
        except Exception as e:
            logger.error(f"Basic query failed: {e}")
            logger.error(traceback.format_exc())

        # Test queries for each patient
        for patient_id in test_patient_ids:
            try:
                logger.info(f"\n=== Getting messages for patient {patient_id} ===")
                result = (
                    supabase.table("short_term_memory")
                    .select("*")
                    .eq("patient_id", patient_id)
                    .order("id", desc=True)
                    .limit(5)
                    .execute()
                )

                if not result.data:
                    logger.info(f"No messages found for patient {patient_id}")
                    continue

                logger.info(f"Found {len(result.data)} messages")

                # Format and print each message
                for i, record in enumerate(result.data, 1):
                    logger.info(f"\nMessage {i}:")
                    logger.info(f"Record ID: {record.get('id')}")

                    # Print the context
                    context = record.get("context")
                    if isinstance(context, dict):
                        # If context is already a dictionary
                        logger.info(
                            f"Context is a dictionary with keys: {list(context.keys())}"
                        )

                        # Try to extract content
                        if "content" in context:
                            content = context["content"]
                            preview = (
                                str(content)[:100] + "..."
                                if len(str(content)) > 100
                                else str(content)
                            )
                            logger.info(f"Content: {preview}")

                        # Try to extract metadata
                        if "metadata" in context:
                            logger.info(f"Metadata: {context['metadata']}")
                    else:
                        # If context is not a dictionary (e.g., a string or integer)
                        logger.info(f"Context (raw): {context}")

            except Exception as e:
                logger.error(f"Error querying patient {patient_id}: {e}")
                logger.error(traceback.format_exc())

    except Exception as e:
        logger.error(f"Test failed: {e}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_supabase_direct())
