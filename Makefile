appname = slackchannel2pdf
package = slackchannel2pdf

help:
	@echo "Makefile for $(appname)"

coverage:
	coverage run -m unittest discover -v && coverage html && coverage report

test:
	coverage run -m unittest -v tests.test_channel_exporter.TestSlackChannelExporter.test_should_handle_team_name_with_invalid_characters

pylint:
	pylint $(package)

check_complexity:
	flake8 $(package) --max-complexity=10

flake8:
	flake8 $(package) --count

deploy:
	rm dist/*
	python setup.py sdist
	twine upload dist/*
