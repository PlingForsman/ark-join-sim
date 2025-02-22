from process import ProcessWindow
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

        self.process.set_window_foreground()
        
        while self.running:
            pass

    def determine_state(self) -> None:
        pass

    def setup(self, server: str) -> None:
        pass

    def start(self, server: str) -> None:
        
        if not self.running:
            self.running = True
            Thread(target=self.run, args=(server,)).start()

    def stop(self) -> None:
        if self.running:
            self.running = False
            self.thread = None

    def validate_points(self, points: dict) -> bool:
        
        for key in points:
            if points[key]["xy"] == [0, 0]: # Might wanna check if point is out of bounds here
                return False
            
        return True


points = {
    1080: {
        "home": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "select": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "list": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "search": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "result": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "join": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "join_confirm": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "failed": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "back": {"xy": [0, 0], "rgb": [0, 0, 0]},
    },
    1440: {
        "home": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "select": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "list": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "search": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "result": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "join": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "join_confirm": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "failed": {"xy": [0, 0], "rgb": [0, 0, 0]},
        "back": {"xy": [0, 0], "rgb": [0, 0, 0]},
    }
}