# -*- coding: utf-8 -*-

import re
from setuptools import setup, find_packages
from etl import __version__ as VERSION

# with open('etl/__init__.py') as f:
#     VERSION = re.search(r'^__version__\s*=\s*\'(.*)\'', f.read(), re.M).group(1)

dependencies = [
    'azure-functions',
    'azure-storage-blob',
    'click',
    'gopro2gpx',
    'gpxpy',
    'moviepy',
    'pandas',
    'psycopg2-binary', # to avoid building psycopg2 from source
    'pyproj',
    'requests',
    'scipy',
    'shapely',
    'tqdm',
]
build_dependencies = dependencies + ['pytest-runner']
test_dependencies = [
    'pytest',
    'pytest-mock',
]
authors = [
    ('Clément Leroux', 'clement.leroux@gmail.com'),
    ('Raphaël Courivaud', 'r.courivaud@gmail.com'),
    ('Raphaëlle Bretrand-Lalo', 'r.bertrand.lalo@gmail.com'),
]
author_names = ', '.join(tup[0] for tup in authors)
author_emails = ', '.join(tup[1] for tup in authors)

setup_args = dict(
    name='etl',
    description='Plastic Origin ETL flow.',
    packages=find_packages(exclude=['docs', 'tests', 'azure', 'wip_devel', 'data']),
    url='https://github.com/surfriderfoundationeurope/etl',
    author=author_names,
    author_email=author_emails,
    install_requires=dependencies,
    python_requires='>=3.6,<3.8',
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'etl =  etl.etl_cli:cli',
        ],
    },
    version=VERSION,
    include_package_data=True,
)

setup(**setup_args)
