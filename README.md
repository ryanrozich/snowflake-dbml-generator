# Snowflake DBML Generator

The Snowflake DBML Generator is an open-source tool that translates Snowflake database schemas into DBML (Database Markup Language), facilitating easy generation of ER diagrams and comprehensive documentation of database structures. 

For data engineers, analysts, and ML engineers, it enables you to bootstrap a rich interactive DB diagram directly from Snowflake.

![Demo Install and Usage](docs/images/demo-final.svg)

## Quick Start

```bash
pip install snowflake-dbml-generator
snowflake-dbml --interactive
```

## Examples

Using [Snowflake's Sample Data Sets](https://docs.snowflake.com/en/user-guide/sample-data), here are demonstrations of generating DBML and visualizing it with dbdiagram.io:

### 1. Snowflake TPCH SF100 Dataset

![TPCH SF100 Dataset Diagram](docs/images/dbdocs_Sample_TPCH_SF100.svg)
- [ER Diagram on dbdiagram.io](https://dbdiagram.io/d/snowflake_sample-TPCH_SF100-6631d8395b24a634d03a1d8e)
- [Snowflake Dataset Documentation](https://docs.snowflake.com/en/user-guide/sample-data-tpch.html)

### 2. Snowflake TPCDS SF100TCL Dataset
![TPCDS SF100TCL Dataset Diagram](docs/images/dbdocs_Sample_TPCDS_SF100TCL.svg)

- [ER Diagram on dbdiagram.io](https://dbdiagram.io/d/snowflake_sample-tpcds_sf100tcl-6631078d5b24a634d02fbd57)
- [Snowflake Dataset Documentation](https://docs.snowflake.com/en/user-guide/sample-data-tpcds.html)

## Features

- **Automatic DBML Generation**: Converts Snowflake schema definitions into DBML automatically.
- **Complex Schema Support**: Manages complex relationships, including composite foreign keys.
- **Interactive Mode**: Guides through configuration file generation and database connection setup.
- **Customizable Visualization**: Allows customization of DBML file appearances with configurable color schemes.
- **SQL Comments Extraction**: Extracts SQL table and column comments as DBML notes.
- **Table Statistics**: Includes table statistics like row count and size in bytes in the DBML output.

## Installation

### Prerequisites
- Python 3.6+
- Snowflake account credentials

### Install from PyPI
```bash
pip install snowflake-dbml-generator
```

### Build from Source
```bash
git clone https://github.com/ryanrozich/snowflake-dbml-generator.git
cd snowflake-dbml-generator
pip install -e .
```

## Usage

### Command Line Interface
Run the generator via the command line. For detailed usage, see [Configuration Parameters](docs/Configuration_Parameters.md).

```bash
snowflake-dbml --user <username> --password <password> --account <account_id> --warehouse <warehouse> --database <database> --role <role>
```

### Interactive Mode
For guided setup:

```bash
snowflake-dbml --interactive
```

## Configuration Parameters

Configuration can be set via environment variables, a `.env` file, or command-line arguments. [Learn more about setting configuration parameters.](docs/Configuration_Parameters.md)

## Configuration File

For advanced setups, particularly when Snowflake does not enforce foreign key relationships, a `config.json` file can define how relationships are inferred. See [Configuring Relationships](docs/Configuring_Relationships.md) for detailed setup.

### Generating DBML

To generate a DBML file after setting up your configuration:

```bash
snowflake-dbml --config-file config.json > output.dbml
```

## Contributing

Contributions are welcome! Whether it's tweaking code, enhancing documentation, or reporting bugs, we'd love to see your pull requests. Let's make this tool even better together!

## License

Licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Ryan Rozich - [GitHub](https://github.com/ryanrozich)

## Acknowledgments