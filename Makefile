.DEFAULT_GOAL := help

###################################################################################################
#
# HELP
#
###################################################################################################

# COLORS
RED    := $(shell tput -Txterm setaf 1)
GREEN  := $(shell tput -Txterm setaf 2)
WHITE  := $(shell tput -Txterm setaf 7)
YELLOW := $(shell tput -Txterm setaf 3)
RESET  := $(shell tput -Txterm sgr0)

# Add the following 'help' target to your Makefile
# And add help text after each target name starting with '\#\#'
# A category can be added with @category
HELP_HELPER = \
		%help; \
		while(<>) { push @{$$help{$$2 // 'options'}}, [$$1, $$3] if /^([a-zA-Z\-\%]+)\s*:.*\#\#(?:@([a-zA-Z\-\%]+))?\s(.*)$$/ }; \
		print "usage: make [target]\n\n"; \
		for (sort keys %help) { \
		print "${WHITE}$$_:${RESET}\n"; \
		for (@{$$help{$$_}}) { \
		$$sep = " " x (32 - length $$_->[0]); \
		print "  ${YELLOW}$$_->[0]${RESET}$$sep${GREEN}$$_->[1]${RESET}\n"; \
		}; \
		print "\n"; }

help: ##@help Prints help
	@perl -e '$(HELP_HELPER)' $(MAKEFILE_LIST)


###################################################################################################
#
# TASKS
#
###################################################################################################

.PHONY: check_style
check_style:  ## Check Python code style
	pycodestyle *.py brume --config .pycodestyle
	flake8 *.py brume --config .pycodestyle
	pylint --rcfile .pylintrc brume/*.py || true
