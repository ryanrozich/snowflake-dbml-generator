# Configuration Parameters

The Snowflake DBML Generator can be configured through environment variables, a `.env` file, or command-line arguments, with the following order of precedence:

1. **Command-Line Arguments**: Override all other settings.
2. **.env File**: Overrides environment variables but can be overridden by command-line options.
3. **Environment Variables**: Default if no other settings are specified.

## Configuration Options

Below is a table of the available configuration parameters, their corresponding environment variable names, and command-line options. Optional parameters are marked with an asterisk (*).

| Environment Variable     | Description                                          | Command-Line Argument                 |
|--------------------------|------------------------------------------------------|---------------------------------------|
| `SNOWFLAKE_USER`         | Snowflake user name.                                 | `--user <username>`                   |
| `SNOWFLAKE_PASSWORD`     | Snowflake password.                                  | `--password <password>`               |
| `SNOWFLAKE_ACCOUNT`      | Snowflake account identifier.                        | `--account <account_id>`              |
| `SNOWFLAKE_WAREHOUSE`    | Snowflake warehouse name.                            | `--warehouse <warehouse>`             |
| `SNOWFLAKE_DATABASE`     | Snowflake database name.                             | `--database <database>`               |
| `SNOWFLAKE_ROLE`         | Snowflake user role.                                 | `--role <role>`                       |
| `INCLUDED_SCHEMAS`*      | Schemas to include, comma-separated.                 | `--included-schemas <schemas>`        |
| `EXCLUDED_SCHEMAS`*      | Schemas to exclude, comma-separated.                 | `--excluded-schemas <schemas>`        |
| `TABLE_COLOR`*           | Color for table headers in DBML.                     | `--table-color <hex_color>`           |
| `VIEW_COLOR`*            | Color for view headers in DBML.                      | `--view-color <hex_color>`            |
| `DYNAMIC_TABLE_COLOR`*   | Color for dynamic table headers in DBML.             | `--dynamic-table-color <hex_color>`   |
| `CONFIG_FILE`*           | Path to the config JSON file.                        | `--config-file <file_path>`           |

For detailed usage of each command-line option, use the help command:

```bash
snowflake-dbml --help
```
