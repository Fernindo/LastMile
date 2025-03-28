import subprocess
import datetime
import os

def backup_database():
    # ✅ Your Neon connection details
    host = "ep-holy-bar-a2bpx2sc-pooler.eu-central-1.aws.neon.tech"
    port = "5432"
    user = "neondb_owner"
    password = "npg_aYC4yHnQIjV1"
    dbname = "neondb"

    # ✅ Output folder
    backup_folder = os.path.join(os.path.dirname(__file__), "databaza")
    os.makedirs(backup_folder, exist_ok=True)

    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(backup_folder, f"backup_{date_str}.txt")

    # ✅ Set password in environment
    env = os.environ.copy()
    env["PGPASSWORD"] = password

    try:
        subprocess.run([
            "pg_dump",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", dbname,
            "--no-owner",
            "--no-privileges",
            "--encoding", "UTF8",
            "--clean",
            "--create",
            "--format", "plain",
            "--file", filename,
            "--sslmode=require"
        ], env=env, check=True)

        print(f"✅ Backup completed successfully and saved as:\n{filename}")
    except subprocess.CalledProcessError as e:
        print("❌ Backup failed:", e)
