from presentation import FONT_SIZES, device_state, status_time, visible_table_columns


def test_device_connected_when_recent():
    result = device_state(4, 5)
    assert result.code == "online" and result.fresh


def test_device_delayed_after_deadline():
    result = device_state(44, 5)
    assert result.code == "delayed" and not result.fresh


def test_device_offline_after_twice_deadline():
    assert device_state(90, 5).code == "offline"


def test_long_interval_not_false_offline():
    assert device_state(60, 30).code == "online"


def test_invalid_age_not_assumed_connected():
    assert device_state(float("inf")).code == "offline"
    assert device_state(-300).code == "offline"


def test_full_table_keeps_all_fields():
    columns = ["ID", "Horário", "Motivo", "Score", "Coluna futura"]
    assert visible_table_columns(columns, "Completa") == columns


def test_compact_table_keeps_readable_columns():
    columns = ["ID", "Horário", "Potência (W)", "Corrente (A)", "Motivo"]
    assert visible_table_columns(columns, "Resumida") == ["Horário", "Corrente (A)", "Potência (W)"]


def test_accessibility_font_sizes():
    assert list(FONT_SIZES.values()) == [16, 18, 20]
    assert status_time("not a date") == "Horário inválido"
