import logging

# Set logging level to suppress debug logs
logging.basicConfig(level=logging.WARNING)

try:
    print("Trying to import from ai_companion.graph.nodes")
    from ai_companion.graph.nodes import get_patient_id_from_platform_id

    print(
        "Successfully imported get_patient_id_from_platform_id from ai_companion.graph.nodes"
    )
except ImportError as e:
    print(f"Error importing from ai_companion.graph.nodes: {e}")

try:
    print("\nTrying to import from ai_companion.graph.utils.nodes")
    from ai_companion.graph.utils.nodes import get_patient_id_from_platform_id

    print(
        "Successfully imported get_patient_id_from_platform_id from ai_companion.graph.utils.nodes"
    )
except ImportError as e:
    print(f"Error importing from ai_companion.graph.utils.nodes: {e}")

# Try to list directories to understand the actual structure
import os

print("\nChecking directory structure:")
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"Project root: {project_root}")
graph_path = os.path.join(project_root, "src", "ai_companion", "graph")
print(f"Graph path: {graph_path}")
if os.path.exists(graph_path):
    print("Contents of graph directory:")
    for item in os.listdir(graph_path):
        print(f"  - {item}")
else:
    print(f"Graph path does not exist: {graph_path}")
