from setuptools import setup, find_namespace_packages

setup(
    name = "pcbmode",
    description = "A printed circuit board design tool with a twist",
    long_description = "",
    version = "5.0.0a1",
    license = "GPL 3.0",
    url = "https://pcbmode.com",

    author = "Saar Drimer",
    author_email = "saardrimer@gmail.com",
    keywords = "pcb svg eda pcbmode",

    python_requires = ">=3.7.0",

    packages=find_namespace_packages(include=['pcbmode.*']),

    test_suite='tests',

    install_requires = [
        'lxml>=4.4.0',
        'pyparsing>=2.4.2'
    ],

    package_data = {
        'pcbmode': [
            'stackups/*.json',
            'styles/*/*.json',
            'fonts/*.svg',
            'pcbmode_config.json'
        ],
    },

    entry_points={
        'console_scripts': [
            'pcbmode = pcbmode.pcbmode:main'
        ]
    }
)
