"""Create a restorable SQL backup of the configured MySQL/MariaDB database."""
from datetime import datetime, timezone
from pathlib import Path

from database import engine


def backup() -> Path:
    if engine.dialect.name not in {"mysql", "mariadb"}:
        raise RuntimeError("This backup utility only supports MySQL/MariaDB")

    output_dir = Path(__file__).resolve().parent / "backups"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"kisanslot-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.sql"

    raw = engine.raw_connection()
    try:
        cursor = raw.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        with output.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write("SET FOREIGN_KEY_CHECKS=0;\nSET NAMES utf8mb4;\n")
            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_sql = cursor.fetchone()[1]
                stream.write(f"\nDROP TABLE IF EXISTS `{table}`;\n{create_sql};\n")
                cursor.execute(f"SELECT * FROM `{table}`")
                columns = [item[0] for item in cursor.description]
                quoted_columns = ", ".join(f"`{name}`" for name in columns)
                while True:
                    rows = cursor.fetchmany(500)
                    if not rows:
                        break
                    values = ",\n".join(
                        cursor.mogrify("(" + ",".join(["%s"] * len(row)) + ")", row)
                        for row in rows
                    )
                    stream.write(f"INSERT INTO `{table}` ({quoted_columns}) VALUES\n{values};\n")
            stream.write("\nSET FOREIGN_KEY_CHECKS=1;\n")
        return output
    finally:
        raw.close()


if __name__ == "__main__":
    path = backup()
    print(f"Backup created: {path.name} ({path.stat().st_size} bytes)")
