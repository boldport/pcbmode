from setuptools import setup, find_packages
setup(
    name = "pcbmode",
    packages = find_packages(),
    use_scm_version=True,
    setup_requires=['setuptools_scm'],

    install_requires = ['lxml', 'pyparsing'],

    package_data = {
        'pcbmode': ['stackups/*.json',
                    'styles/*/*.json',
                    'fonts/*.svg'],
    },

    # metadata for upload to PyPI
    author = "Saar Drimer",
    author_email = "saardrimer@gmail.com",
    description = "A printed circuit board design tool with a twist",
    license = "MIT",
    keywords = "pcb svg eda pcbmode",
    url = "https://github.com/boldport/pcbmode",

    entry_points={
        'console_scripts': ['pcbmode = pcbmode.pcbmode:main']
    },
    zip_safe = True
)

