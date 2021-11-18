import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="biobb_remote",
    version="1.2.0",
    author="Biobb developers",
    author_email="gelpi@ub.edu",
    description="Biobb_remote is the Biobb module for remote execution via ssl.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="Bioinformatics Workflows BioExcel Compatibility",
    url="https://github.com/bioexcel/biobb_remote",
    project_urls={
        "Documentation": "http://biobb_remote.readthedocs.io/en/latest/",
        "Bioexcel": "https://bioexcel.eu/"
    },
    packages=setuptools.find_packages(exclude=['docs', 'test']),
    install_requires=[],
    python_requires='>=3',
    entry_points={
        "console_scripts": [
            "credentials = scripts.credentials:main",
            "scp_service = scripts.scp_service:main",
            "slurm_test = scripts.slurm_test:main",
            "ssh_command = scripts.ssh_command:main"
        ]
    },
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
    ),
)
