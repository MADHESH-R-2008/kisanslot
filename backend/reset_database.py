"""Explicitly reset the configured MySQL database. Intended for manual use only."""
import os

from sqlalchemy import inspect, text

from database import engine


def reset() -> None:
    expected = os.environ.get("RESET_DATABASE_NAME")
    if not expected:
        raise RuntimeError("RESET_DATABASE_NAME is required")
    if engine.dialect.name not in {"mysql", "mariadb"}:
        raise RuntimeError("Refusing to reset a non-MySQL database")

    with engine.begin() as connection:
        actual = connection.execute(text("SELECT DATABASE()")) .scalar_one()
        if actual != expected:
            raise RuntimeError(f"Refusing to reset unexpected database: {actual}")
        tables = inspect(connection).get_table_names()
        connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        try:
            for table in tables:
                escaped = table.replace("`", "``")
                connection.execute(text(f"DROP TABLE `{escaped}`"))
        finally:
            connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    print(f"Reset complete: dropped {len(tables)} tables from {expected}")


if __name__ == "__main__":
    reset()
