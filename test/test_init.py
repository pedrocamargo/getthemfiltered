import configparser
from pathlib import Path

import pytest

METADATA_FILE = Path(__file__).resolve().parent.parent / "getthemfiltered" / "metadata.txt"


@pytest.mark.parametrize(
    "expectation",
    [
        "name",
        "qgisMinimumVersion",
        "description",
        "about",
        "version",
        "author",
        "email",
        "repository",
        "tracker",
    ],
)
def test_metadata_fields(expectation):
    """Test that all required metadata fields are present."""
    assert METADATA_FILE.exists(), f"Metadata file not found: {METADATA_FILE}"

    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(METADATA_FILE, encoding="utf-8")

    assert parser.has_section("general"), f"Missing [general] section in {METADATA_FILE}"
    metadata = dict(parser.items("general"))
    assert expectation in metadata, f'Missing metadata key "{expectation}"'
    assert len(metadata[expectation].strip()) > 0, f'Metadata key "{expectation}" is empty'
