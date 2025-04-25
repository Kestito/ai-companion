#!/usr/bin/env python
"""
Run all the patient chat fix tests and verification.

This script will:
1. Run the standalone verification script
2. Run the integration tests

Usage:
    python run_tests.py
"""

import sys
import subprocess
import time


def print_header(message):
    """Print a header message."""
    print("\n" + "=" * 80)
    print(message.center(80))
    print("=" * 80 + "\n")


def run_command(command, description):
    """Run a command and print the result."""
    print_header(description)

    # Run the command
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    elapsed_time = time.time() - start_time

    # Print the output
    print(result.stdout)

    if result.stderr:
        print("ERRORS:")
        print(result.stderr)

    print(
        f"\nCommand completed in {elapsed_time:.2f} seconds with status code {result.returncode}"
    )
    return result.returncode


def main():
    """Run the tests."""
    print_header("PATIENT CHAT FIX VERIFICATION")
    print(
        "This script will run all the tests to verify the patient chat fix is working properly."
    )

    # Run the standalone verification script
    print("\nStep 1: Running the standalone verification script...")
    verify_code = run_command(
        "python tests/verify_patient_chat_fix.py", "STANDALONE VERIFICATION"
    )

    # Run the integration tests
    print("\nStep 2: Running the integration tests...")
    test_code = run_command(
        "pytest -xvs tests/integration/test_patient_chat.py", "INTEGRATION TESTS"
    )

    # Determine overall success
    if verify_code == 0 and test_code == 0:
        print_header("SUCCESS: ALL TESTS PASSED")
        print("The patient chat fix has been successfully applied and verified.")
        return 0
    else:
        print_header("ERROR: SOME TESTS FAILED")
        if verify_code != 0:
            print("- The standalone verification script failed.")
        if test_code != 0:
            print("- The integration tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
