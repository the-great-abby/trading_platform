# Trading Platform - Main Makefile
# Clean, organized structure with no duplicate targets

# Include clean, organized Makefiles
include makefiles/Makefile.main
include makefiles/Makefile.simple
include makefiles/Makefile.services
include makefiles/Makefile.kubernetes
include makefiles/Makefile.port-forward
include makefiles/Makefile.backtest
include makefiles/Makefile.build
include makefiles/Makefile.test
include makefiles/Makefile.live-trading
include makefiles/Makefile.paper-trading
include makefiles/Makefile.validation
include makefiles/Makefile.secrets

# Standalone Makefiles (not in makefiles/ directory)
-include Makefile.order-sync

# Include semantic versioning system
include Makefile.versioning

# Default target
.DEFAULT_GOAL := help