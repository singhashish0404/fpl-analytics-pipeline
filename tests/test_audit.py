from src.audit import determine_status

def test_determine_status_no_failures():
    result = determine_status("some_check",0)
    assert result =="pass"


def test_determine_status_negative_points():
    result = determine_status("negative_points", 1)

    assert result == "WARNING"


def test_determine_status_other_failure():
    result = determine_status("null_player_id", 1)

    assert result == "FAIL" 