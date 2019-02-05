#PW:=$(shell cat ~/.pypipw)

VERSION=0.0.2

define INITPY
name = "orca"
__version__ = '$(VERSION)' 
endef

export INITPY

sdist:
	echo "$$INITPY" > orca/__init__.py
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
	python3 orca run -v wf.yaml arg1 test 300
