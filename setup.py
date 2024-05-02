from setuptools import setup, find_packages

setup(
    name='snowflake-dbml-generator',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'snowflake-dbml=snowflake_dbml.generator:main',
        ],
    },
    author='Ryan Rozich',
    author_email='github@rozich.com',
    description='Automatically generate DBML files from Snowflake databases.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ryanrozich/snowflake-dbml-generator',
    install_requires=[
        'snowflake-connector-python>=3.9.0',  # Connect to Snowflake
        'python-dotenv>=1.0.1',               # For loading environment variables from .env files
        'pydbml>=0.1.11'                       # Generate DBML files
    ],
    classifiers=[
        # Classifiers can help people find your project
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ]
)