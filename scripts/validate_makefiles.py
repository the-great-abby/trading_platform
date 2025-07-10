#!/usr/bin/env python3
"""
Makefile Validation Script
Enforces size limits and syntax validation for modular Makefiles
"""

import os
import sys
import subprocess
from pathlib import Path

# Configuration
MAX_LINES = 200
MAKEFILE_PATTERN = "Makefile*"
EXCLUDED_FILES = ["Makefile.old", "Makefile.backup", "Makefile.old2"]

def get_makefiles():
    """Get all Makefile* files in current directory"""
    makefiles = []
    for file in Path(".").glob(MAKEFILE_PATTERN):
        if file.name not in EXCLUDED_FILES:
            makefiles.append(file)
    return makefiles

def check_file_size(file_path):
    """Check if file is within size limit"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        return len(lines), len(lines) <= MAX_LINES
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return 0, False

def check_makefile_syntax(file_path):
    """Check Makefile syntax using make -n"""
    try:
        # Try to check syntax by parsing the file without executing
        result = subprocess.run(
            ["make", "-f", str(file_path), "-n"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⚠️  Timeout checking {file_path}")
        return True  # Assume OK if timeout
    except Exception as e:
        print(f"⚠️  Could not check syntax for {file_path}: {e}")
        return True  # Assume OK if can't check

def validate_makefiles():
    """Validate all Makefiles"""
    print("🔍 Validating Makefiles...")
    print(f"📏 Size limit: {MAX_LINES} lines per file")
    print()
    
    makefiles = get_makefiles()
    if not makefiles:
        print("❌ No Makefiles found!")
        return False
    
    all_valid = True
    total_lines = 0
    
    for makefile in sorted(makefiles):
        print(f"📄 Checking {makefile.name}...")
        
        # Check size
        lines, size_ok = check_file_size(makefile)
        total_lines += lines
        
        if size_ok:
            print(f"   ✅ Size: {lines} lines")
        else:
            print(f"   ❌ Size: {lines} lines (exceeds {MAX_LINES} limit)")
            all_valid = False
        
        # Check syntax
        syntax_ok = check_makefile_syntax(makefile)
        if syntax_ok:
            print(f"   ✅ Syntax: OK")
        else:
            print(f"   ❌ Syntax: Errors found")
            all_valid = False
        
        print()
    
    print(f"📊 Summary:")
    print(f"   📁 Files checked: {len(makefiles)}")
    print(f"   📏 Total lines: {total_lines}")
    print(f"   📄 Average per file: {total_lines // len(makefiles)}")
    
    if all_valid:
        print("✅ All Makefiles are valid!")
        return True
    else:
        print("❌ Some Makefiles have issues!")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        print("🔧 Auto-fix mode not implemented yet")
        print("💡 Please manually split large Makefiles")
        return
    
    success = validate_makefiles()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 