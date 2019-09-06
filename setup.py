import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

requires = [
    'gdal',
    'numpy'
]

setuptools.setup(
    name="SREMPy-landsat",
    version="1.0",
    author="Eduard Kazakov",
    author_email="ee.kazakov@gmail.com",
    description="Python realization of SREM algorithm for Landsat imagery",
    long_description=long_description,
    keywords='landsat, srem, atmospheric correction',
    long_description_content_type="text/markdown",
    url="https://github.com/silenteddie/SREMPy-landsat",
    install_requires=requires,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: ...",
        "Operating System :: OS Independent",
    ],
)