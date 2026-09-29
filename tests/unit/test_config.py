from sprayrover.config import load_rover_config


def test_rover_config_has_required_sections():
    config = load_rover_config()
    for section in ("geometry", "limits", "sensors", "safety"):
        assert section in config


def test_geometry_values_are_positive():
    geometry = load_rover_config()["geometry"]
    for key in ("wheelbase", "track_width", "wheel_radius"):
        assert geometry[key] > 0
