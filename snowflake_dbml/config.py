# snowflake_dbml/config.py
import os
import json
from dotenv import load_dotenv

# defaults
default_table_color = '#3498db'  # Default blue
default_view_color = '#9b59b6'  # Default purple
default_dynamic_table_color = '#9b59b6'  # Default orange

# Load environment variables from a .env file if present
load_dotenv(override=True) # if .env file is present, override existing environment variables

def load_config():
    """Return configuration loaded from environment variables or .env file, including schema filters."""
    return {
        'user': os.getenv('SNOWFLAKE_USER'),
        'password': os.getenv('SNOWFLAKE_PASSWORD'),
        'account': os.getenv('SNOWFLAKE_ACCOUNT'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
        'database': os.getenv('SNOWFLAKE_DATABASE'),
        'role': os.getenv('SNOWFLAKE_ROLE'),

        'primary_key_hints_path': os.getenv('PRIMARY_KEY_HINTS_PATH'),

        'included_schemas': os.getenv('INCLUDED_SCHEMAS'),  # Schemas to include
        'excluded_schemas': os.getenv('EXCLUDED_SCHEMAS'),  # Schemas to exclude
        
        'table_color': os.getenv('TABLE_COLOR', default_table_color),
        'view_color': os.getenv('VIEW_COLOR', default_view_color), 
        'dynamic_table_color': os.getenv('DYNAMIC_TABLE_COLOR', default_dynamic_table_color) 
    }

def load_primary_key_hints(path=None):
    """Load primary key hints from a JSON file."""
    if not path:
        path = os.getenv('PRIMARY_KEY_HINTS_PATH', '')  # Default or .env specified path
    if not path:
        return {}  # Return empty hints if no path is provided
    try:
        with open(path, 'r') as file:
            return json.load(file)['table-primary-keys']
    except (FileNotFoundError, KeyError):
        raise FileNotFoundError(f"Primary key hints file {path} not found or is invalid.")
    except json.JSONDecodeError:
        raise ValueError(f"Error parsing the JSON hints file {path}.")

def load_visualization_params():
    """Return visualization parameters from environment variables with defaults."""
    return {
        'table_color': os.getenv('TABLE_COLOR', default_table_color),
        'view_color': os.getenv('VIEW_COLOR', default_view_color),
        'dynamic_table_color': os.getenv('DYNAMIC_TABLE_COLOR', default_dynamic_table_color)
    }