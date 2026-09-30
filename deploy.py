import os
import glob
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def get_private_key():
    p_key_str = os.environ['SNF_PRIVATE_KEY']
    p_key = serialization.load_pem_private_key(
        p_key_str.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

def run_deployment():
    print("Connecting to Snowflake with Key-Pair...")
    conn = snowflake.connector.connect(
        account=os.environ['SNF_ACCOUNT'],
        user=os.environ['SNF_USER'],
        private_key=get_private_key(),
        warehouse=os.environ['SNF_WAREHOUSE'],
        database=os.environ['SNF_DATABASE'],
        schema=os.environ['SNF_SCHEMA'],
        role=os.environ.get('SNF_ROLE', 'DATA_ENGINEER')
    )

    # Scans 'scripts/' folder
    script_files = sorted(glob.glob("scripts/*.txt") + glob.glob("scripts/*.sql"))
    if not script_files:
        print("No script files found in scripts/ folder.")
        conn.close()
        return

    print(f"Found {len(script_files)} file(s) to execute.")

    for file_path in script_files:
        print(f"\n--- Executing: {file_path} ---")
        with open(file_path, "r", encoding="utf-8") as f:
            sql_script = f.read().strip()

        if not sql_script:
            continue

        for cur in conn.cursor().execute_string(sql_script):
            print(f"Status: {cur.statusmessage}")

    conn.close()
    print("\nAll scripts executed successfully!")

if __name__ == "__main__":
    run_deployment()