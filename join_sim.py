from process_window import ProcessWindow
from threading import Thread

import ctypes
import json
import sys

class JoinSim:
    def __init__(self, process: ProcessWindow) -> None:
        self.process = process
        self.running = False

    def ensure_compatablility(self) -> None:

        if self.process.resolution[1] not in points:
            try:
                with open("points.json", "r") as f:
                    custom_points = json.load(f)[str(self.process.resolution[1])]

                if not self.validate_points(custom_points):
                    ctypes.windll.user32.MessageBoxW(
                        0, 
                        "Your custom points are not valid. Please edit the points.json file to match your resolution or change to 1080/1440p\n\nOne or more xy points are set to [0, 0]",
                        "Invalid Points", 
                        1)
                    sys.exit()

            except FileNotFoundError:
                with open("points.json", "w") as f:
                    json.dump({self.process.resolution[1]: points[1080]}, f, indent=4)

                ctypes.windll.user32.MessageBoxW(
                    0, 
                    f"Your resolution is not supported ({self.process.resolution[0]}x{self.process.resolution[1]}). A default template has been created for you. Please edit the points.json file to match your resolution or change to 1080/1440p",
                    "Resolution Error", 
                    1)
                sys.exit()

    def run(self, server: str) -> None:

        next_action = self.determine_state()
        
        while self.running:
            pass

    def determine_state(self) -> str | None:

        found_points: list = []

        for point in points[self.process.resolution[1]]:
            x, y = points[self.process.resolution[1]][point]["xy"]
            rgb = points[self.process.resolution[1]][point]["rgb"]

            if self.process.await_pixel((x, y), rgb, 5, timeout=0.5):
                found_points.append(point)

        if found_points:
            return found_points[-1]

    def setup(self, server: str) -> None:
        pass

    def start(self, server: str) -> None:
        
        if not self.running:
            self.running = True
            Thread(target=self.run, args=(server,)).start()

    def stop(self) -> None:
        if self.running:
            self.running = False

    def validate_points(self, points: dict) -> bool:
        
        for key in points:

            x, y = points[key]["xy"]

            if x <= 0 or y <= 0 or x > self.process.resolution[0] or y > self.process.resolution[1]:            
                return False
            
        return True


points = {
    1080: {
        "home": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "select": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "search": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "result": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "join": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "join_confirm": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "failed": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "back": {"xy": [0, 0], "rgb": [0, 0, 0]},
    },
    1440: {
        "home": {"xy": [1250, 1170], "rgb": [0, 0, 0]},
        "select": {"xy": [630, 1029], "rgb": [125, 254, 246]},
        "search": {"xy": [2423,417], "rgb": [4, 34, 51]},
        "result": {"xy": [144, 437], "rgb": [218, 218, 149]},
        "join": {"xy": [2255, 1262], "rgb": [254, 254, 254]},
        "join_confirm": {"xy": [790, 1246], "rgb": [134, 79, 23]},
        "failed": {"xy": [1504, 974], "rgb": [2, 50, 79]},
        "back": {"xy": [246, 1176], "rgb": [146, 224, 236]},
    }
}