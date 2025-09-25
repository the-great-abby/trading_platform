# Portfolio Management System Linting Configuration
# Extends existing trading system linting rules

# Import base configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Portfolio-specific linting rules
PORTFOLIO_LINT_RULES = {
    # Portfolio optimization specific
    "portfolio_optimization": {
        "max_function_length": 100,
        "max_parameters": 8,
        "allow_complex_math": True,
        "require_docstrings": True,
        "require_type_hints": True,
    },
    
    # Risk management specific
    "risk_management": {
        "max_function_length": 80,
        "require_error_handling": True,
        "require_validation": True,
        "require_logging": True,
    },
    
    # API endpoints
    "api_endpoints": {
        "max_function_length": 50,
        "require_async": True,
        "require_response_models": True,
        "require_error_handling": True,
    },
    
    # Database models
    "database_models": {
        "require_table_names": True,
        "require_indexes": True,
        "require_constraints": True,
        "require_migrations": True,
    }
}

# File-specific rules
FILE_RULES = {
    "src/portfolio/optimization/*.py": PORTFOLIO_LINT_RULES["portfolio_optimization"],
    "src/portfolio/risk/*.py": PORTFOLIO_LINT_RULES["risk_management"],
    "services/*/api/*.py": PORTFOLIO_LINT_RULES["api_endpoints"],
    "src/portfolio/models/*.py": PORTFOLIO_LINT_RULES["database_models"],
}

# Import rules for portfolio modules
IMPORT_RULES = {
    "cvxpy": "Use cvxpy for convex optimization",
    "PyPortfolioOpt": "Use PyPortfolioOpt for portfolio utilities",
    "QuantLib": "Use QuantLib for quantitative finance calculations",
    "numpy": "Use numpy for numerical computations",
    "pandas": "Use pandas for data manipulation",
    "sqlalchemy": "Use SQLAlchemy for database operations",
    "fastapi": "Use FastAPI for REST API endpoints",
}

