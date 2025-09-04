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

# Default target
.DEFAULT_GOAL := help