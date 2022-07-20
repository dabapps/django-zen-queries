#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from setuptools import setup
import re
import os
import sys


name = "django-zen-queries"
package = "zen_queries"
description = "Explicit control over query execution in Django applications."
url = "https://github.com/dabapps/django-zen-queries"
author = "DabApps"
author_email = "hello@dabapps.com"
license = "BSD"

with open("README.md") as f:
    readme = f.read()


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, "__init__.py")).read()
    return re.search("^__version__ = ['\"]([^'\"]+)['\"]", init_py, re.MULTILINE).group(
        1
    )


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [
        dirpath
        for dirpath, dirnames, filenames in os.walk(package)
        if os.path.exists(os.path.join(dirpath, "__init__.py"))
    ]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [
        (dirpath.replace(package + os.sep, "", 1), filenames)
        for dirpath, dirnames, filenames in os.walk(package)
        if not os.path.exists(os.path.join(dirpath, "__init__.py"))
    ]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename) for filename in filenames])
    return {package: filepaths}


if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    args = {"version": get_version(package)}
    print("You probably want to also tag the version now:")
    print("  git tag -a %(version)s -m 'version %(version)s'" % args)
    print("  git push --tags")
    sys.exit()


setup(
    name=name,
    version=get_version(package),
    url=url,
    license=license,
    description=description,
    long_description=readme,
    long_description_content_type="text/markdown",
    author=author,
    author_email=author_email,
    packages=get_packages(package),
    package_data=get_package_data(package),
    python_requires=">=3.6",
    install_requires=[
        "Django>=3.2",
    ],
    project_urls={
        "Changelog": "https://github.com/dabapps/django-zen-queries/releases",
        "Issues": "https://github.com/dabapps/django-zen-queries/issues",
    }
)
