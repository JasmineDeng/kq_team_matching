from src.load_data import convert_alias_to_name


def test_convert_alias_to_name() -> None:
    aliases = [
        {"B", "BEE"},
    ]
    all_names = {"AB", "BEE", "C"}
    assert convert_alias_to_name(all_names, "D", aliases) == "D"
    assert convert_alias_to_name(all_names, "B", aliases) == "BEE"
    assert convert_alias_to_name(all_names, "BEE", aliases) == "BEE"
