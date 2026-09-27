import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "producer"))
from simulator import Driver, haversine_km, CITY


def test_haversine_known_distance():
    # Hitec City to Secunderabad is roughly 13-14 km
    d = haversine_km(17.4435, 78.3772, 17.4399, 78.4983)
    assert 12 < d < 15


def test_driver_stays_inside_city():
    d = Driver(driver_id="t", lat=17.44, lon=78.40)
    for _ in range(500):
        d.step(2.0, [])
    assert CITY["lat_min"] <= d.lat <= CITY["lat_max"]
    assert CITY["lon_min"] <= d.lon <= CITY["lon_max"]


def test_every_tick_emits_location_update():
    d = Driver(driver_id="t", lat=17.44, lon=78.40)
    events = []
    d.step(2.0, events)
    assert any(e["event_type"] == "location_update" for e in events)
