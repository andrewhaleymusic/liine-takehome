from dataclasses import dataclass


@dataclass(slots=True)
class ParsedRestaurantHours:
    name: str
    hours_text: str


def parse_csv_rows() -> list[ParsedRestaurantHours]:
    raise NotImplementedError("Prompt 3 will implement CSV parsing.")
