# Risk Management Linting Configuration

# Black Configuration
black_config = {
    "line-length": 88,
    "target-version": ["py311"],
    "include": r'\.pyi?$',
    "exclude": r'''
    /(
        \.eggs
      | \.git
      | \.hg
      | \.mypy_cache
      | \.tox
      | \.venv
      | _build
      | buck-out
      | build
      | dist
      | \.pytest_cache
    )/
    ''',
}

# Flake8 Configuration
flake8_config = {
    "max-line-length": 88,
    "extend-ignore": ["E203", "W503", "E501"],
    "exclude": [
        ".git",
        "__pycache__",
        "build",
        "dist",
        ".venv",
        ".eggs",
        "*.egg",
        ".pytest_cache",
        ".mypy_cache",
    ],
    "per-file-ignores": {
        "__init__.py": ["F401"],  # Allow unused imports in __init__.py
        "tests/*": ["S101", "S106", "S108"],  # Allow assert and hardcoded values in tests
        "src/risk/services/*": ["PLR0913", "PLR0912"],  # Allow many parameters and branches in services
    },
}

# Pylint Configuration
pylint_config = {
    "max-line-length": 88,
    "disable": [
        "too-few-public-methods",
        "too-many-arguments",
        "too-many-locals",
        "too-many-branches",
        "too-many-statements",
        "too-many-instance-attributes",
        "too-many-public-methods",
        "duplicate-code",
        "import-outside-toplevel",
        "consider-using-f-string",
        "unnecessary-lambda",
        "no-member",  # False positives with SQLAlchemy
        "not-callable",  # False positives with Pydantic
    ],
    "good-names": [
        "i", "j", "k", "ex", "e", "f", "g", "h", "n", "m", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        "df", "dt", "id", "db", "var", "cv", "es", "mv", "cv", "std", "mean", "max", "min", "sum", "len", "str",
        "api", "url", "uri", "json", "xml", "html", "css", "js", "sql", "sqlite", "mysql", "postgresql",
        "var_95", "var_99", "es_95", "es_99", "cv_95", "cv_99",  # Risk management specific
        "pct", "pct_change", "returns", "volatility", "correlation", "beta", "alpha", "sharpe", "sortino",
        "drawdown", "max_drawdown", "portfolio_value", "position_value", "risk_metrics", "stress_test",
    ],
    "ignore-paths": [
        r"tests/.*",
        r"\.venv/.*",
        r"build/.*",
        r"dist/.*",
        r"\.eggs/.*",
        r"\.git/.*",
        r"\.pytest_cache/.*",
        r"\.mypy_cache/.*",
    ],
    "load-plugins": [
        "pylint.extensions.mccabe",
        "pylint.extensions.docparams",
        "pylint.extensions.typing",
    ],
}

# MyPy Configuration
mypy_config = {
    "python_version": "3.11",
    "warn_return_any": True,
    "warn_unused_configs": True,
    "disallow_untyped_defs": True,
    "disallow_incomplete_defs": True,
    "check_untyped_defs": True,
    "disallow_untyped_decorators": True,
    "no_implicit_optional": True,
    "warn_redundant_casts": True,
    "warn_unused_ignores": True,
    "warn_no_return": True,
    "warn_unreachable": True,
    "strict_equality": True,
    "show_error_codes": True,
    "show_column_numbers": True,
    "show_error_context": True,
    "pretty": True,
    "error_summary": True,
    "ignore_missing_imports": True,  # For external libraries
    "plugins": [
        "pydantic.mypy",
        "sqlalchemy.ext.mypy.plugin",
    ],
    "exclude": [
        "tests/",
        ".venv/",
        "build/",
        "dist/",
        ".eggs/",
        ".git/",
        ".pytest_cache/",
        ".mypy_cache/",
    ],
    "per_module_options": {
        "src.risk.services.*": {
            "disallow_untyped_defs": False,  # Allow untyped in service layer for flexibility
        },
        "src.risk.models.*": {
            "disallow_untyped_defs": True,  # Strict typing for models
        },
        "tests.*": {
            "disallow_untyped_defs": False,  # Allow untyped in tests
        },
    },
}

# Risk Management Specific Rules
risk_management_rules = {
    "naming_conventions": {
        "var_confidence_levels": ["var_95", "var_99", "es_95", "es_99"],
        "risk_metrics": ["var", "es", "cv", "volatility", "beta", "sharpe", "sortino", "calmar"],
        "stress_scenarios": ["market_crash", "rate_shock", "volatility_spike", "sector_rotation", "options_decay"],
        "correlation_metrics": ["correlation_matrix", "concentration_risk", "diversification_ratio"],
        "compliance_terms": ["audit_trail", "trade_documentation", "regulatory_checks"],
        "alert_levels": ["warning", "breach", "critical"],
        "limit_types": ["position_size", "daily_loss", "sector_concentration", "var_limit", "volatility_limit"],
    },
    "performance_targets": {
        "var_calculation": "<5s for 50+ assets",
        "stress_testing": "<30s for comprehensive scenarios",
        "correlation_analysis": "<10s for portfolio analysis",
        "memory_usage": "<100MB per risk calculation",
    },
    "validation_rules": {
        "var_values": "must be non-negative",
        "confidence_levels": "must be between 0.5 and 0.999",
        "portfolio_volatility": "must be between 0 and 10 (1000% max)",
        "maximum_drawdown": "must be between 0 and 1 (100% max)",
        "position_weights": "must be between 0 and 1",
        "correlation_values": "must be between -1 and 1",
    },
}

