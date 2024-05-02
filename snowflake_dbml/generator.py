# snowflake_dbml/generator.py
import argparse
import getpass
import os
from datetime import datetime
from collections import defaultdict
import snowflake.connector
from pydbml import PyDBML, Database
from pydbml.classes import Project, Table, Column, Reference, Note, TableGroup
from snowflake.connector import DictCursor
from snowflake_dbml.config import load_config, load_primary_key_hints, load_visualization_params

import logging

# Configure the logger for the module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the default logging level

# Handler setup is minimal; assume the caller will configure it.
logger.addHandler(logging.NullHandler())

def fetch_data(connection_params, included_schemas=None, excluded_schemas=None):
    """Fetch table metadata along with primary and foreign key information."""

    # If connection_params not passed, then load connection params from envvars
    if not connection_params:
        connection_params = load_config()

    # If included_schemas or excluded_schemas not passed, then load from connection_params
    if not included_schemas:
        included_schemas = connection_params.get('included_schemas')
    if not excluded_schemas:
        excluded_schemas = connection_params.get('excluded_schemas')

    # Validate required connection parameters
    required_params = ['user', 'password', 'account', 'warehouse', 'database', 'role']
    missing_params = [param for param in required_params if not connection_params.get(param)]
    if missing_params:
        raise ValueError(f"Missing required connection parameters: {', '.join(missing_params)}")    

    conn = snowflake.connector.connect(**connection_params)
    cursor = conn.cursor(DictCursor)

    # Construct schema filter for querying tables and columns
    schema_filter = ""
    if included_schemas:
        included_list = ','.join(f"'{schema.strip()}'" for schema in included_schemas.split(','))
        schema_filter += f" AND t.TABLE_SCHEMA IN ({included_list})"
    if excluded_schemas:
        excluded_list = ','.join(f"'{schema.strip()}'" for schema in excluded_schemas.split(','))
        schema_filter += f" AND t.TABLE_SCHEMA NOT IN ({excluded_list})"

    # Fetching table and column details
    table_query = f"""
    SELECT t.TABLE_SCHEMA, t.TABLE_NAME, t.TABLE_TYPE, t.IS_DYNAMIC, t.AUTO_CLUSTERING_ON, t.COMMENT AS TABLE_COMMENT,
           t.ROW_COUNT, t.BYTES, t.CREATED, t.LAST_DDL, t.LAST_ALTERED,
           t.TABLE_OWNER, t.LAST_DDL_BY, t.CLUSTERING_KEY,
           c.COLUMN_NAME, c.DATA_TYPE, c.COMMENT
    FROM INFORMATION_SCHEMA.TABLES t
    LEFT JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_SCHEMA = c.TABLE_SCHEMA AND t.TABLE_NAME = c.TABLE_NAME
    WHERE t.TABLE_CATALOG = '{connection_params['database']}' {schema_filter}
    ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION;
    """
    cursor.execute(table_query)
    tables_and_columns = cursor.fetchall()

    # Fetching primary key details
    pk_query = "SHOW PRIMARY KEYS IN DATABASE;"
    cursor.execute(pk_query)
    primary_keys = cursor.fetchall()

    # Fetching foreign key details
    fk_query = "SHOW IMPORTED KEYS IN DATABASE;"
    cursor.execute(fk_query)
    foreign_keys = cursor.fetchall()

    conn.close()

    # Filter keys to include only those related to fetched tables
    table_set = {(row['TABLE_SCHEMA'], row['TABLE_NAME']) for row in tables_and_columns}
    filtered_pks = [pk for pk in primary_keys if (pk['schema_name'], pk['table_name']) in table_set]
    filtered_fks = [fk for fk in foreign_keys if (fk['fk_schema_name'], fk['fk_table_name']) in table_set]

    # Organize the results into structured data
    data = {
        'tables': tables_and_columns,
        'primary_keys': filtered_pks,
        'foreign_keys': filtered_fks
    }

    return data

