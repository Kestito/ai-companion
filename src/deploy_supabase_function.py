#!/usr/bin/env python
"""
Generate SQL for the search_documents function to be run in the Supabase SQL editor.

This script reads the SQL function definition from migrations/search_documents_function.sql
and outputs it to a file that can be copied and pasted into the Supabase SQL editor.
"""

import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def generate_sql_script():
    """Generate SQL script for the search_documents function."""
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the project root
        project_root = os.path.dirname(current_dir)
        # Path to the SQL file
        sql_file_path = os.path.join(project_root, "migrations", "search_documents_function.sql")
        
        # Read the SQL function definition
        with open(sql_file_path, "r") as f:
            sql_function = f.read()
        
        # Output file path
        output_file_path = os.path.join(project_root, "supabase_function.sql")
        
        # Write the SQL function to the output file
        with open(output_file_path, "w") as f:
            f.write(sql_function)
        
        logger.info(f"SQL function written to {output_file_path}")
        logger.info("Copy and paste this SQL into the Supabase SQL editor to create the function")
        
        # Print instructions
        print("\n" + "="*80)
        print("INSTRUCTIONS:")
        print("1. Go to the Supabase dashboard")
        print("2. Click on 'SQL Editor'")
        print("3. Create a new query")
        print(f"4. Copy and paste the contents of {output_file_path}")
        print("5. Run the query to create the function")
        print("="*80 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Error generating SQL script: {e}")
        return False

def print_test_instructions():
    """Print instructions for testing the function."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase URL or key not found in environment variables")
        return
    
    print("\n" + "="*80)
    print("TEST INSTRUCTIONS:")
    print("After deploying the function, you can test it with this curl command:")
    print("\ncurl -X POST \\")
    print(f"  '{supabase_url}/rest/v1/rpc/search_documents' \\")
    print("  -H 'Content-Type: application/json' \\")
    print(f"  -H 'apikey: {supabase_key}' \\")
    print(f"  -H 'Authorization: Bearer {supabase_key}' \\")
    print("  -d '{\"query_text\": \"POLA\", \"limit_val\": 5}'")
    print("="*80 + "\n")

if __name__ == "__main__":
    logger.info("Generating SQL script for the search_documents function...")
    if generate_sql_script():
        logger.info("SQL script generated successfully")
        print_test_instructions()
    else:
        logger.error("SQL script generation failed") 