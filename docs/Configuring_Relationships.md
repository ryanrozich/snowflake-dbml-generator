# Configuring Relationships

The Snowflake DBML Generator allows specifying relationship hints through a `config.json` file to address databases that do not explicitly define primary and foreign key relationships due to Snowflake's lack of enforcement on referential integrity.

## Example Configuration (`config.json.sample`)

```json
{
    "table-primary-keys": {
        "schema1.dim_table1": {
            "natural_key": ["entity1_name"],
            "primary_key": {
                "column": "ID",
                "reference_as": ["entity1_ID"]
            }
        },
        "schema2.dim_table2": {
            "natural_key": ["entity2_name", "other_id"],
            "primary_key": {
                "column": "ID",
                "reference_as": ["entity2_ID"]
            }
        }
    }
}
```

### Key Types

- **`natural_key`**: Composite key. If another table contains all specified columns, a DBML foreign key relationship is created.
- **`primary_key`**: Defines a primary key and lists column names in other tables that should be treated as foreign keys. Useful for linking columns with different names that represent the same entity.

### Relationship Inference

- **Natural Key**: Automatically creates foreign key relationships in the DBML for tables containing the specified `natural_key` columns.
- **Primary Key**: Generates foreign key relationships for tables that contain any `reference_as` column, pointing to the `primary_key` column specified.

This enables your DBML diagram to illustrate the intended schema relationships, even when those are not stored in Snowflake as Primary and Foreign Keys.
```