import setuptools
import orca

setuptools.setup(
    name="orca",
    version=orca.__version__,
    author="Adam Shelton, Olaf David",
    author_email="",
    install_requires=[
        "csip ==  0.8.13",
        "jsonschema == 2.0",
        "click == 7.0",
        "click-log == 0.3.2",
        "dotted == 0.1.8",
        "ruamel.yaml == 0.15.88",
        "pymongo == 3.7.2",
        "requests == 2.21.0",
        "pykafka == 2.8.0" 
    ],
    description="A cli tool for orchestrating model workflows",
    long_description=open('README.md').read(),
    url="https://github.com/KoduIsGreat/orca.git",
    packages=setuptools.find_packages(),
    entry_points={
        'setuptools.installation': [
            'eggsecutable = orca.cli.commands:orca'
        ],
        'console_scripts': [
            'orca=orca.cli.commands:orca'
        ]
    },
    classifiers=[
        "License :: GNU License",
        "Command Line Interface"
    ]
)
