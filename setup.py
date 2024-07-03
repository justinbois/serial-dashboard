from setuptools import setup, find_packages
from codecs import open
from os import path

__version__ = "0.1.2"

here = path.abspath(path.dirname(__file__))

# get the dependencies and installs
with open(path.join(here, "requirements.txt"), encoding="utf-8") as f:
    all_reqs = f.read().split("\n")

install_requires = [x.strip() for x in all_reqs if "git+" not in x]

# Need to also include click
install_requires.append('Click')

dependency_links = [
    x.strip().replace("git+", "") for x in all_reqs if x.startswith("git+")
]

# Entry points for click
entry_points = {
    'console_scripts': [
        'serialdashboard = serial_dashboard.scripts.serialdashboard:cli',
    ]
}

setup(
    name="serial_dashboard",
    version=__version__,
    description="Bokeh-based serial dashboard.",
    long_description="Bokeh-based serial dashboard.",
    url="https://github.com/justinbois/serial-dashboard",
    download_url="https://github.com/justinbois/serial-dashboard/tarball/" + __version__,
    license="BSD",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
    ],
    keywords="",
    packages=find_packages(exclude=["docs", "tests*"]),
    include_package_data=True,
    author="Justin Bois",
    install_requires=install_requires,
    entry_points=entry_points,
    dependency_links=dependency_links,
    author_email="bois@caltech.edu",
)
