"""Fictional records. Only the discoverable, public projection is used by the UI."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PublicMember:
    name: str
    state: str = ""
    city: str = ""

    biography: str = ""
    photo_url: str = ""

    def label(self, member_id):
        location = ", ".join(filter(None, (self.city, self.state))) or "Location unlisted"
        return f"{self.name} · ID {member_id} · {location}"


def public_directory(core):
    records = {i: {"name": name} for i, name in core.items()}
    records.update({
        1: {"name": "David", "public_biography": "I like bringing people together over a board game. My favorite part is introducing two friends who have never met.", "public_state": "California", "public_city": "Long Beach"},
        2: {"name": "Mary", "public_biography": "I trade sketches with friends and organize a weekend drawing circle. There is always room for one more sketchbook.", "public_state": "California", "public_city": "Anaheim"},
        4: {"name": "Laura", "public_biography": "I collect trail maps and plan short walks with friends. A good picnic spot earns a star on my map.", "public_state": "Washington", "public_city": "Pasco"},
        5: {"name": "Sinbad", "public_biography": "I make up puzzle hunts for game nights. My favorite clues take two friends working together to solve.", "private_city": "Cedar Hollow"},
        101: {"name": "John Smith", "public_state": "California", "public_city": "Long Beach"},
        102: {"name": "John Smith", "public_state": "Washington", "public_city": "Tacoma"},
        104: {"name": "Nell Vale"},
        105: {"name": "Ada Finch"},
        106: {"name": "Tess Reed"},
        103: {"name": "Jules North", "public_state": "Oregon", "discoverable": False},
    })
    return {
        i: PublicMember(row["name"], row.get("public_state", ""), row.get("public_city", ""),
                        row.get("public_biography", ""), row.get("public_photo_url", ""))
        for i, row in records.items() if row.get("discoverable", True)
    }


def search_members(directory, query, *, state=None):
    term = " ".join(query.split()).casefold()
    if not term:
        return []
    digits = term.removeprefix("#")
    exact_id = digits.isascii() and digits.isdecimal()
    matches = []
    for member_id, member in directory.items():
        if state and member.state != state:
            continue
        if exact_id:
            match = digits == str(member_id)
        else:
            match = term in member.name.casefold()
        if match:
            matches.append(member_id)
    return sorted(matches, key=lambda i: (directory[i].name.casefold() != term,
                                          directory[i].name.casefold(), i))


def unique_member(directory, query, *, state=None):
    matches = search_members(directory, query, state=state)
    return matches[0] if len(matches) == 1 else None
