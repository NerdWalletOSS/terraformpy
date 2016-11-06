from setuptools import setup, find_packages


setup(
    name='terraformpy',
    version='0.0.1',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'click==6.6',
        'sh==1.11',
    ],
    entry_points={
        'console_scripts': [
            'terraformpy = terraformpy.cli:main',
        ],
    },
)
