import json
import numpy as np
import pandas as pd
from datetime import datetime
from math import radians, cos, sin, asin, sqrt, atan2, degrees


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points in nautical miles."""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    # Radius of Earth in nautical miles is approximately 3440.06
    nm = 3440.06 * c
    return nm


def interpolate_position(start_lat, start_lon, end_lat, end_lon, fraction):
    """Interpolate position along a great circle path."""
    if fraction <= 0:
        return start_lat, start_lon
    if fraction >= 1:
        return end_lat, end_lon

    lat1, lon1, lat2, lon2 = map(radians, [start_lat, start_lon, end_lat, end_lon])

    # Distance between points
    d = 2 * asin(
        sqrt(
            sin((lat1 - lat2) / 2) ** 2
            + cos(lat1) * cos(lat2) * sin((lon1 - lon2) / 2) ** 2
        )
    )

    A = sin((1 - fraction) * d) / sin(d)
    B = sin(fraction * d) / sin(d)

    x = A * cos(lat1) * cos(lon1) + B * cos(lat2) * cos(lon2)
    y = A * cos(lat1) * sin(lon1) + B * cos(lat2) * sin(lon2)
    z = A * sin(lat1) + B * sin(lat2)

    lat = atan2(z, sqrt(x**2 + y**2))
    lon = atan2(y, x)

    return degrees(lat), degrees(lon)


class Leg:
    def __init__(self, acid, start_pt, end_pt, start_time, speed_kts, alt):
        self.acid = acid
        self.start_lat, self.start_lon = start_pt
        self.end_lat, self.end_lon = end_pt
        self.p0 = np.array([start_pt[1], start_pt[0]])  # [lon, lat]
        self.p1 = np.array([end_pt[1], end_pt[0]])
        self.t0 = start_time
        self.alt = alt

        # Distance in NM
        self.dist = haversine(
            self.start_lat, self.start_lon, self.end_lat, self.end_lon
        )
        # Duration in seconds
        self.duration = (self.dist / speed_kts) * 3600 if speed_kts > 0 else 0
        self.t1 = self.t0 + self.duration

        # Velocity in deg/sec (Approximate for detection phase)
        if self.duration > 0:
            self.v = (self.p1 - self.p0) / self.duration
        else:
            self.v = np.array([0.0, 0.0])

    def to_dict(self):
        return {
            "start": [self.start_lon, self.start_lat],
            "end": [self.end_lon, self.end_lat],
            "t0": self.t0,
            "t1": self.t1,
            "alt": self.alt,
            "dist": self.dist,
        }


class FlightEngine:
    def __init__(self, data_path):
        with open(data_path, "r") as f:
            self.flights = json.load(f)
        self.airport_coords = {
            "CYYZ": (43.68, -79.63),
            "CYVR": (49.19, -123.18),
            "CYUL": (45.47, -73.74),
            "CYYC": (51.11, -114.02),
            "CYOW": (45.32, -75.67),
            "CYWG": (49.91, -97.24),
            "CYHZ": (44.88, -63.51),
            "CYEG": (53.31, -113.58),
            "CYQB": (46.79, -71.39),
            "CYYJ": (48.65, -123.43),
            "CYYT": (47.62, -52.75),
            "CYXE": (52.17, -106.70),
        }
        self.legs = self._precalculate_legs()

    def parse_waypoint(self, wp_str):
        # Format: 49.97N/110.935W
        lat_str, lon_str = wp_str.split("/")
        lat = float(lat_str[:-1])
        if lat_str.endswith("S"):
            lat = -lat
        lon = float(lon_str[:-1])
        if lon_str.endswith("W"):
            lon = -lon
        return lat, lon

    def get_full_route(self, flight):
        dep_coords = self.airport_coords.get(flight["departure airport"])
        arr_coords = self.airport_coords.get(flight["arrival airport"])

        route_points = []
        if dep_coords:
            route_points.append(dep_coords)

        if flight["route"]:
            for wp in flight["route"].split():
                route_points.append(self.parse_waypoint(wp))

        if arr_coords:
            route_points.append(arr_coords)
        return route_points

    def _calculate_legs_for_flight(self, f):
        points = self.get_full_route(f)
        current_time = f["departure time"]
        legs = []
        for i in range(len(points) - 1):
            leg = Leg(
                f["ACID"],
                points[i],
                points[i + 1],
                current_time,
                f["aircraft speed"],
                f["altitude"],
            )
            legs.append(leg)
            current_time += leg.duration
        return legs

    def _precalculate_legs(self):
        all_legs = []
        for f in self.flights:
            all_legs.extend(self._calculate_legs_for_flight(f))
        return all_legs

    def calculate_trajectory(self, flight, interval_sec=60):
        points = self.get_full_route(flight)
        speed_kts = flight["aircraft speed"]
        start_time = flight["departure time"]

        trajectory = []
        current_time = start_time

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            dist = haversine(p1[0], p1[1], p2[0], p2[1])
            duration = (dist / speed_kts) * 3600

            t = 0
            while t < duration:
                frac = t / duration
                lat, lon = interpolate_position(p1[0], p1[1], p2[0], p2[1], frac)
                trajectory.append(
                    {
                        "time": current_time + t,
                        "lat": lat,
                        "lon": lon,
                        "alt": flight["altitude"],
                        "acid": flight["ACID"],
                    }
                )
                t += interval_sec

            current_time += duration

        trajectory.append(
            {
                "time": current_time,
                "lat": points[-1][0],
                "lon": points[-1][1],
                "alt": flight["altitude"],
                "acid": flight["ACID"],
            }
        )
        return trajectory

    def find_conflicts(self):
        """Find all conflicts across all flights."""
        conflicts = []
        # Group legs by flight
        flight_legs = {}
        for l in self.legs:
            if l.acid not in flight_legs:
                flight_legs[l.acid] = []
            flight_legs[l.acid].append(l)

        acids = list(flight_legs.keys())
        processed_pairs = set()

        for i in range(len(acids)):
            for j in range(i + 1, len(acids)):
                acid1, acid2 = acids[i], acids[j]
                pair = tuple(sorted([acid1, acid2]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)

                f1 = next(f for f in self.flights if f["ACID"] == acid1)
                f2 = next(f for f in self.flights if f["ACID"] == acid2)

                intervals = self.check_pair_conflict(f1, f2)
                if not intervals:
                    continue

                # Calculate true min distance for the whole flight
                min_dist = 9999.0
                legs1 = flight_legs[acid1]
                legs2 = flight_legs[acid2]

                for l1 in legs1:
                    for l2 in legs2:
                        t_start = max(l1.t0, l2.t0)
                        t_end = min(l1.t1, l2.t1)
                        if t_start >= t_end:
                            continue

                        # Use quadratic to find local min time
                        A = l1.p0 + l1.v * (t_start - l1.t0)
                        B = l2.p0 + l2.v * (t_start - l2.t0)
                        P0 = A - B
                        Vrel = l1.v - l2.v
                        lat_avg = (l1.start_lat + l2.start_lat) / 2
                        cos_lat = cos(radians(lat_avg))
                        scale = np.array([cos_lat, 1.0])
                        P0_nm = P0 * 60.0 * scale
                        Vrel_nm = Vrel * 60.0 * scale

                        a = np.dot(Vrel_nm, Vrel_nm)
                        if a > 1e-15:
                            t_min_rel = -np.dot(P0_nm, Vrel_nm) / a
                            t_min_seg = np.clip(t_min_rel, 0, t_end - t_start)
                        else:
                            t_min_seg = 0

                        t_check = t_start + t_min_seg
                        p1 = interpolate_position(
                            l1.start_lat,
                            l1.start_lon,
                            l1.end_lat,
                            l1.end_lon,
                            (t_check - l1.t0) / l1.duration,
                        )
                        p2 = interpolate_position(
                            l2.start_lat,
                            l2.start_lon,
                            l2.end_lat,
                            l2.end_lon,
                            (t_check - l2.t0) / l2.duration,
                        )
                        dist = haversine(p1[0], p1[1], p2[0], p2[1])
                        if dist < min_dist:
                            min_dist = dist
                            # Capture the center point of the conflict
                            conflict_lat = (p1[0] + p2[0]) / 2
                            conflict_lon = (p1[1] + p2[1]) / 2

                conflicts.append(
                    {
                        "time": int((intervals[0][0] + intervals[0][1]) / 2),
                        "acid1": acid1,
                        "acid2": acid2,
                        "lat": conflict_lat,
                        "lon": conflict_lon,
                        "intervals": intervals,
                        "duration": int(sum(i[1] - i[0] for i in intervals)),
                        "dist": min_dist,
                        "alt_diff": abs(f1["altitude"] - f2["altitude"]),
                    }
                )

        return conflicts

    def check_pair_conflict(self, f1, f2):
        legs1 = self._calculate_legs_for_flight(f1)
        legs2 = self._calculate_legs_for_flight(f2)
        intervals = []

        for l1 in legs1:
            for l2 in legs2:
                t_start = max(l1.t0, l2.t0)
                t_end = min(l1.t1, l2.t1)
                if t_start >= t_end:
                    continue
                if abs(l1.alt - l2.alt) >= 2000:
                    continue

                # 1. Fast Quadratic Pruning
                A = l1.p0 + l1.v * (t_start - l1.t0)
                B = l2.p0 + l2.v * (t_start - l2.t0)
                P0 = A - B
                Vrel = l1.v - l2.v
                lat_avg = (l1.start_lat + l2.start_lat) / 2
                cos_lat = cos(radians(lat_avg))
                scale = np.array([cos_lat, 1.0])
                P0_nm = P0 * 60.0 * scale
                Vrel_nm = Vrel * 60.0 * scale

                a = np.dot(Vrel_nm, Vrel_nm)
                b = 2 * np.dot(P0_nm, Vrel_nm)
                c = np.dot(P0_nm, P0_nm) - (5.0**2)

                candidate = None
                if a > 1e-15:
                    disc = b**2 - 4 * a * c
                    if disc >= 0:
                        t1_r = (-b - np.sqrt(disc)) / (2 * a)
                        t2_r = (-b + np.sqrt(disc)) / (2 * a)
                        r0 = max(0, t1_r)
                        r1 = min(t_end - t_start, t2_r)
                        if r0 < r1:
                            candidate = [t_start + r0, t_start + r1]
                elif c <= 0:
                    candidate = [t_start, t_end]

                if not candidate:
                    continue

                # 2. Precision Refinement (Sub-second Bisection)
                # We find the exact moments using Haversine + Great Circle
                def get_dist(t):
                    p1 = interpolate_position(
                        l1.start_lat,
                        l1.start_lon,
                        l1.end_lat,
                        l1.end_lon,
                        (t - l1.t0) / l1.duration,
                    )
                    p2 = interpolate_position(
                        l2.start_lat,
                        l2.start_lon,
                        l2.end_lat,
                        l2.end_lon,
                        (t - l2.t0) / l2.duration,
                    )
                    return haversine(p1[0], p1[1], p2[0], p2[1])

                # Narrow the window to where it's truly < 5NM
                refined_start = candidate[0]
                refined_end = candidate[1]

                # Binary search for start
                low, high = t_start, t_end
                found_s = False
                for _ in range(15):  # ~0.03s precision over 1000s
                    mid = (low + high) / 2
                    if get_dist(mid) < 5.0:
                        high = mid
                        refined_start = mid
                        found_s = True
                    else:
                        low = mid

                # Binary search for end
                low, high = refined_start, t_end
                found_e = False
                for _ in range(15):
                    mid = (low + high) / 2
                    if get_dist(mid) < 5.0:
                        low = mid
                        refined_end = mid
                        found_e = True
                    else:
                        high = mid

                if found_s and found_e and refined_start < refined_end:
                    intervals.append([refined_start, refined_end])

        # Merge overlapping intervals
        intervals.sort()
        merged = []
        if intervals:
            cs, ce = intervals[0]
            for ns, ne in intervals[1:]:
                if ns <= ce + 1:
                    ce = max(ce, ne)
                else:
                    merged.append([cs, ce])
                    cs, ce = ns, ne
            merged.append([cs, ce])
        return merged

    def get_legs_for_flight(self, acid):
        return [l.to_dict() for l in self.legs if l.acid == acid]

    def get_conflict_pair_data(self, acid1, acid2):
        f1 = next((f for f in self.flights if f["ACID"] == acid1), None)
        f2 = next((f for f in self.flights if f["ACID"] == acid2), None)
        if not f1 or not f2:
            return None

        legs1 = self.get_legs_for_flight(acid1)
        legs2 = self.get_legs_for_flight(acid2)
        merged = self.check_pair_conflict(f1, f2)

        return {"legs1": legs1, "legs2": legs2, "intervals": merged}

    def get_constraints(self, plane_type):
        """Returns min/max altitude and speed for a given aircraft model."""
        if "Dash 8" in plane_type:
            return {
                "min_alt": 22000,
                "max_alt": 28000,
                "min_speed": 310,
                "max_speed": 410,
            }
        if any(x in plane_type for x in ["E195", "A220"]):
            # A220 is Narrow-body alt (28-39) but Regional speed (370-500)
            alt_min, alt_max = (
                (28000, 39000) if "A220" in plane_type else (22000, 28000)
            )
            return {
                "min_alt": alt_min,
                "max_alt": alt_max,
                "min_speed": 370,
                "max_speed": 500,
            }
        if any(x in plane_type for x in ["737", "A320", "A321"]):
            return {
                "min_alt": 28000,
                "max_alt": 39000,
                "min_speed": 415,
                "max_speed": 505,
            }
        if any(x in plane_type for x in ["787", "777", "A330"]):
            return {
                "min_alt": 31000,
                "max_alt": 43000,
                "min_speed": 430,
                "max_speed": 505,
            }
        if any(x in plane_type for x in ["767", "757", "A300"]):
            return {
                "min_alt": 28000,
                "max_alt": 41000,
                "min_speed": 410,
                "max_speed": 505,
            }
        return {"min_alt": 20000, "max_alt": 45000, "min_speed": 300, "max_speed": 600}
