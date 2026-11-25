
import sqlite3
from pathlib import Path

# Store the database alongside our Python files.
DB_PATH = Path(__file__).with_name("6degrees.db")


def connect():
    """Open our 6Degrees database."""
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize_database():
    """Create our database tables if needed."""

    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                person1_id INTEGER NOT NULL,
                person2_id INTEGER NOT NULL,
                PRIMARY KEY (person1_id, person2_id),
                FOREIGN KEY (person1_id) REFERENCES people(id),
                FOREIGN KEY (person2_id) REFERENCES people(id),
                CHECK (person1_id < person2_id)
            )
        """)


def add_person(name):
    """Add a person to the database."""

    name = " ".join(name.strip().split())

    if not name:
        print("Please enter a name.")
        return

    with connect() as db:
        cursor = db.execute(
            "INSERT OR IGNORE INTO people (name) VALUES (?)",
            (name,)
        )

        if cursor.rowcount:
            print(f"Added: {name}")
        else:
            print(f"{name} is already in the database.")


def list_people():
    """Display everyone in our database."""

    with connect() as db:
        people = db.execute(
            "SELECT id, name FROM people ORDER BY name"
        ).fetchall()

    print("\n6Degrees Contact Directory")
    print("-" * 35)

    if not people:
        print("No contacts yet.")

    for person_id, name in people:
        print(f"{person_id}. {name}")

    return people


def add_relationship(person1_id, person2_id):
    """Connect two existing people."""

    if person1_id == person2_id:
        print("A person cannot connect to themselves.")
        return

    first, second = sorted((person1_id, person2_id))

    try:
        with connect() as db:
            db.execute("""
                INSERT INTO relationships
                (person1_id, person2_id)
                VALUES (?, ?)
            """, (first, second))

        print("Relationship added successfully!")

    except sqlite3.IntegrityError:
        print("Relationship already exists or an ID is invalid.")


if __name__ == "__main__":
    initialize_database()
    print("6Degrees database initialized successfully!")
