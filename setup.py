import os
from setuptools import setup, find_packages


try:
    with open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()
except:
    long_description = ''


setup(
    name='pretix-pages',
    version='1.0.1',
    description='pretix plugin that allows you to add static pages to your event site, for example for a FAQ, terms of service, etc.',
    long_description=long_description,
    url='https://github.com/pretix/pretix-pages',
    author='Raphael Michel',
    author_email='mail@raphaelmichel.de',

    install_requires=[],
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    entry_points="""
[pretix.plugin]
pretix_pages=pretix_pages:PretixPluginMeta
""",
)