def generate_dbml(data, connection_params=None, primary_key_hints=None, visualization_params=None):
    db = Database()

    # Load visualization params, primary key hints, and connection params
    vis_params_default = load_visualization_params()
    if visualization_params:
        for key in vis_params_default:
            if key in visualization_params and visualization_params[key]:
                vis_params_default[key] = visualization_params[key]
    visualization_params = vis_params_default

    primary_key_hints = primary_key_hints or load_primary_key_hints()
    connection_params = connection_params or load_config()

    # Create the project and add metadata note
    project = Project(name=connection_params['database'])
    note_text = f"Generated using snowflake-dbml on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                f"Database: {connection_params['database']}\n" \
                f"Database User: {connection_params['user']}\n" \
                f"Included Schemas: {connection_params.get('included_schemas', 'All')}\n" \
                f"Excluded Schemas: {connection_params.get('excluded_schemas', 'None')}"
    project.note = Note(text=note_text)
    db.add_project(project)

    # Initialize table group mapping
    table_groups = {}
    tables = {}

    # 
    # Create tables, columns, and handle primary keys
    # 
    for row in data['tables']:
        schema = row['TABLE_SCHEMA'].lower()
        table_name = row['TABLE_NAME'].lower()
        full_table_name = f"{schema}.{table_name}"

        if full_table_name not in tables:
            # Determine the header color and type for the table
            is_dynamic = row['IS_DYNAMIC'] == 'YES'
            table_color = visualization_params['view_color'] if row['TABLE_TYPE'] == 'VIEW' else visualization_params['dynamic_table_color'] if is_dynamic else visualization_params['table_color']
            emoji = "🚀 " if is_dynamic else ""
            table = Table(schema=schema, name=table_name, header_color=table_color, note=generate_table_notes(row, row['TABLE_TYPE'], emoji=emoji))

            # Group tables by schema
            if schema not in table_groups:
                table_groups[schema] = TableGroup(name=schema, items=[table])
            elif table not in table_groups[schema].items:
                table_groups[schema].items.append(table)

            db.add_table(table)
            tables[full_table_name] = table
        else:
            table = tables[full_table_name]

        # Add column and tag primary keys where applicable
        column = Column(name=row['COLUMN_NAME'], type=row['DATA_TYPE'])
        if row.get('COMMENT'):
            column.note = Note(text=row['COMMENT'])
        # Check if column is a primary key
        for pk in data['primary_keys']:
            if pk['column_name'] == row['COLUMN_NAME'] and pk['table_name'].lower() == table_name:
                column.pk = True
        table.add_column(column)

    # 
    # Handle foreign keys returned from snowflake
    # 
    
    # Initialize storage for foreign key columns to handle composite keys
    foreign_keys = defaultdict(lambda: {'from_cols': [], 'to_cols': [], 'from_table': None, 'to_table': None})

    # Collect foreign key columns grouped by foreign key name
    for fk in data['foreign_keys']:
        key_name = fk['fk_name']
        schema_fk = fk['fk_schema_name'].lower()
        table_fk = fk['fk_table_name'].lower()
        schema_pk = fk['pk_schema_name'].lower()
        table_pk = fk['pk_table_name'].lower()
        
        # Ensure the tables are loaded in the DBML database object
        if f"{schema_fk}.{table_fk}" in db.table_dict and f"{schema_pk}.{table_pk}" in db.table_dict:
            from_table = db[f"{schema_fk}.{table_fk}"]
            to_table = db[f"{schema_pk}.{table_pk}"]
            from_column = from_table[fk['fk_column_name']]
            to_column = to_table[fk['pk_column_name']]
            
            # Append to the list maintaining the order as per 'key_sequence'
            foreign_keys[key_name]['from_cols'].append((fk['key_sequence'], from_column))
            foreign_keys[key_name]['to_cols'].append((fk['key_sequence'], to_column))
            foreign_keys[key_name]['from_table'] = from_table
            foreign_keys[key_name]['to_table'] = to_table

    # Create foreign key references for each group
    for key, cols in foreign_keys.items():
        # Sort columns by key sequence to maintain the correct order
        cols['from_cols'].sort()
        cols['to_cols'].sort()
        
        # Extract columns from sorted tuples
        from_columns = [col for _, col in cols['from_cols']]
        to_columns = [col for _, col in cols['to_cols']]

        # Create a Reference object with composite keys if needed
        reference = Reference(type='>', col1=from_columns, col2=to_columns, comment=f"Foreign key relationship {key}.")
        db.add_reference(reference)

    # 
    # infer foreign keys using primary key hints
    # 
    relationships = infer_relationships(tables, primary_key_hints)
    for rel in relationships:
        db.add_reference(rel)

    # Add table groups to the database
    for group in table_groups.values():
        db.add_table_group(group)

    # Generate and return DBML representation
    return db.dbml

