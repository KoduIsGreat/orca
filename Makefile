#PW:=$(shell cat ~/.pypipw)

VERSION=0.2.0

sdist:
	echo "name = 'orca'" > orca/__init__.py
	echo "__version__ = '$(VERSION)'" >> orca/__init__.py
	python3 setup.py sdist

#upload: sdist
#	twine upload -r pypi -p $(PW) dist/orca-$(VERSION).tar.gz

install: sdist
	pip3 install dist/orca-$(VERSION).tar.gz

uninstall:
	pip3 uninstall -y orca

clean:
	rm -rf dist *.egg-info
	
demo:
	python3 orca run -v comprehensive_example.yaml arg1 test 300

run:
	python3 orca run -v $(file) 
