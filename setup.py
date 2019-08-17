from setuptools import find_packages, setup

with open('VERSION') as version_fd:
    VERSION = version_fd.read().strip()

with open('README.rst') as readme_fd:
    long_description = readme_fd.read()

setup(
    name='terraformpy',
    version=VERSION,
    author="Evan Borgstrom",
    author_email="eborgstrom@nerdwallet.com",
    description="Terraformpy is a library and command line tool to supercharge "
                "your Terraform configs using a full fledged Python environment!",
    long_description=long_description,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'schematics>=2.0,<3.0',
        'six>=1.11,<2'
    ],
    extras_require={
        'dev:python_version <= "2.7"': [
            'pytest>=4.6,<4.7',
        ],
        'dev:python_version > "3"': [
            'pytest>=5.0,<6',
        ]
    },
    entry_points={
        'console_scripts': [
            'terraformpy = terraformpy.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Pre-processors",
        "Topic :: System :: Systems Administration",
    ]
)
