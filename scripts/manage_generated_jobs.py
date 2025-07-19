#!/usr/bin/env python3
"""
Generated Jobs Management Script
Manages cleanup and archival of generated Kubernetes job files.
"""

import os
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

class GeneratedJobsManager:
    def __init__(self, generated_dir: str = "k8s/generated", archive_dir: str = "k8s/archived"):
        self.generated_dir = Path(generated_dir)
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(exist_ok=True)
    
    def list_generated_jobs(self) -> List[Path]:
        """List all generated job files"""
        if not self.generated_dir.exists():
            return []
        
        return list(self.generated_dir.glob("*.yaml"))
    
    def get_job_info(self, job_file: Path) -> dict:
        """Get information about a job file"""
        stat = job_file.stat()
        return {
            "name": job_file.name,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "age_days": (datetime.now() - datetime.fromtimestamp(stat.st_ctime)).days
        }
    
    def cleanup_old_jobs(self, days: int = 7, dry_run: bool = True) -> List[Path]:
        """Clean up jobs older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        old_jobs = []
        
        for job_file in self.list_generated_jobs():
            job_info = self.get_job_info(job_file)
            if job_info["created"] < cutoff_date:
                old_jobs.append(job_file)
                if not dry_run:
                    job_file.unlink()
                    print(f"🗑️  Deleted: {job_file.name}")
        
        if dry_run and old_jobs:
            print(f"📋 Would delete {len(old_jobs)} jobs older than {days} days:")
            for job in old_jobs:
                job_info = self.get_job_info(job)
                print(f"  - {job.name} (created {job_info['age_days']} days ago)")
        elif not old_jobs:
            print(f"✅ No jobs older than {days} days found")
        
        return old_jobs
    
    def archive_jobs(self, job_names: Optional[List[str]] = None, dry_run: bool = True) -> List[Path]:
        """Archive specific jobs or all jobs"""
        jobs_to_archive = []
        
        if job_names:
            # Archive specific jobs
            for name in job_names:
                job_file = self.generated_dir / name
                if job_file.exists():
                    jobs_to_archive.append(job_file)
                else:
                    print(f"⚠️  Job not found: {name}")
        else:
            # Archive all jobs
            jobs_to_archive = self.list_generated_jobs()
        
        archived_jobs = []
        for job_file in jobs_to_archive:
            archive_path = self.archive_dir / job_file.name
            if not dry_run:
                shutil.move(str(job_file), str(archive_path))
                print(f"📦 Archived: {job_file.name}")
                archived_jobs.append(archive_path)
            else:
                print(f"📦 Would archive: {job_file.name}")
        
        return archived_jobs
    
    def restore_jobs(self, job_names: List[str], dry_run: bool = True) -> List[Path]:
        """Restore jobs from archive"""
        restored_jobs = []
        
        for name in job_names:
            archive_file = self.archive_dir / name
            if archive_file.exists():
                restore_path = self.generated_dir / name
                if not dry_run:
                    shutil.move(str(archive_file), str(restore_path))
                    print(f"🔄 Restored: {name}")
                    restored_jobs.append(restore_path)
                else:
                    print(f"🔄 Would restore: {name}")
            else:
                print(f"⚠️  Archived job not found: {name}")
        
        return restored_jobs
    
    def show_status(self):
        """Show status of generated and archived jobs"""
        generated_jobs = self.list_generated_jobs()
        archived_jobs = list(self.archive_dir.glob("*.yaml")) if self.archive_dir.exists() else []
        
        print("=== Generated Jobs Status ===")
        print(f"Generated jobs: {len(generated_jobs)}")
        print(f"Archived jobs: {len(archived_jobs)}")
        
        if generated_jobs:
            print("\n📁 Generated Jobs:")
            for job_file in sorted(generated_jobs):
                job_info = self.get_job_info(job_file)
                print(f"  - {job_file.name} ({job_info['age_days']} days old, {job_info['size']} bytes)")
        
        if archived_jobs:
            print("\n📦 Archived Jobs:")
            for job_file in sorted(archived_jobs):
                job_info = self.get_job_info(job_file)
                print(f"  - {job_file.name} (archived {job_info['age_days']} days ago)")
    
    def cleanup_completed_jobs(self, dry_run: bool = True) -> List[Path]:
        """Clean up jobs that have been completed in Kubernetes"""
        import subprocess
        
        completed_jobs = []
        
        for job_file in self.list_generated_jobs():
            # Extract job name from filename (remove timestamp)
            job_name = job_file.stem.split('-', 1)[1] if '-' in job_file.stem else job_file.stem
            
            try:
                # Check if job exists and is completed
                result = subprocess.run([
                    'kubectl', 'get', 'job', job_name, '-n', 'trading-system', 
                    '--no-headers', '-o', 'custom-columns=:.status.conditions[0].type'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and 'Complete' in result.stdout:
                    completed_jobs.append(job_file)
                    if not dry_run:
                        job_file.unlink()
                        print(f"✅ Deleted completed job: {job_file.name}")
                    else:
                        print(f"✅ Would delete completed job: {job_file.name}")
                        
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                # Job might not exist or be accessible
                pass
        
        return completed_jobs

def main():
    parser = argparse.ArgumentParser(description="Manage generated Kubernetes job files")
    parser.add_argument("--action", choices=["status", "cleanup", "archive", "restore", "cleanup-completed"], 
                       default="status", help="Action to perform")
    parser.add_argument("--days", type=int, default=7, help="Age threshold for cleanup (days)")
    parser.add_argument("--jobs", nargs="+", help="Specific job names to archive/restore")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    parser.add_argument("--force", action="store_true", help="Force action (disable dry-run)")
    
    args = parser.parse_args()
    
    manager = GeneratedJobsManager()
    
    if args.action == "status":
        manager.show_status()
    
    elif args.action == "cleanup":
        if args.force:
            args.dry_run = False
        manager.cleanup_old_jobs(days=args.days, dry_run=args.dry_run)
    
    elif args.action == "archive":
        if args.force:
            args.dry_run = False
        manager.archive_jobs(job_names=args.jobs, dry_run=args.dry_run)
    
    elif args.action == "restore":
        if not args.jobs:
            print("❌ Error: Must specify job names to restore")
            return
        if args.force:
            args.dry_run = False
        manager.restore_jobs(job_names=args.jobs, dry_run=args.dry_run)
    
    elif args.action == "cleanup-completed":
        if args.force:
            args.dry_run = False
        manager.cleanup_completed_jobs(dry_run=args.dry_run)

if __name__ == "__main__":
    main() 