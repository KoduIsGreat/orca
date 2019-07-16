#PW:=$(shell cat ~/.pypipw)

VERSION=0.5.4-dev1

sdist:
	echo "name = 'amanzi.orca'" > orca/__init__.py
	echo "__version__ = '$(VERSION)'" >> orca/__init__.py
	python3 setup.py sdist

#upload: sdist
#	twine upload -r pypi -p $(PW) dist/orca-$(VERSION).tar.gz

install: sdist
	pip3 install dist/orca-$(VERSION).tar.gz

uninstall:
	pip3 uninstall -y orca

clean:
	rm -rf dist *.egg-info tests/fixtures/configs/.dot
	
demo:
	python3 orca run -v comprehensive_example.yaml arg1 test 300

run:
	python3 orca run -v $(file)
	
test:
	python3 -m unittest tests/integration/*_test.py
	python3 -m unittest tests/unit/*_test.py
#	python3 -m unittest tests/fixtures/configs/*_test.py

test_docs:
	(cd docs && mkdocs serve)
	
format:
	find . -name '*.py' -exec autopep8 --in-place '{}' \;