def infer_relationships(tables, primary_key_hints):
    """
    Infers and creates DBML Reference objects based on primary and natural key relationships.
    `tables` is a dictionary with table names as keys and pydbml Table objects as values.
    """
    references = []

    # Infer relationships based on natural keys and primary keys
    for table_name, table in tables.items():
        if table_name not in primary_key_hints:
            continue

        hints = primary_key_hints[table_name]
        natural_keys = hints.get('natural_key', [])
        primary_key = hints.get('primary_key', {})
        
        # Check all tables for matching natural keys
        for other_table_name, other_table in tables.items():
            if other_table_name != table_name:
                other_table_column_names = {col.name for col in other_table.columns}
                table_column_names = {col.name for col in table.columns}

                # Natural key relationships
                if len(natural_keys) > 0:
                    if set(natural_keys).issubset(other_table_column_names) and set(natural_keys).issubset(table_column_names):
                        from_columns = [col for col in other_table.columns if col.name in natural_keys]
                        to_columns = [col for col in table.columns if col.name in natural_keys]
                        if from_columns and to_columns:
                            ref = Reference(type='>', 
                                        col1=from_columns, 
                                        col2=to_columns,
                                        comment=f"Natural key relationship inferred from primary key hints for {table_name}.")
                            references.append(ref)

                # Primary key relationships
                if primary_key:
                    pk_column_name = primary_key['column']
                    for ref_as in primary_key['reference_as']:
                        # Find the matching column object in other_table
                        from_column = next((column for column in other_table.columns if column.name == ref_as), None)

                        # Find the matching column object in table
                        to_column = next((column for column in table.columns if column.name == pk_column_name), None)

                        if from_column and to_column:
                            ref = Reference(
                                type='>',
                                col1=[from_column],  # Use the actual Column object
                                col2=[to_column],    # Use the actual Column object
                                comment=f"Primary key relationship inferred from primary key hints for {table_name}."
                            )
                            references.append(ref)


    return references


def escape_dbml_string(text):
    """Escapes single quotes in DBML strings by adding a backslash."""
    return text.replace("'", "\\'").strip()

def generate_table_notes(row, table_type, emoji):
    is_dynamic = row['IS_DYNAMIC'] == 'YES'
    note_content = f"{emoji}{'DYNAMIC TABLE' if is_dynamic else table_type}\n"
    if row['TABLE_COMMENT']:
        note_content += f"Comment: {escape_dbml_string(row['TABLE_COMMENT'])}\n"
    if row['TABLE_TYPE'] != 'VIEW':
        note_content += f"\nMetrics:\n- Rows: {format_number(row['ROW_COUNT'])}\n- Size: {human_readable_size(row['BYTES'])}\n"
        note_content += f"\nTimestamps:\n- Created: {row['CREATED']}\n- Last DDL: {row['LAST_DDL']}\n- Last Altered: {row['LAST_ALTERED']}\n"
        note_content += f"\nOwnership:\n- Owner: {row['TABLE_OWNER']}\n- Last DDL By: {row['LAST_DDL_BY']}\n"
        clustering_value = row['CLUSTERING_KEY'] if row['CLUSTERING_KEY'] else '<none>'
        note_content += f"\nClustering:\n- Clustering Key: {clustering_value}\n-Auto Clustering: {row['AUTO_CLUSTERING_ON']}\n"
    return note_content

def format_column_name(name):
    """Encloses column names with spaces in double quotes."""
    return f'"{name}"' if ' ' in name else name

def format_number(value):
    """Formats numbers with commas."""
    return f"{value:,}" if value is not None else "Unknown"

def human_readable_size(size, precision=2):
    if size is None:
        return "Unknown size"
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    suffix_index = 0
    while size >= 1024 and suffix_index < 4:
        suffix_index += 1
        size /= 1024.0
    return f"{size:.{precision}f} {suffixes[suffix_index]}"

def format_multiline_note(note_content, indent_level=2):
    """
    Formats a multiline note with proper indentation.
    :param note_content: The content of the note.
    :param indent_level: Number of indentations (each indentation is 2 spaces by default in DBML).
    :return: Formatted multiline note.
    """
    indentation = '  ' * indent_level
    last_indentation = '  ' * max((indent_level - 1),0)
    note_lines = note_content.strip().split('\n')
    formatted_lines = [indentation + line.strip() for line in note_lines]
    return "'''\n" + '\n'.join(formatted_lines) + "\n" + last_indentation + "'''\n"

