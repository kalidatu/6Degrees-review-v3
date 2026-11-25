
from collections import deque
from database import connect, initialize_database


def find_people(name):
    """Find contacts by full or partial name."""
    with connect() as db:
        return db.execute(
            """
            SELECT id, name FROM people
            WHERE name LIKE ? COLLATE NOCASE
            ORDER BY name
            """,
            (f"%{name}%",)
        ).fetchall()


def get_network():
    """Load saved relationships into a graph."""
    network = {}

    with connect() as db:
        people = db.execute(
            "SELECT id FROM people"
        ).fetchall()

        for (person_id,) in people:
            network[person_id] = []

        relationships = db.execute(
            """
            SELECT person1_id, person2_id
            FROM relationships
            """
        ).fetchall()

        for first, second in relationships:
            network[first].append(second)
            network[second].append(first)

    return network


def find_connection(start, target, network):
    """Find the shortest path using BFS."""
    queue = deque([[start]])
    visited = {start}

    while queue:
        path = queue.popleft()
        person = path[-1]

        if person == target:
            return path

        for neighbor in network.get(person, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    return None


def choose_person(prompt):
    """Resolve a partial name to one contact."""
    while True:
        search = input(prompt).strip()

        if not search:
            print("Please enter a name.")
            continue

        matches = find_people(search)

        if not matches:
            print("No matching contact found.")
            return None

        if len(matches) == 1:
            return matches[0]

        print("\nMultiple matches:")
        for person_id, name in matches:
            print(f"{person_id}. {name}")

        choice = input("Enter the correct ID: ").strip()

        for person_id, name in matches:
            if choice == str(person_id):
                return person_id, name

        print("Invalid selection.")
        return None


def main():
    initialize_database()

    print("=" * 45)
    print("           WELCOME TO 6DEGREES")
    print("=" * 45)
    print("Discover who connects you.\n")

    start = choose_person("Enter your name: ")
    if start is None:
        return

    target = choose_person(
        "Who do you want to connect with? "
    )
    if target is None:
        return

    network = get_network()
    path = find_connection(start[0], target[0], network)

    if path is None:
        print("\nNo connection found in our database.")
        return

    with connect() as db:
        names = {
            person_id: name
            for person_id, name in db.execute(
                "SELECT id, name FROM people"
            )
        }

    print("\nConnection found!")
    print(" -> ".join(names[person_id] for person_id in path))
    print(f"\nDegrees of separation: {len(path) - 1}")


if __name__ == "__main__":
    main()
