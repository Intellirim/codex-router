#!/usr/bin/env python3
"""
Build validation script for codex-router.
Ensures all required files exist and basic imports work.
"""
import sys
import os
from pathlib import Path

def validate_file_structure():
    """Verify all required files exist."""
    required_files = [
        "README.md",
        "LICENSE",
        ".gitignore",
        "pyproject.toml",
        "codex_router/__init__.py",
        "codex_router/cli.py",
        "codex_router/router.py",
        "codex_router/orchestrator.py",
        "codex_router/providers.py",
        "codex_router/tracker.py",
        "codex_router/config.py",
        "codex_router/display.py",
        "tests/test_router.py",
        "tests/test_tracker.py",
        "tests/test_config.py",
        "tests/test_providers.py",
    ]

    project_root = Path(__file__).parent
    missing = []

    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing.append(file_path)

    if missing:
        print("ERROR: Missing required files:")
        for f in missing:
            print(f"  - {f}")
        return False

    print("✓ All required files present")
    return True

def validate_imports():
    """Verify basic imports work."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))

        import codex_router
        from codex_router import cli, router, orchestrator, providers, tracker, config, display

        print("✓ All modules import successfully")
        return True
    except ImportError as e:
        print(f"ERROR: Import failed: {e}")
        return False

def validate_pyproject():
    """Verify pyproject.toml has required fields."""
    project_root = Path(__file__).parent
    pyproject_path = project_root / "pyproject.toml"

    try:
        with open(pyproject_path, 'rb') as f:
            if sys.version_info >= (3, 11):
                import tomllib
                data = tomllib.load(f)
            else:
                # Fallback for older Python - just check file exists
                print("✓ pyproject.toml exists (version check skipped for Python < 3.11)")
                return True

        # Check required fields
        if 'project' not in data:
            print("ERROR: pyproject.toml missing [project] section")
            return False

        required_fields = ['name', 'version', 'dependencies']
        missing = [f for f in required_fields if f not in data['project']]

        if missing:
            print(f"ERROR: pyproject.toml missing fields: {missing}")
            return False

        if 'project.scripts' not in str(data) and 'scripts' not in data.get('project', {}):
            print("WARNING: pyproject.toml may be missing [project.scripts] entry point")

        print("✓ pyproject.toml structure valid")
        return True
    except Exception as e:
        print(f"ERROR: Failed to validate pyproject.toml: {e}")
        return False

def main():
    """Run all validation checks."""
    print("Running build validation for codex-router...\n")

    checks = [
        ("File Structure", validate_file_structure),
        ("Python Imports", validate_imports),
        ("pyproject.toml", validate_pyproject),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        result = check_func()
        results.append(result)

    print("\n" + "=" * 50)
    if all(results):
        print("✓ All validation checks PASSED")
        return 0
    else:
        print("✗ Some validation checks FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
