.PHONY: all


PROJECT_FOLDER = django_partisan
WORKING_DIRECTORY = $(shell pwd)


coverage_html: go_to_project_folder coverage_run coverage_html_report
coverage_simple: go_to_project_folder coverage_run coverage_cmd_report
make_checks: go_to_project_folder check_black check_mypy
make_all_checks: go_to_project_folder coverage_run coverage_cmd_report make_checks

go_to_project_folder:
	cd $(WORKING_DIRECTORY)

# Tools section
run_black:
	poetry run black -S $(PROJECT_FOLDER)

# Tests section
run_tests:
	poetry run test_partisan/manage.py test $(PROJECT_FOLDER)

# Linters section
check_black:
	poetry run black -S --diff --check $(PROJECT_FOLDER)

check_mypy:
	poetry run mypy $(PROJECT_FOLDER)

# Coverage section
coverage_run:
	poetry run coverage run test_partisan/manage.py test $(PROJECT_FOLDER)

coverage_html_report:
	poetry run coverage html

coverage_cmd_report:
	poetry run coverage report