def prompt_for_config(existing_config):
    print("Entering interactive mode to gather necessary configuration parameters.")
    config = {
        'user': input("Enter your Snowflake user name: ") or existing_config.get('user'),
        'password': getpass.getpass("Enter your Snowflake password: "),
        'account': input("Enter your Snowflake account identifier (e.g., xy12345.us-east-1): ") or existing_config.get('account'),
        'warehouse': input("Enter your Snowflake warehouse name: ") or existing_config.get('warehouse'),
        'database': input("Enter your Snowflake database name: ") or existing_config.get('database'),
        'role': input("Enter your Snowflake role: ") or existing_config.get('role'),
        'included_schemas': input("Enter a comma-separated list of schemas to include (optional): "),
        'excluded_schemas': input("Enter a comma-separated list of schemas to exclude (optional): "),
        'table_color': input("Enter a hex color for table headers (optional): "),
        'view_color': input("Enter a hex color for view headers (optional): "),
        'config': input("Enter a hex color for view headers (optional): ")
    }
    return config

def save_config_to_env(config):
    answer = input("Would you like to save these settings to a .env file for future use? (yes/no): ")
    if answer.lower() in ['yes', 'y']:
        print("Saving configuration to .env file...")
        with open('.env', 'w') as f:
            for key, value in config.items():
                if value:  # Only save non-empty values
                    f.write(f"{key.upper()}={value}\n")
        print("Configuration saved to .env file in the current directory.")
    else:
        print("Configuration not saved.")


def main():
    # Setup Argument Parser with more options
    parser = argparse.ArgumentParser(
        description="Reverese engineer ER diagrams files from Snowflake databases using DBML",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter  # This will show default values in the help message
    )
    parser.add_argument('--user', type=str, help='Snowflake user name')
    parser.add_argument('--password', type=str, help='Snowflake password')
    parser.add_argument('--account', type=str, help='Snowflake account identifier')
    parser.add_argument('--warehouse', type=str, help='Snowflake warehouse')
    parser.add_argument('--database', type=str, help='Snowflake database name')
    parser.add_argument('--role', type=str, help='Snowflake role')
    parser.add_argument('--config-file', type=str, help='Path to the config JSON file (contains primary/foreign key hints)')
    parser.add_argument('--included-schemas', type=str, help='Comma-separated list of schemas to include')
    parser.add_argument('--excluded-schemas', type=str, help='Comma-separated list of schemas to exclude')
    parser.add_argument('--table-color', type=str, help='Color for table headers in DBML.')
    parser.add_argument('--view-color', type=str, help='Color for view headers in DBML.')
    parser.add_argument('--dynamic-table-color', type=str, help='Color for dynamic table headers in DBML.')
    parser.add_argument('--interactive', action='store_true', help='Enter interactive mode to configure parameters interactively')
    
    args = parser.parse_args()

    if args.interactive:
        config = prompt_for_config({})
        # Further processing, such as saving to a .env file or continuing with the execution, goes here.
        # You could call save_config_to_env(config) here if needed
        save_config_to_env(config)
    else:
        # Load configurations, prioritizing command-line arguments over environment variables
        config = load_config()
        connection_params = {
            'user': args.user or config['user'],
            'password': args.password or config['password'],
            'account': args.account or config['account'],
            'warehouse': args.warehouse or config['warehouse'],
            'database': args.database or config['database'],
            'role': args.role or config['role'],
        }

        primary_key_hints = load_primary_key_hints(args.config_file or config.get('config-file'))

        if args.included_schemas:
            config['included_schemas'] = args.included_schemas
        if args.excluded_schemas:
            config['excluded_schemas'] = args.excluded_schemas

        visualization_params = load_visualization_params()
        # Override visualization params with command-line arguments if provided
        if args.table_color:
            visualization_params['table_color'] = args.table_color
        if args.view_color:
            visualization_params['view_color'] = args.view_color
        if args.dynamic_table_color:
            visualization_params['dynamic_table_color'] = args.dynamic_table_color

    logging.debug(f"Generating DBML")
    logging.debug(f"Connection Params: {connection_params}")
    logging.debug(f"Primary Key Hints: {primary_key_hints}")
    logging.debug(f"Visualization Params: {visualization_params}")

    data = fetch_data(connection_params, config['included_schemas'], config['excluded_schemas'])

    logging.debug(f"Fetched data from Snowflake: {len(data)} rows")


    dbml_output = generate_dbml(data, connection_params=connection_params, primary_key_hints=primary_key_hints, visualization_params=visualization_params)
    print(dbml_output)

if __name__ == "__main__":

    main()