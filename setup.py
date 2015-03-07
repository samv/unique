from setuptools import find_packages, setup


try:
    with open("README.rst", "ro") as readme:
        lines = []
        for line in readme:
            lines.append(line)
            if "...and much more" in line:
                break
        long_description = "".join(lines)
except:
    long_description = """
This module implements a B-Tree store for normalize objects, backed by git.
"""


setup(
    author='Sam Vilain',
    author_email='sam@vilain.net',
    description="Unique/Primary Key Index Store for normalize objects",
    license='MIT',
    long_description=long_description,
    name='unique',
    packages=find_packages(),
    install_requires=('richenum>=1.0.0', 'normalize>=0.7.4'),
    test_suite="run_tests",
    version='0.0.1',
    url="http://github.io/samv/unique",
)
