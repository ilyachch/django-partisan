.PHONY: all


PROJECT_FOLDER = django_partisan


coverage_html: coverage_run coverage_html_report
coverage_simple: coverage_run coverage_cmd_report

make_checks: check_black check_mypy

# Tests section
run_tests:
	test_partisan/manage.py test django_partisan

# Linters section

check_black:
	poetry run black -S --diff --check $(PROJECT_FOLDER)

check_mypy:
	poetry run mypy $(PROJECT_FOLDER)

# Coverage section
coverage_run:
	coverage run test_partisan/manage.py test django_partisan

coverage_html_report:
	coverage html

coverage_cmd_report:
	coverage report

