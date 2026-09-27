"""
Ride / delivery tracking event simulator.

Simulates N drivers moving around a city and emits a continuous stream of
JSON events (location updates, trip lifecycle events).

Usage:
    python simulator.py                          # print to terminal forever
    python simulator.py --drivers 50 --interval 2
    python simulator.py --duration 30            # stop after 30 seconds
    python simulator.py --sink sqs --queue-url https://sqs.ap-south-1.amazonaws.com/123/ride-tracking-events

Sinks:
    stdout   -> prints one JSON event per line (default)
    file     -> appends JSON lines to events.jsonl
    sqs      -> sends to an AWS SQS queue in batches of 10 (needs boto3 + AWS creds)
"""

import argparse
import json
import os
import math
import random
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Hyderabad bounding box (roughly Gachibowli to Secunderabad)
CITY = {"lat_min": 17.38, "lat_max": 17.48, "lon_min": 78.34, "lon_max": 78.52}

# Named hotspots so demand clusters realistically (creates "surge" zones)
HOTSPOTS = [
    ("Hitec City", 17.4435, 78.3772),
    ("Gachibowli", 17.4401, 78.3489),
    ("Banjara Hills", 17.4156, 78.4347),
    ("Secunderabad", 17.4399, 78.4983),
    ("Kukatpally", 17.4849, 78.4138),
]

