#!/usr/bin/env python3
"""
Session Startup Script
Quickly get up to speed on our project
"""

import os
import subprocess
from datetime import datetime
from typing import Dict, List

class SessionStartup:
    """Quick startup for new development sessions"""
    
    def __init__(self):
        self.learnings_file = "docs/team_learnings.md"
        self.todo_file = "TODO.md"
        self.blockers_file = "docs/blockers/today.md"
        
    def quick_status(self):
        """Show quick status of current work"""
        print("🚀 Quick Session Startup")
        print("=" * 40)
        
        # Check if we have learnings document
        if os.path.exists(self.learnings_file):
            print("✅ Team learnings document found")
        else:
            print("❌ Team learnings document missing")
        
        # Check current blockers
        if os.path.exists(self.blockers_file):
            with open(self.blockers_file, 'r') as f:
                blockers = f.read()
                if blockers.strip():
                    print("\n🚨 Active Blockers:")
                    print(blockers[-300:])  # Last 300 chars
                else:
                    print("\n✅ No active blockers")
        else:
            print("\n✅ No blockers file found")
        
        # Check TODO status
        if os.path.exists(self.todo_file):
            print("\n📋 TODO Status:")
            with open(self.todo_file, 'r') as f:
                todo_content = f.read()
                # Count unchecked items
                unchecked = todo_content.count('- [ ]')
                checked = todo_content.count('- [x]')
                print(f"  Pending: {unchecked} items")
                print(f"  Completed: {checked} items")
        else:
            print("\n❌ TODO.md not found")
    
    def show_priorities(self):
        """Show current priorities"""
        print("\n🎯 Current Priorities:")
        print("=" * 30)
        
        priorities = [
            "1. Fix RabbitMQ syntax errors",
            "2. Set up basic testing infrastructure", 
            "3. Implement differential coverage debugging",
            "4. Focus on critical areas: trading engine, risk management",
            "5. Optimize resource usage for development"
        ]
        
        for priority in priorities:
            print(f"  {priority}")
    
    def show_preferences(self):
        """Show our working preferences"""
        print("\n🤝 Working Preferences:")
        print("=" * 30)
        
        preferences = [
            "• Direct communication (no excessive agreement)",
            "• Container-only development",
            "• Resource-conscious approach",
            "• Practical over theoretical",
            "• Immediate logging of progress/blockers",
            "• Risk-based testing priorities"
        ]
        
        for pref in preferences:
            print(f"  {pref}")
    
    def show_learnings(self):
        """Show key learnings"""
        print("\n📚 Key Learnings:")
        print("=" * 30)
        
        learnings = [
            "• Port standardization: 11000-11999 range for external access",
            "• Differential coverage great for debugging",
            "• Critical lack of tests in the system",
            "• RabbitMQ has syntax errors to fix",
            "• Focus on critical areas first (trading engine, risk management)"
        ]
        
        for learning in learnings:
            print(f"  {learning}")
    
    def quick_commands(self):
        """Show useful commands for this session"""
        print("\n⚡ Quick Commands:")
        print("=" * 30)
        
        commands = [
            "make -f Makefile.simple status          # Check current status",
            "make -f Makefile.simple critical        # Show critical areas",
            "make -f Makefile.simple debug           # Show debugging workflow",
            "python scripts/simple_collaboration.py sync  # Quick sync",
            "docker-compose -f docker-compose.dev.yml up  # Start dev environment",
            "make -f Makefile.test test              # Run tests"
        ]
        
        for cmd in commands:
            print(f"  {cmd}")
    
    def check_critical_issues(self):
        """Check for critical issues that need immediate attention"""
        print("\n🚨 Critical Issues Check:")
        print("=" * 30)
        
        # Check for RabbitMQ syntax error
        rabbitmq_file = "src/services/queue/rabbitmq_service.py"
        if os.path.exists(rabbitmq_file):
            with open(rabbitmq_file, 'r') as f:
                content = f.read()
                if 'IndentationError' in content or 'indentation' in content.lower():
                    print("  ❌ RabbitMQ syntax error detected")
                else:
                    print("  ✅ RabbitMQ syntax looks good")
        else:
            print("  ❓ RabbitMQ file not found")
        
        # Check test coverage
        test_files = [
            "tests/unit/test_rabbitmq_service.py",
            "tests/unit/test_trading_engine.py"
        ]
        
        missing_tests = []
        for test_file in test_files:
            if not os.path.exists(test_file):
                missing_tests.append(test_file)
        
        if missing_tests:
            print(f"  ❌ Missing test files: {len(missing_tests)}")
        else:
            print("  ✅ Basic test files present")
        
        # Check docker setup
        docker_files = [
            "docker-compose.dev.yml",
            "docker-compose.test.yml"
        ]
        
        missing_docker = []
        for docker_file in docker_files:
            if not os.path.exists(docker_file):
                missing_docker.append(docker_file)
        
        if missing_docker:
            print(f"  ❌ Missing docker files: {len(missing_docker)}")
        else:
            print("  ✅ Docker setup looks good")
    
    def run_full_startup(self):
        """Run complete startup sequence"""
        print("🚀 Starting new development session...")
        print("=" * 50)
        
        self.quick_status()
        self.show_priorities()
        self.show_preferences()
        self.show_learnings()
        self.check_critical_issues()
        self.quick_commands()
        
        print("\n" + "=" * 50)
        print("✅ Session startup complete!")
        print("💡 Tip: Use 'make -f Makefile.simple status' for quick updates")


def main():
    """Main function"""
    import sys
    
    startup = SessionStartup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        startup.quick_status()
    else:
        startup.run_full_startup()


if __name__ == "__main__":
    main() 