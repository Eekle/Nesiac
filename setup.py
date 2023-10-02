from setuptools import setup, find_packages

setup(
    name="Nesiac",
    version="0.2",
    description="Compiled arm binary analysis",
    author="Eekle",
    packages=find_packages(),
    python_requires=">3.10",
    entry_points={"console_scripts": ["nesiac=nesiac.cli:cli"]},
    install_requires=["rich", "pyelftools", "cpp-demangle"],
)
