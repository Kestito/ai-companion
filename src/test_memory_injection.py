import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Import memory injection node
from ai_companion.graph.nodes import memory_injection_node


async def test_memory_injection():
    """Test memory injection node using sample patient IDs."""
    logger.info("Starting memory injection test")

    # Test both patient IDs we found in the Supabase database
    test_patient_ids = [
        "38592401-8cc1-4559-9a14-ef146e1aa4ea",  # Has valid messages in format with content
        "ee0b625d-a5d7-4c6d-8179-28a9c1b548fc",  # Has the numeric "222" as context
    ]

    # Create a minimal state object with patient_id and empty messages
    for patient_id in test_patient_ids:
        logger.info(f"\n===== Testing injection for patient {patient_id} =====")

        # Create a minimal state with the patient ID
        state = {
            "patient_id": patient_id,
            "messages": [],  # No messages needed for this test
        }

        # Call the memory injection node
        try:
            result = await memory_injection_node(state)

            # Check if we got a memory context
            memory_context = result.get("memory_context", "")

            if memory_context:
                logger.info(
                    f"Memory injection successful! Got {len(memory_context)} characters of context"
                )
                logger.info("Memory context:")
                logger.info("=" * 50)
                logger.info(memory_context)
                logger.info("=" * 50)
            else:
                logger.warning("Memory injection returned empty context")

        except Exception as e:
            logger.error(f"Error during memory injection: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_memory_injection())
