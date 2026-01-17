import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional
from app.engine.trajectory import FlightEngine
from app.engine.spotter import SpotterEngine
import pandas as pd
from datetime import datetime

load_dotenv()
MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")

app = FastAPI(title="planNAV")

# Mount static files
app.mount("/static/cache", StaticFiles(directory=".cache"), name="cache")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# Initialize Engine
DATA_FILE = "data/canadian_flights_250.json"
engine = FlightEngine(DATA_FILE)
spotter = SpotterEngine()

# Pre-compute expensive data on startup
print("Initializing Flight Engine data (Conflicts & Stats)...")
engine.get_stats()
print("Initialization complete.")


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard")
async def dashboard(request: Request, page: int = 1):
    # Use cached stats from engine
    stats = engine.get_stats()

    # Pagination
    per_page = 20
    total_pages = (len(engine.flights) + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_flights = engine.flights[start_idx:end_idx]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "flights": paginated_flights,
            "page": page,
            "total_pages": total_pages,
        },
    )


@app.get("/hotspots")
async def hotspots_page(request: Request):
    return templates.TemplateResponse(
        "hotspots.html",
        {
            "request": request,
            "mapbox_token": MAPBOX_TOKEN,
        },
    )


@app.get("/api/hotspots-data")
async def get_hotspots_data():
    conflicts = engine.find_conflicts()
    features = []

    for c in conflicts:
        # Weight based on separation severity (0 to 1)
        # Max weight 1.0 if dist is 0NM, weight 0.0 if dist is 5NM
        weight = max(0.1, (5.0 - c["dist"]) / 5.0)

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [c["lon"], c["lat"]]},
                "properties": {
                    "weight": weight,
                    "time": c["time"],
                    "acid1": c["acid1"],
                    "acid2": c["acid2"],
                    "dist": c["dist"],
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


@app.get("/api/conflict-data/{acid1}/{acid2}")
async def get_conflict_data(acid1: str, acid2: str):
    data = engine.get_conflict_pair_data(acid1, acid2)
    if not data:
        return {"error": "Not found"}
    return data


@app.get("/analyze-conflict/{acid1}/{acid2}")
async def analyze_conflict(request: Request, acid1: str, acid2: str):
    f1 = next((f for f in engine.flights if f["ACID"] == acid1), None)
    f2 = next((f for f in engine.flights if f["ACID"] == acid2), None)

    if not f1 or not f2:
        return "Not found"

    legs1 = engine.get_legs_for_flight(acid1)
    legs2 = engine.get_legs_for_flight(acid2)

    return templates.TemplateResponse(
        "partials/conflict_analysis.html",
        {
            "request": request,
            "acid1": acid1,
            "acid2": acid2,
            "flight1": f1,
            "flight2": f2,
            "legs1_count": len(legs1),
            "legs2_count": len(legs2),
            "mapbox_token": MAPBOX_TOKEN,
        },
    )


@app.get("/conflict-visualizer/{acid1}/{acid2}")
async def conflict_visualizer(request: Request, acid1: str, acid2: str):
    return templates.TemplateResponse(
        "partials/visualizer.html",
        {
            "request": request,
            "acid1": acid1,
            "acid2": acid2,
            "mapbox_token": MAPBOX_TOKEN,
        },
    )


@app.get("/conflicts")
@app.get("/conflicts/{acid1}/{acid2}")
async def conflicts_page(
    request: Request, acid1: Optional[str] = None, acid2: Optional[str] = None
):
    conflicts = engine.find_conflicts()
    unique_conflicts = []
    seen = set()
    for c in conflicts:
        pair = tuple(sorted([c["acid1"], c["acid2"]]))
        if pair not in seen:
            unique_conflicts.append(c)
            seen.add(pair)

    if not acid1 or not acid2:
        if unique_conflicts:
            c = unique_conflicts[0]
            return RedirectResponse(url=f"/conflicts/{c['acid1']}/{c['acid2']}")

    initial_analysis = None
    if acid1 and acid2:
        initial_analysis = {"acid1": acid1, "acid2": acid2}

    return templates.TemplateResponse(
        "conflicts.html",
        {
            "request": request,
            "conflicts": unique_conflicts,
            "initial_analysis": initial_analysis,
        },
    )


@app.get("/analyze")
async def analyze(request: Request):
    conflicts = engine.find_conflicts()
    # Deduplicate and group conflicts
    unique_conflicts = []
    seen = set()
    for c in conflicts:
        pair = tuple(sorted([c["acid1"], c["acid2"]]))
        if pair not in seen:
            unique_conflicts.append(c)
            seen.add(pair)

    return templates.TemplateResponse(
        "partials/conflicts.html", {"request": request, "conflicts": unique_conflicts}
    )


@app.get("/flight/{acid}")
async def flight_detail(request: Request, acid: str):
    flight = next((f for f in engine.flights if f["ACID"] == acid), None)
    if not flight:
        return "Flight not found"

    legs = engine.get_legs_for_flight(acid)

    return templates.TemplateResponse(
        "partials/flight_detail.html",
        {
            "request": request,
            "flight": flight,
            "legs_count": len(legs),
        },
    )


@app.get("/flight-image")
async def flight_image(request: Request, plane_type: str):
    image_url = spotter.get_image(plane_type)
    return templates.TemplateResponse(
        "partials/aircraft_image.html",
        {
            "request": request,
            "image_url": image_url,
            "plane_type": plane_type,
        },
    )
