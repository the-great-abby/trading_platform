#!/usr/bin/env python3
"""
Simple Collaboration Tools
For 2-person development team
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleCollaboration:
    """Simple collaboration tools for 2-person team"""
    
    def __init__(self):
        self.progress_file = "docs/progress/today.md"
        self.learnings_file = "docs/learnings/today.md"
        self.blockers_file = "docs/blockers/today.md"
        
        # Ensure directories exist
        os.makedirs("docs/progress", exist_ok=True)
        os.makedirs("docs/learnings", exist_ok=True)
        os.makedirs("docs/blockers", exist_ok=True)
    
    def log_progress(self, task: str, status: str, details: str = ""):
        """Log progress on a task"""
        timestamp = datetime.now().strftime("%H:%M")
        
        with open(self.progress_file, "a") as f:
            f.write(f"## {task} ({timestamp})\n")
            f.write(f"Status: {status}\n")
            if details:
                f.write(f"Details: {details}\n")
            f.write("\n")
        
        logger.info(f"📝 Progress logged: {task} - {status}")
    
    def log_learning(self, topic: str, discovery: str, impact: str):
        """Log a learning or discovery"""
        timestamp = datetime.now().strftime("%H:%M")
        
        with open(self.learnings_file, "a") as f:
            f.write(f"## {topic} ({timestamp})\n")
            f.write(f"Discovery: {discovery}\n")
            f.write(f"Impact: {impact}\n")
            f.write("\n")
        
        logger.info(f"💡 Learning logged: {topic}")
    
    def log_blocker(self, task: str, blocker: str, help_needed: str = ""):
        """Log a blocker that needs help"""
        timestamp = datetime.now().strftime("%H:%M")
        
        with open(self.blockers_file, "a") as f:
            f.write(f"## {task} ({timestamp})\n")
            f.write(f"Blocker: {blocker}\n")
            if help_needed:
                f.write(f"Help needed: {help_needed}\n")
            f.write("\n")
        
        logger.info(f"🚨 Blocker logged: {task} - {blocker}")
    
    def quick_status(self):
        """Show quick status of current work"""
        print("📊 Quick Status Check")
        print("=" * 30)
        
        # Check recent progress
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r") as f:
                recent_progress = f.read()
                if recent_progress.strip():
                    print("Recent Progress:")
                    print(recent_progress[-500:])  # Last 500 chars
                else:
                    print("No recent progress logged")
        
        # Check recent learnings
        if os.path.exists(self.learnings_file):
            with open(self.learnings_file, "r") as f:
                recent_learnings = f.read()
                if recent_learnings.strip():
                    print("\nRecent Learnings:")
                    print(recent_learnings[-500:])
                else:
                    print("\nNo recent learnings logged")
        
        # Check active blockers
        if os.path.exists(self.blockers_file):
            with open(self.blockers_file, "r") as f:
                active_blockers = f.read()
                if active_blockers.strip():
                    print("\nActive Blockers:")
                    print(active_blockers[-500:])
                else:
                    print("\nNo active blockers")
    
    def quick_sync(self):
        """Quick sync questions"""
        questions = [
            "What are you working on right now?",
            "Any blockers or issues?",
            "Any discoveries or learnings?",
            "What's your next priority?"
        ]
        
        print("🤝 Quick Sync Questions:")
        print("=" * 30)
        for i, question in enumerate(questions, 1):
            print(f"{i}. {question}")
        
        print("\n💡 Tip: Use these commands to log:")
        print("  python scripts/simple_collaboration.py progress <task> <status>")
        print("  python scripts/simple_collaboration.py learning <topic> <discovery>")
        print("  python scripts/simple_collaboration.py blocker <task> <blocker>")
    
    def identify_critical_areas(self):
        """Identify critical areas that need testing"""
        critical_areas = {
            'trading_engine': {
                'priority': 10,
                'risk': 'High - Core business logic',
                'change_frequency': 'High',
                'testing_status': 'Needs work'
            },
            'risk_management': {
                'priority': 9,
                'risk': 'High - Financial safety',
                'change_frequency': 'Medium',
                'testing_status': 'Needs work'
            },
            'order_execution': {
                'priority': 8,
                'risk': 'High - Customer impact',
                'change_frequency': 'High',
                'testing_status': 'Needs work'
            },
            'market_data': {
                'priority': 7,
                'risk': 'Medium - Data integrity',
                'change_frequency': 'High',
                'testing_status': 'Needs work'
            },
            'authentication': {
                'priority': 9,
                'risk': 'High - Security',
                'change_frequency': 'Low',
                'testing_status': 'Needs work'
            }
        }
        
        print("🎯 Critical Areas for Testing:")
        print("=" * 40)
        
        # Sort by priority
        sorted_areas = sorted(critical_areas.items(), 
                            key=lambda x: x[1]['priority'], reverse=True)
        
        for area, details in sorted_areas:
            print(f"\n{area.upper()}")
            print(f"  Priority: {details['priority']}/10")
            print(f"  Risk: {details['risk']}")
            print(f"  Change Frequency: {details['change_frequency']}")
            print(f"  Testing Status: {details['testing_status']}")
    
    def quick_debug_workflow(self):
        """Quick debugging workflow"""
        workflow = [
            "1. Reproduce the bug consistently",
            "2. Write a minimal test case",
            "3. Use differential coverage to find location",
            "4. Fix the bug",
            "5. Verify the fix works",
            "6. Document what was wrong and how you fixed it"
        ]
        
        print("🐛 Quick Debugging Workflow:")
        print("=" * 30)
        for step in workflow:
            print(f"  {step}")
        
        print("\n💡 Tip: Use differential coverage when tests fail:")
        print("  - Run passing tests to get coverage")
        print("  - Run failing test to get coverage")
        print("  - Compare to find unique code paths")
        print("  - Focus debugging on those paths")


def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/simple_collaboration.py status")
        print("  python scripts/simple_collaboration.py sync")
        print("  python scripts/simple_collaboration.py critical")
        print("  python scripts/simple_collaboration.py debug")
        print("  python scripts/simple_collaboration.py progress <task> <status>")
        print("  python scripts/simple_collaboration.py learning <topic> <discovery>")
        print("  python scripts/simple_collaboration.py blocker <task> <blocker>")
        return
    
    collab = SimpleCollaboration()
    command = sys.argv[1]
    
    if command == "status":
        collab.quick_status()
    elif command == "sync":
        collab.quick_sync()
    elif command == "critical":
        collab.identify_critical_areas()
    elif command == "debug":
        collab.quick_debug_workflow()
    elif command == "progress" and len(sys.argv) >= 4:
        task = sys.argv[2]
        status = sys.argv[3]
        details = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        collab.log_progress(task, status, details)
    elif command == "learning" and len(sys.argv) >= 4:
        topic = sys.argv[2]
        discovery = sys.argv[3]
        impact = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else "Improved development"
        collab.log_learning(topic, discovery, impact)
    elif command == "blocker" and len(sys.argv) >= 4:
        task = sys.argv[2]
        blocker = sys.argv[3]
        help_needed = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        collab.log_blocker(task, blocker, help_needed)
    else:
        print("Invalid command or missing arguments")


if __name__ == "__main__":
    main() 