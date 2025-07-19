# Generated Jobs Management Strategy

## Overview

As you generate more Kubernetes jobs using the template system, you'll accumulate files in `k8s/generated/`. This document outlines strategies for managing these files effectively.

## 📁 File Organization

```
k8s/
├── generated/                    # Active generated jobs
│   ├── backtest-run_backtest-20250711_072959.yaml
│   ├── backtest-run_backtest-20250711_073107.yaml
│   └── ...
├── archived/                    # Archived jobs (optional)
│   └── ...
├── job-templates/               # Template files
│   └── base-job-template.yaml
└── [existing static files]      # Legacy files
```

## 🎯 Management Strategies

### Strategy 1: **Keep Generated Files** (Recommended for Development)

**Pros:**
- Easy to track what jobs were created
- Can reference successful configurations
- Version control shows job evolution
- Easy to reapply specific jobs

**Cons:**
- Directory grows over time
- Need periodic cleanup

**Best for:** Development, testing, debugging

### Strategy 2: **Archive After Completion**

**Pros:**
- Keeps generated directory clean
- Preserves job history
- Can restore if needed

**Cons:**
- Requires manual management
- Need to track what's archived

**Best for:** Production environments

### Strategy 3: **Delete After Completion**

**Pros:**
- Minimal disk usage
- Clean directory structure
- Jobs can be regenerated from templates

**Cons:**
- No job history
- Can't reference successful configurations
- Need to regenerate if needed

**Best for:** CI/CD pipelines, automated systems

## 🛠️ Management Tools

### 1. **Status Check**
```bash
# Check current status
make k8s-jobs-status

# Or directly
python3 scripts/manage_generated_jobs.py --action status
```

### 2. **Cleanup Old Jobs**
```bash
# Preview cleanup (dry run)
make k8s-jobs-cleanup DAYS=7

# Force cleanup
make k8s-jobs-cleanup-force DAYS=7

# Or directly
python3 scripts/manage_generated_jobs.py --action cleanup --days 7 --dry-run
python3 scripts/manage_generated_jobs.py --action cleanup --days 7 --force
```

### 3. **Archive Jobs**
```bash
# Preview archive (dry run)
make k8s-jobs-archive

# Force archive
make k8s-jobs-archive-force

# Archive specific jobs
python3 scripts/manage_generated_jobs.py --action archive --jobs job1.yaml job2.yaml --force
```

### 4. **Cleanup Completed Jobs**
```bash
# Preview cleanup of completed jobs (dry run)
make k8s-jobs-cleanup-completed

# Force cleanup of completed jobs
make k8s-jobs-cleanup-completed-force
```

## 📋 Recommended Workflow

### For Development/Testing

1. **Generate jobs as needed**
   ```bash
   make k8s-job-backtest SCRIPT=run_backtest.py APPLY=true
   ```

2. **Check status weekly**
   ```bash
   make k8s-jobs-status
   ```

3. **Cleanup old jobs monthly**
   ```bash
   make k8s-jobs-cleanup DAYS=30 --dry-run  # Preview
   make k8s-jobs-cleanup-force DAYS=30       # Execute
   ```

### For Production

1. **Generate jobs**
   ```bash
   make k8s-job-backtest SCRIPT=run_backtest.py APPLY=true
   ```

2. **Archive after completion**
   ```bash
   # After job completes successfully
   python3 scripts/manage_generated_jobs.py --action archive --jobs job-name.yaml --force
   ```

3. **Cleanup archived jobs quarterly**
   ```bash
   # Remove archived jobs older than 90 days
   find k8s/archived/ -name "*.yaml" -mtime +90 -delete
   ```

## 🔄 Migration from Static Jobs

### Phase 1: **Parallel Operation**
- Keep existing static job files
- Generate new jobs using templates
- Compare results and configurations

### Phase 2: **Gradual Migration**
- Archive successful static jobs
- Replace with template-generated versions
- Update documentation and scripts

### Phase 3: **Template-Only**
- Remove static job files
- Use only template system
- Maintain archive for reference

## 📊 Monitoring and Metrics

### Track Generated Jobs
```bash
# Count generated jobs
ls -1 k8s/generated/*.yaml | wc -l

# Check disk usage
du -sh k8s/generated/

# List jobs by age
find k8s/generated/ -name "*.yaml" -mtime +7 -ls
```

### Track Job Success
```bash
# Check completed jobs
kubectl get jobs -n trading-system --field-selector=status.successful=1

# Check failed jobs
kubectl get jobs -n trading-system --field-selector=status.failed=1
```

## 🎯 Best Practices

### 1. **Naming Conventions**
- Generated jobs include timestamps
- Use descriptive script names
- Include job type in filename

### 2. **Resource Management**
- Monitor disk usage
- Set cleanup schedules
- Archive important configurations

### 3. **Version Control**
- Commit template changes
- Don't commit generated files (add to .gitignore)
- Document successful configurations

### 4. **Documentation**
- Keep examples of successful jobs
- Document custom parameters
- Maintain troubleshooting guide

## 🔧 Automation

### Cron Job for Cleanup
```bash
# Add to crontab for weekly cleanup
0 2 * * 0 cd /path/to/project && make k8s-jobs-cleanup-force DAYS=7
```

### Git Hooks
```bash
# Pre-commit hook to check generated directory size
if [ $(find k8s/generated/ -name "*.yaml" | wc -l) -gt 100 ]; then
    echo "Warning: Many generated jobs found. Consider cleanup."
fi
```

## 🚨 Troubleshooting

### Common Issues

1. **Too Many Generated Files**
   ```bash
   # Quick cleanup
   make k8s-jobs-cleanup-force DAYS=1
   ```

2. **Need to Restore Archived Job**
   ```bash
   python3 scripts/manage_generated_jobs.py --action restore --jobs job-name.yaml --force
   ```

3. **Job Configuration Reference**
   ```bash
   # Find successful job configuration
   grep -r "successful_parameter" k8s/generated/
   ```

## 📈 Success Metrics

- **Clean Directory**: Generated directory stays manageable
- **Fast Access**: Quick job generation and application
- **No Duplication**: Template system prevents duplicate configurations
- **Easy Recovery**: Can regenerate jobs from templates
- **Version Control**: Template changes tracked, generated files not committed

This strategy ensures your Kubernetes job management remains efficient and maintainable as your system scales! 🎉 