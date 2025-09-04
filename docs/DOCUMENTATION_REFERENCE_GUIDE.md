# 📚 Documentation Reference System Guide

## Quick Start

The Documentation Reference rule automatically activates when you're creating or editing features. It helps you leverage the extensive documentation in `docs/` and `md/` directories.

### When It Activates
- **New feature development** - Creating new services, strategies, or components
- **Feature modifications** - Significant changes to existing functionality  
- **Architecture decisions** - System design or integration planning
- **Troubleshooting** - Debugging complex issues or performance problems

## Key Commands

### Search Documentation
```bash
# Find docs by keyword
find docs/ md/ -name "*.md" -exec grep -l "keyword" {} \;

# List all guides
ls docs/*_GUIDE.md md/*_GUIDE.md

# Find architecture docs
ls docs/ARCHITECTURE_*.md docs/APPLICATION_*.md
```

### Quick Access
```bash
# Open relevant docs for current feature
code docs/FEATURE_NAME_GUIDE.md

# View quick reference
code docs/QUICK_REFERENCE.md

# Check current status
code docs/CURRENT_STATUS_AND_NEXT_STEPS.md
```

## Documentation Structure

### Primary Documentation (`docs/`)
- **Architecture & Design**: `ARCHITECTURE_*.md`, `APPLICATION_*.md`
- **Feature Guides**: `*_GUIDE.md`, `*_STRATEGY_GUIDE.md`
- **System Operations**: `KUBERNETES_*.md`, `DEPLOYMENT.md`
- **Quick References**: `QUICK_REFERENCE*.md`, `*_REFERENCE.md`

### Secondary Documentation (`md/`)
- **Implementation Summaries**: `*_SUMMARY.md`, `*_REPORT.md`
- **Learning Materials**: `*_LEARNING_*.md`, `*_QUICKSTART.md`
- **Configuration Guides**: `*_CONFIGURATION.md`, `*_SETUP.md`

## Workflow Integration

### Before Starting New Features
1. **Search existing docs** for related functionality
2. **Review architecture docs** for system context
3. **Check implementation guides** for established patterns
4. **Identify knowledge gaps** that need documentation

### During Development
1. **Reference existing patterns** from docs
2. **Update relevant guides** as implementation progresses
3. **Document decisions** and rationale
4. **Create implementation notes** for complex logic

### After Completion
1. **Create comprehensive guides** for new features
2. **Update quick references** with new information
3. **Document lessons learned** and best practices
4. **Update status documents** with progress

## Example Usage

### Creating a New Trading Strategy
```bash
# 1. Research existing strategies
find docs/ md/ -name "*STRATEGY*" -exec grep -l "trading" {} \;

# 2. Review strategy guides
code docs/OPTIONS_STRATEGIES_GUIDE.md
code docs/ADVANCED_STRATEGIES_GUIDE.md

# 3. Check implementation patterns
code docs/STRATEGY_IMPROVEMENT_GUIDE.md

# 4. Create new strategy documentation
code docs/NEW_STRATEGY_GUIDE.md
```

### Setting Up New Service
```bash
# 1. Review architecture docs
code docs/APPLICATION_ARCHITECTURE_SUMMARY.md
code docs/KUBERNETES_FIRST_GUIDE.md

# 2. Check service patterns
code docs/SERVICE_REQUIREMENTS.md
code docs/CENTRALIZED_API_GUIDE.md

# 3. Review deployment guides
code docs/DEPLOYMENT.md
code docs/KUBERNETES_STABILITY_GUIDE.md
```

## Benefits

- **Faster development** - Leverage existing knowledge and patterns
- **Better decisions** - Access to historical context and rationale
- **Consistent implementation** - Follow established patterns
- **Knowledge preservation** - Document learnings for future reference
- **Reduced onboarding time** - Comprehensive documentation for new team members

## Integration with Other Rules

The Documentation Reference rule works with:
- **AI Development Assistant** - For complex features and code review
- **Trading** - For strategy development and backtesting
- **Infrastructure** - For deployment and system architecture
- **Python** - For code organization and best practices

This system ensures that your development process is informed by existing knowledge and that new knowledge is properly documented for future use.
