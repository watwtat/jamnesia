#!/usr/bin/env python3
"""
Test runner for Jamnesia poker hand management system.

This script runs all test suites and provides a summary of results.
"""

import os
import sys
import unittest
from io import StringIO


def run_test_suite(test_module_name, description):
    """Run a specific test suite and return results"""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")

    # Import the test module
    try:
        test_module = __import__(test_module_name)
    except ImportError as e:
        print(f"❌ Failed to import {test_module_name}: {e}")
        return False, 0, 0

    # Create test loader and suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_module)

    # Run tests with custom result tracking
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)

    # Print results
    output = stream.getvalue()
    print(output)

    # Summary
    tests_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success = failures == 0 and errors == 0

    if success:
        print(f"✅ {description}: {tests_run} tests passed")
    else:
        print(
            f"❌ {description}: {failures} failures, {errors} errors out of {tests_run} tests"
        )

        # Print failure details
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")

        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")

    return success, tests_run, failures + errors


def main():
    """Main test runner function"""
    print("🧪 Jamnesia Test Suite")
    print("=" * 60)

    # Test suites to run
    test_suites = [
        ("test_poker_engine", "Poker Engine Tests"),
        ("test_models", "Database Models Tests"),
        ("test_app", "Flask Application Tests"),
        ("test_position", "Position Enum Tests"),
        ("test_template_position", "Position Template Tests"),
        ("test_replay", "Hand Replay Tests"),
    ]

    total_tests = 0
    total_failures = 0
    all_passed = True

    # Run each test suite
    for module_name, description in test_suites:
        success, tests_run, failures = run_test_suite(module_name, description)
        total_tests += tests_run
        total_failures += failures

        if not success:
            all_passed = False

    # Final summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")

    if all_passed:
        print(f"🎉 ALL TESTS PASSED!")
        print(f"   Total tests run: {total_tests}")
        print(f"   All {total_tests} tests successful")
        return_code = 0
    else:
        print(f"💥 SOME TESTS FAILED")
        print(f"   Total tests run: {total_tests}")
        print(f"   Failed tests: {total_failures}")
        print(
            f"   Success rate: {((total_tests - total_failures) / total_tests * 100):.1f}%"
        )
        return_code = 1

    print(f"\n{'='*60}")

    # Coverage reminder
    print("\n📋 Additional Testing Notes:")
    print("   • Run 'python -m coverage run run_tests.py' for coverage analysis")
    print("   • Use 'python -m pytest' for more detailed test reporting")
    print("   • Manual testing: 'python app.py' and visit http://localhost:8000")

    return return_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
