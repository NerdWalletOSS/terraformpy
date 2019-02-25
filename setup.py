from setuptools import find_packages, setup

with open('VERSION') as version_fd:
    VERSION = version_fd.read().strip()

setup(
    name='terraformpy',
    version=VERSION,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'schematics>=1.1.1,<3.0',
        'six>=1.11,<2'
    ],
    entry_points={
        'console_scripts': [
            'terraformpy = terraformpy.cli:main',
        ],
    },
)