STATUSES = ["idle", "en_route_to_pickup", "en_route_to_customer"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def random_point_near(lat, lon, radius_km=1.5):
    """Random point within radius_km of a hotspot."""
    d = radius_km * math.sqrt(random.random())
    theta = random.uniform(0, 2 * math.pi)
    dlat = (d / 111.0) * math.cos(theta)
    dlon = (d / (111.0 * math.cos(math.radians(lat)))) * math.sin(theta)
    return round(lat + dlat, 6), round(lon + dlon, 6)


def random_city_point():
    hs = random.choice(HOTSPOTS)
    return random_point_near(hs[1], hs[2], radius_km=2.0)


@dataclass
class Driver:
    driver_id: str
    lat: float
    lon: float
    status: str = "idle"
    trip_id: str | None = None
    dest_lat: float | None = None
    dest_lon: float | None = None
    pickup: tuple | None = None
    dropoff: tuple | None = None
    promised_eta_min: float | None = None
    trip_started_at: float | None = None
    speed_kmph: float = 0.0
    heading: float = 0.0
    seq: int = field(default=0)

    def step(self, interval_s: float, events: list):
        """Advance the driver by one tick and append any events produced."""
        self.seq += 1

        if self.status == "idle":
            # Wander slowly; occasionally accept a new trip
            if random.random() < 0.15:
                self._start_trip(events)
            else:
                self.speed_kmph = random.uniform(0, 12)
                self._drift(interval_s)
        else:
            self.speed_kmph = max(5.0, random.gauss(28, 8))
            arrived = self._move_towards(self.dest_lat, self.dest_lon, interval_s)
            if arrived:
                if self.status == "en_route_to_pickup":
                    self.status = "en_route_to_customer"
                    self.dest_lat, self.dest_lon = self.dropoff
                    events.append(self._trip_event("trip_picked_up"))
                else:
                    events.append(self._trip_event("trip_completed"))
                    self._reset()

        # Every tick emits a location update (this is the bulk of the stream)
        events.append(self._location_event())

    # --- movement helpers -------------------------------------------------

    def _drift(self, interval_s):
        dist_km = self.speed_kmph * interval_s / 3600
        self.heading = (self.heading + random.uniform(-40, 40)) % 360
        self._advance(dist_km, self.heading)

    def _move_towards(self, tlat, tlon, interval_s) -> bool:
        remaining = haversine_km(self.lat, self.lon, tlat, tlon)
        dist_km = self.speed_kmph * interval_s / 3600
        if dist_km >= remaining:
            self.lat, self.lon = tlat, tlon
            return True
        bearing = math.degrees(
            math.atan2(
                math.sin(math.radians(tlon - self.lon)) * math.cos(math.radians(tlat)),
                math.cos(math.radians(self.lat)) * math.sin(math.radians(tlat))
                - math.sin(math.radians(self.lat)) * math.cos(math.radians(tlat))
                * math.cos(math.radians(tlon - self.lon)),
            )
        )
        # small road-like wobble
        self.heading = (bearing + random.uniform(-15, 15)) % 360
        self._advance(dist_km, self.heading)
        return False

    def _advance(self, dist_km, heading_deg):
        h = math.radians(heading_deg)
        self.lat += (dist_km / 111.0) * math.cos(h)
        self.lon += (dist_km / (111.0 * math.cos(math.radians(self.lat)))) * math.sin(h)
        self.lat = min(max(self.lat, CITY["lat_min"]), CITY["lat_max"])
        self.lon = min(max(self.lon, CITY["lon_min"]), CITY["lon_max"])
        self.lat, self.lon = round(self.lat, 6), round(self.lon, 6)

    # --- trip lifecycle ---------------------------------------------------

    def _start_trip(self, events):
        self.trip_id = f"trip_{uuid.uuid4().hex[:8]}"
        self.pickup = random_city_point()
        self.dropoff = random_city_point()
        total_km = haversine_km(self.lat, self.lon, *self.pickup) + haversine_km(*self.pickup, *self.dropoff)
        self.promised_eta_min = round(total_km / 25 * 60 + 5, 1)  # assume 25 km/h + 5 min buffer
        self.trip_started_at = time.time()
        self.status = "en_route_to_pickup"
        self.dest_lat, self.dest_lon = self.pickup
        events.append(self._trip_event("trip_requested"))
        events.append(self._trip_event("trip_accepted"))

    def _reset(self):
        self.status = "idle"
        self.trip_id = None
        self.dest_lat = self.dest_lon = None
        self.pickup = self.dropoff = None
        self.promised_eta_min = None
        self.trip_started_at = None

    # --- event builders ---------------------------------------------------

    def _base(self, event_type):
        return {
            "event_id": uuid.uuid4().hex,
            "event_type": event_type,
            "driver_id": self.driver_id,
            "trip_id": self.trip_id,
            "event_time": now_iso(),
            "seq": self.seq,
        }

    def _location_event(self):
        e = self._base("location_update")
        e.update({
            "lat": self.lat,
            "lon": self.lon,
            "speed_kmph": round(self.speed_kmph, 1),
            "heading": round(self.heading, 1),
            "status": self.status,
        })
        return e

    def _trip_event(self, event_type):
        e = self._base(event_type)
        e.update({
            "pickup_lat": self.pickup[0], "pickup_lon": self.pickup[1],
            "dropoff_lat": self.dropoff[0], "dropoff_lon": self.dropoff[1],
            "promised_eta_min": self.promised_eta_min,
        })
        return e


# --- sinks ----------------------------------------------------------------

class StdoutSink:
    def send(self, events):
        for e in events:
            print(json.dumps(e), flush=True)


class FileSink:
    def __init__(self, path="events.jsonl"):
        self.f = open(path, "a")

    def send(self, events):
        for e in events:
            self.f.write(json.dumps(e) + "\n")
        self.f.flush()


class SqsSink:
    def __init__(self, queue_url, region):
        import boto3  # only needed for this sink
        self.client = boto3.client("sqs", region_name=region)
        self.queue_url = queue_url

    def send(self, events):
        # SQS accepts at most 10 messages per SendMessageBatch call.
        for i in range(0, len(events), 10):
            chunk = events[i:i + 10]
            entries = [{"Id": str(j), "MessageBody": json.dumps(e)} for j, e in enumerate(chunk)]
            resp = self.client.send_message_batch(QueueUrl=self.queue_url, Entries=entries)
            if resp.get("Failed"):
                print(f"# {len(resp['Failed'])} messages failed to send", file=sys.stderr)


# --- realism knobs: duplicates and late events ----------------------------

def inject_noise(events, dup_rate=0.02, late_rate=0.01, late_buffer: list = None):
    """Phones resend and go offline; emit some duplicates and hold some events back."""
    out = []
    for e in events:
        if random.random() < late_rate and late_buffer is not None:
            late_buffer.append((time.time() + random.uniform(20, 90), e))  # release later
            continue
        out.append(e)
        if random.random() < dup_rate:
            out.append(dict(e))  # exact duplicate (same event_id) -> dedup in silver
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drivers", type=int, default=20)
    ap.add_argument("--interval", type=float, default=2.0, help="seconds between ticks")
    ap.add_argument("--duration", type=float, default=0, help="stop after N seconds (0 = forever)")
    ap.add_argument("--sink", choices=["stdout", "file", "sqs"], default="stdout")
    ap.add_argument("--queue-url", default=os.environ.get("SQS_QUEUE_URL"))
    ap.add_argument("--region", default="ap-south-1")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    sink = {"stdout": StdoutSink, "file": FileSink,
            "sqs": lambda: SqsSink(args.queue_url, args.region)}[args.sink]()
    if args.sink == "sqs" and not args.queue_url:
        sys.exit("--queue-url (or SQS_QUEUE_URL env var) is required for the sqs sink")

    drivers = []
    for i in range(args.drivers):
        lat, lon = random_city_point()
        drivers.append(Driver(driver_id=f"drv_{i:04d}", lat=lat, lon=lon,
                              heading=random.uniform(0, 360)))

    late_buffer: list = []
    start = time.time()
    sent = 0
    try:
        while True:
            tick_events = []
            for d in drivers:
                d.step(args.interval, tick_events)

            # release any late events whose time has come
            now = time.time()
            ready = [e for t, e in late_buffer if t <= now]
            late_buffer[:] = [(t, e) for t, e in late_buffer if t > now]

            batch = inject_noise(tick_events, late_buffer=late_buffer) + ready
            sink.send(batch)
            sent += len(batch)

            if args.duration and now - start >= args.duration:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        print(f"# stopped after {time.time() - start:.0f}s, {sent} events sent", file=sys.stderr)


if __name__ == "__main__":
    main()
