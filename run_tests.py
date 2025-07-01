#!/usr/bin/env python3
"""Test runner script with coverage reporting."""

import subprocess
import sys
import os
from pathlib import Path


def run_tests():
    """Run tests with coverage reporting."""
    print("🧪 Running Policy Enforcer Test Suite")
    print("=" * 50)
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Activate virtual environment
    venv_python = project_root / "venv" / "bin" / "python"
    if not venv_python.exists():
        print("❌ Virtual environment not found. Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
        return False
    
    try:
        # Run unit tests only for now (since integration tests require API keys)
        print("🔬 Running Unit Tests...")
        cmd = [
            str(venv_python), "-m", "pytest", 
            "tests/unit",
            "-v",
            "--cov=policy_enforcer",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing", 
            "--cov-report=xml",
            "--tb=short"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("\n📊 Test Results:")
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            print(f"📈 Coverage report generated in: {project_root}/htmlcov/index.html")
            return True
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_integration_tests():
    """Run integration tests (requires API keys)."""
    print("\n🔗 Running Integration Tests...")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ Skipping integration tests - OPENAI_API_KEY not set")
        return True
    
    venv_python = Path(__file__).parent / "venv" / "bin" / "python"
    
    try:
        cmd = [
            str(venv_python), "-m", "pytest",
            "tests/integration",
            "-v",
            "--tb=short",
            "-m", "not slow"  # Skip slow tests by default
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False


def main():
    """Main test runner."""
    if len(sys.argv) > 1 and sys.argv[1] == "--integration":
        success = run_integration_tests()
    elif len(sys.argv) > 1 and sys.argv[1] == "--all":
        success = run_tests() and run_integration_tests()
    else:
        success = run_tests()
    
    if success:
        print("\n🎉 Test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Test suite failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()