"""
A simple test to verify settings for memory storage.
"""

from ai_companion.settings import settings
import os


def main():
    """
    Test if the settings are configured correctly for memory storage.
    """
    print("SHORT_TERM_MEMORY_DB_PATH:", settings.SHORT_TERM_MEMORY_DB_PATH)
    print(
        "Using in-memory database only"
        if settings.SHORT_TERM_MEMORY_DB_PATH == ":memory:"
        else "Still using file database"
    )

    # Check for existence of SQLite file
    data_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "short_term_memory.db"
    )
    print(f"SQLite file exists at {data_path}: {os.path.exists(data_path)}")

    # Print Supabase settings
    print("Supabase URL:", settings.supabase_url)
    print(
        "Supabase connection available:",
        bool(settings.supabase_url and settings.supabase_key),
    )


if __name__ == "__main__":
    main()
