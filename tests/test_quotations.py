"""Checks that every quotation in the data file is complete."""

import yaml

REQUIRED_KEYS = ("quotation", "author", "game")


def test_every_quotation_has_all_fields():
    """A missing field crashes add_record with KeyError and loses the trophy."""

    with open("src/data/quotations.yaml", "r", encoding="utf8") as file:
        quotations = yaml.safe_load(file)["quotations"]

    assert len(quotations) > 0

    for index, item in enumerate(quotations):
        assert isinstance(item, dict), f"item {index} is not a mapping: {item!r}"
        for key in REQUIRED_KEYS:
            value = item.get(key)
            assert isinstance(value, str) and value.strip(), (
                f"item {index} has no '{key}': {item!r}"
            )
