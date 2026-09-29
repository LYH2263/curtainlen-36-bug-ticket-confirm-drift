from app.engines.curtain_math import fabric_meters
def test_seed_bedroom():
    assert fabric_meters(2.2, 1.5, 2.0, 0.10, 0.15, 1.4)["panels"] == 4
