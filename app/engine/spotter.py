import os
import json
import time
import requests
from bs4 import BeautifulSoup


class SpotterEngine:
    def __init__(self, cache_dir=".cache"):
        self.cache_dir = cache_dir
        self.images_dir = os.path.join(cache_dir, "aircraft_images")
        self.registry_path = os.path.join(cache_dir, "registry.json")
        os.makedirs(self.images_dir, exist_ok=True)

        # Mapping from flight data "Plane type" to Planespotters "actype"
        self.mapping = {
            "Boeing 757-200F": "s_boeing-757-200",
            "Boeing 737-800": "s_boeing-737-800",
            "Embraer E195-E2": "s_embraer-e195-e2",
            "Dash 8-400": "s_de-havilland-canada-dhc-8-400",
            "Boeing 787-9": "s_boeing-787-9",
            "Boeing 767-300F": "s_boeing-767-300",
            "Airbus A320": "s_airbus-a320-200",
            "Boeing 737 MAX 8": "s_boeing-737-max-8",
            "Airbus A300-600F": "s_airbus-a300-600",
            "Airbus A220-300": "s_airbus-a220-300",
            "Airbus A321": "s_airbus-a321-200",
            "Boeing 777-300ER": "s_boeing-777-300er",
        }

        self.registry = self._load_registry()

    def _load_registry(self):
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_registry(self):
        with open(self.registry_path, "w") as f:
            json.dump(self.registry, f, indent=2)

    def get_image(self, plane_type):
        """Returns the local path to the aircraft image, fetching if necessary."""
        if plane_type in self.registry:
            entry = self.registry[plane_type]
            if entry["status"] == "success":
                return entry["local_path"]
            # If failed, only retry after 24 hours
            if entry["status"] in ["not_found", "error"]:
                if time.time() - entry.get("last_attempt", 0) < 86400:
                    return None

        return self._fetch_and_cache(plane_type)

    def _fetch_and_cache(self, plane_type):
        actype = self.mapping.get(plane_type)
        if not actype:
            self.registry[plane_type] = {
                "status": "error",
                "message": "No mapping found for plane type",
                "last_attempt": time.time(),
            }
            self._save_registry()
            return None

        search_url = f"https://www.planespotters.net/photo/search?actype={actype}&sort=latest&s=hq"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            # Respectful delay before external call
            time.sleep(1)
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            soup = BeautifulSoup(response.text, "html.parser")
            photo_card = soup.find(class_="photo-card-clickable")

            if not photo_card:
                self.registry[plane_type] = {
                    "status": "not_found",
                    "last_attempt": time.time(),
                }
                self._save_registry()
                return None

            img_tag = photo_card.find("img")
            if not img_tag:
                return None

            src = img_tag.get("src")
            if not src or not isinstance(src, str):
                return None

            img_url: str = src

            # Save image
            slug = plane_type.lower().replace(" ", "-").replace("/", "-")
            ext = img_url.split(".")[-1].split("?")[0]  # strip query params if any
            local_filename = f"{slug}.{ext}"
            local_path = os.path.join(self.images_dir, local_filename)

            img_response = requests.get(img_url, headers=headers, timeout=10)
            with open(local_path, "wb") as f:
                f.write(img_response.content)

            self.registry[plane_type] = {
                "status": "success",
                "actype": actype,
                "local_path": f"/static/cache/aircraft_images/{local_filename}",
                "last_attempt": time.time(),
            }
            self._save_registry()
            return self.registry[plane_type]["local_path"]

        except Exception as e:
            self.registry[plane_type] = {
                "status": "error",
                "message": str(e),
                "last_attempt": time.time(),
            }
            self._save_registry()
            return None
