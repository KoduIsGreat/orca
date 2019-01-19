import setuptools

with open("ReadMe.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="orca",
    version="0.0.1",
    author="Adam Shelton",
    author_email="",
    description="A cli tool for orchestrating model workflows",
    long_description=long_description,
    url="https://github.com/KoduIsGreat/orca.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: GNU License",
        "Command Line Interface"
    ]
)