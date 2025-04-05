import datetime

from src.data_types.parseable_datetime import ParseableDatetime


def test_parseable_datetime() -> None:
    # Test serialization
    dt = ParseableDatetime(datetime.datetime(2023, 10, 1, 12, 30, 45))
    assert dt.serialize() == "2023-10-01_12-30-45"

    # Test deserialization
    dt_str = "2023-10-01_12-30-45"
    parsed_dt = ParseableDatetime.deserialize(dt_str)
    assert parsed_dt.datetime_obj == datetime.datetime(2023, 10, 1, 12, 30, 45)

    # Test invalid format
    invalid_dt_str = "2023/10/01 12:30:45"
    try:
        ParseableDatetime.deserialize(invalid_dt_str)
    except ValueError as e:
        assert str(e) == f"Invalid date string format: {invalid_dt_str}. Expected format is %Y-%m-%d_%H-%M-%S."
