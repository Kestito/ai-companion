#!/usr/bin/env python
"""
Deploy the optimized search_documents function and text search indexes to Supabase.

This script provides a step-by-step guide to deploying the search functionality
to Supabase, with validation and detailed instructions.
"""

import os
import logging
from dotenv import load_dotenv
import subprocess
import platform
import webbrowser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def generate_sql_script():
    """Generate the optimized SQL script for search indexes and function."""
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
        output_file_path = os.path.join(project_root, "supabase_search_indexes.sql")
        
        # Write the SQL function to the output file
        with open(output_file_path, "w") as f:
            f.write(sql_function)
        
        logger.info(f"SQL script written to {output_file_path}")
        return output_file_path
    except Exception as e:
        logger.error(f"Error generating SQL script: {e}")
        return None

def validate_environment_variables():
    """Validate that required environment variables are set."""
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file or environment")
        return False
    
    return True

def open_supabase_sql_editor():
    """Attempt to open the Supabase SQL Editor in the default browser."""
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        return False
    
    # Extract the project ID from the URL
    # Example URL: https://aubulhjfeszmsheonmpy.supabase.co
    parts = supabase_url.split('.')
    if len(parts) >= 3:
        project_id = parts[0].split('//')[1]
        sql_editor_url = f"https://app.supabase.com/project/{project_id}/sql"
        
        try:
            logger.info(f"Opening Supabase SQL Editor at {sql_editor_url}")
            webbrowser.open(sql_editor_url)
            return True
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
            return False
    
    return False

def copy_to_clipboard(text):
    """Copy text to clipboard based on the operating system."""
    try:
        system = platform.system()
        
        if system == 'Windows':
            # Windows
            cmd = 'clip'
            subprocess.run(cmd, input=text.encode('utf-8'), check=True)
            return True
        elif system == 'Darwin':
            # macOS
            cmd = 'pbcopy'
            subprocess.run(cmd, input=text.encode('utf-8'), check=True)
            return True
        elif system == 'Linux':
            # Linux with xclip
            cmd = 'xclip -selection clipboard'
            subprocess.run(cmd, input=text.encode('utf-8'), shell=True, check=True)
            return True
        else:
            logger.warning(f"Unsupported platform for clipboard: {system}")
            return False
    except Exception as e:
        logger.error(f"Failed to copy to clipboard: {e}")
        return False

def read_sql_file(file_path):
    """Read the SQL file content."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read SQL file: {e}")
        return None

def print_test_instructions():
    """Print instructions for testing the function."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        return
    
    print("\n" + "="*80)
    print("🧪 TEST INSTRUCTIONS:")
    print("After deploying the SQL, you can test it with this curl command:")
    print("\ncurl -X POST \\")
    print(f"  '{supabase_url}/rest/v1/rpc/search_documents' \\")
    print("  -H 'Content-Type: application/json' \\")
    print(f"  -H 'apikey: {supabase_key}' \\")
    print(f"  -H 'Authorization: Bearer {supabase_key}' \\")
    print("  -d '{\"query_text\": \"POLA\", \"limit_val\": 5}'")
    
    # Add PowerShell example for Windows users
    print("\nOr in PowerShell:")
    print("$headers = @{")
    print("    \"Content-Type\" = \"application/json\"")
    print(f"    \"apikey\" = \"{supabase_key}\"")
    print(f"    \"Authorization\" = \"Bearer {supabase_key}\"")
    print("}")
    print("$body = @{")
    print("    query_text = \"POLA\"")
    print("    limit_val = 5")
    print("} | ConvertTo-Json")
    print(f"Invoke-RestMethod -Method Post -Uri \"{supabase_url}/rest/v1/rpc/search_documents\" -Headers $headers -Body $body")
    print("="*80 + "\n")

def main():
    """Main function to deploy Supabase indexes and search function."""
    logger.info("Starting deployment of Supabase search indexes and function...")
    
    # Validate environment
    if not validate_environment_variables():
        logger.error("Environment validation failed. Please check your .env file.")
        print("\n❌ ERROR: Missing Supabase credentials in .env file.")
        print("Please ensure you have set SUPABASE_URL and SUPABASE_KEY in your .env file.")
        return False
    
    print("\n🔍 Checking environment variables... ✓")
    
    # Generate SQL script
    print("📝 Generating SQL script for Supabase deployment...")
    sql_file_path = generate_sql_script()
    if not sql_file_path:
        logger.error("SQL script generation failed.")
        print("❌ ERROR: Failed to generate SQL script.")
        return False
    
    print(f"✓ SQL script generated at: {sql_file_path}")
    
    # Read SQL content
    sql_content = read_sql_file(sql_file_path)
    if not sql_content:
        logger.error("Error reading SQL file.")
        print("❌ ERROR: Failed to read SQL content.")
        return False
    
    # Try to copy to clipboard
    print("📋 Copying SQL to clipboard...")
    clipboard_result = copy_to_clipboard(sql_content)
    if clipboard_result:
        logger.info("SQL script copied to clipboard!")
        print("✓ SQL script copied to clipboard!")
    else:
        print("⚠️ Could not copy to clipboard. You'll need to manually copy from the file.")
    
    # Try to open Supabase SQL Editor
    print("🌐 Opening Supabase SQL Editor in your browser...")
    browser_opened = open_supabase_sql_editor()
    if browser_opened:
        print("✓ Browser opened to Supabase SQL Editor!")
    else:
        print("⚠️ Could not open browser automatically.")
    
    # Print instructions
    print("\n" + "="*80)
    print("📋 DEPLOYMENT INSTRUCTIONS:")
    print("1. Go to the Supabase dashboard")
    print("2. Navigate to the SQL Editor")
    if not browser_opened:
        print("   - URL: https://app.supabase.com/project/[your-project-id]/sql")
    print("3. Create a new query")
    print("4. Paste the SQL content into the editor")
    if clipboard_result:
        print("   - The SQL has been copied to your clipboard (just press Ctrl+V or Cmd+V)")
    else:
        print(f"   - Copy the SQL from: {sql_file_path}")
    print("5. Run the query to create the indexes and function")
    print("6. Check for any errors in the output")
    print("\n👉 IMPORTANT: This will create or update these objects:")
    print("   - Text search index on document_chunks.chunk_content")
    print("   - Text search index on document_chunks.title")
    print("   - Index on document_chunks.document_id")
    print("   - The public.search_documents function")
    print("   - A test_search_function to verify installation")
    print("="*80 + "\n")
    
    # Print test instructions
    print_test_instructions()
    
    # Print verification instructions
    print("\n" + "="*80)
    print("✅ VERIFICATION INSTRUCTIONS:")
    print("After deploying the SQL, you can verify it works by running the following in the SQL Editor:")
    print("\nSELECT public.test_search_function('POLA');")
    print("\nYou should see a success message with the number of results found.")
    print("="*80 + "\n")
    
    print("\n🎉 Deployment preparation completed successfully!")
    print("Follow the instructions above to complete the deployment.")
    
    logger.info("Deployment preparation completed successfully!")
    return True

if __name__ == "__main__":
    main() 