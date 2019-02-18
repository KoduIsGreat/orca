import setuptools
import orca

setuptools.setup(
    name="orca",
    version=orca.__version__,
    author="Adam Shelton",
    author_email="",
    install_requires=[
        "argparse == 1.4.0",
        "pyyaml == 4.2b1",
        "requests == 2.21.0",
        "csip ==  0.8.13",
        "jsonschema == 2.0",
        "click == 7.0",
        "dotted == 0.1.8",
        "docker == 3.7.0"
    ],
    description="A cli tool for orchestrating model workflows",
    long_description=open('README.md').read(),
    url="https://github.com/KoduIsGreat/orca.git",
    packages=setuptools.find_packages(),
    entry_points={
        'setuptools.installation': [
            'eggsecutable = orca.cli:orca'
        ]
    },
    classifiers=[
        "License :: GNU License",
        "Command Line Interface"
    ]
)
