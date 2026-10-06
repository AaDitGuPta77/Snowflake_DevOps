import os
import glob
import sys
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

def get_connection():
    p_key_str = os.environ['SNF_PRIVATE_KEY']
    p_key = serialization.load_pem_private_key(
        p_key_str.encode(),
        password=None,
        backend=default_backend()
    )
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return snowflake.connector.connect(
        account=os.environ['SNF_ACCOUNT'],
        user=os.environ['SNF_USER'],
        private_key=pkb,
        role=os.environ['SNF_ROLE'],
        warehouse=os.environ['SNF_WAREHOUSE'],
        database=os.environ['SNF_DATABASE'],
        schema=os.environ['SNF_SCHEMA']
    )

def execute_scripts(conn):
    """Step 7: Execute scripts in sequence."""
    script_files = sorted(glob.glob("scripts/*.txt"))
    if not script_files:
        print("No deployment scripts found in scripts/ directory.")
        return

    print(f"\n--- Step 7: Executing scripts in sequence: {script_files} ---")
    for file_path in script_files:
        print(f"--> Running: {file_path}")
        with open(file_path, "r") as f:
            sql_statements = f.read()

        # Step 8: Catches SQL errors
        for cursor in conn.execute_string(sql_statements):
            cursor.fetchall()
        print(f"--> Completed: {file_path}")

def validate_data(conn):
    """Step 9: Validate data (row counts, objects, identity)."""
    print("\n--- Step 9: Validating Data and Objects in Snowflake ---")
    cursor = conn.cursor()
    try:
        # Check row counts in tbl_orders
        cursor.execute("SELECT COUNT(*) FROM dev_db.public.tbl_orders;")
        row_count = cursor.fetchone()[0]
        print(f"Validation Check: tbl_orders contains {row_count} rows.")
        if row_count == 0:
            raise ValueError("Validation failed: tbl_orders contains 0 rows.")

        # Check existence of the view
        cursor.execute("SHOW VIEWS LIKE 'vw_high_value_orders' IN SCHEMA dev_db.public;")
        if not cursor.fetchall():
            raise ValueError("Validation failed: vw_high_value_orders view does not exist.")

        print("Data validation successful: objects exist and row counts verified.")
    finally:
        cursor.close()

def main():
    conn = get_connection()
    try:
        # Step 7: Ordered Execution
        execute_scripts(conn)

        # Step 9: Data Validation
        validate_data(conn)

        print("\n--- Pipeline Completed Successfully! ---")
    except Exception as e:
        # Step 8: Error reading from deploy log / execution
        print(f"\n[ALERT - STEP 8] Error during run: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()