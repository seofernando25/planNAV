import pytest
import numpy as np
from app.engine.trajectory import haversine, interpolate_position, Leg, FlightEngine


def test_haversine():
    # Known distance: Toronto (CYYZ) to Vancouver (CYVR) is ~1808 NM
    toronto = (43.68, -79.63)
    vancouver = (49.19, -123.18)
    dist = haversine(toronto[0], toronto[1], vancouver[0], vancouver[1])
    assert 1800 < dist < 1820


def test_interpolation():
    # Midpoint of a 100 NM path
    start = (40.0, -80.0)
    end = (41.0, -80.0)
    mid = interpolate_position(start[0], start[1], end[0], end[1], 0.5)
    assert mid[0] == pytest.approx(40.5, abs=0.1)
    assert mid[1] == -80.0


def test_leg_initialization():
    leg = Leg("TEST101", (40.0, -80.0), (41.0, -80.0), 1000, 400, 30000)
    assert leg.acid == "TEST101"
    assert leg.duration > 0
    assert leg.t1 > leg.t0
    assert (
        leg.v[1] > 0
    )  # Latitude increasing (index 1 in p0 is lat) - wait Leg uses [lon, lat]


def test_analytical_time_slice():
    # Head-on collision course
    # Plane A at 30,000ft, Plane B at 30,000ft
    speed = 300  # NM/h
    # 300 NM/h = 0.0833 NM/sec
    # Total distance 20 NM, should meet in the middle
    leg_a = Leg("ACID_A", (45.0, -75.2), (45.0, -74.8), 0, speed, 30000)
    leg_b = Leg("ACID_B", (45.0, -74.8), (45.0, -75.2), 0, speed, 30000)

    engine = FlightEngine("data/canadian_flights_250.json")
    engine.legs = [leg_a, leg_b]

    conflicts = engine.find_conflicts()
    assert len(conflicts) == 1
    conflict = conflicts[0]

    # Check for mandatory keys to avoid template crashes
    assert "dist" in conflict
    assert "duration" in conflict
    assert "intervals" in conflict

    # Time = 10 NM / 0.166 NM/sec = 60 seconds
    assert 55 < conflict["duration"] < 65
    assert len(conflict["intervals"]) == 1
