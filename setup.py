from setuptools import find_packages, setup

project_name = "llmapps"
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name=project_name,
    packages=find_packages("."), # [project_name, f"{project_name}.app", f"{project_name}.controller"],
    #package_dir={project_name: "src"},
    version="0.1.0",
    description="LLM Applications Factory",
    entry_points={
        'console_scripts': [
            # if you have any scripts in your package, list them here
            'llmapps=llmapps.main:main'
        ],
    },
    author="Yaron",
    author_email="yaron@gmail.com",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.9",
    install_requires=requirements,
)
