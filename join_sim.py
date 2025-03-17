import ctypes
import json
import sys
import time

from process_window import ProcessWindow
from tools import threaded


class JoinSim:
    
    def __init__(self, process: ProcessWindow) -> None:
        self.process = process
        self.running = False
        self.custom_points = None
        self.ensure_compatablility()

    def ensure_compatablility(self) -> None:

        if self.process.client_res[1] not in points:
            try:
                with open("points.json", "r") as f:
                    custom_points = json.load(f)[str(self.process.client_res[1])]

                if not self.validate_points(custom_points):
                    ctypes.windll.user32.MessageBoxW(
                        0, 
                        "Your custom points are not valid. Please edit the points.json file to match your resolution or change to 1080/1440p\n\nOne or more xy points are set to [0, 0] or exceed the resolution of your monitor",
                        "Invalid Points", 
                        1
                    )
                    sys.exit()

            except FileNotFoundError:
                with open("points.json", "w") as f:
                    json.dump({self.process.client_res[1]: points[1080]}, f, indent=4)

                ctypes.windll.user32.MessageBoxW(
                    0, 
                    f"Your resolution is not supported ({self.process.client_res[0]}x{self.process.client_res[1]}). A default template has been created for you. Please edit the points.json file to match your resolution or change to 1080/1440p",
                    "Resolution Error", 
                    1
                )
                sys.exit()

            except KeyError:
                ctypes.windll.user32.MessageBoxW(
                    0, 
                    f"Your resolution is not supported ({self.process.client_res[0]}x{self.process.client_res[1]}). Please edit the points.json file to match your resolution or change to 1080/1440p",
                    "Resolution Error", 
                    1
                )
                sys.exit()

    @threaded
    def run(self, server: str) -> None:

        if self.custom_points:
            points = self.custom_points

        self.setup()
        
        while self.running:
            for point in points[self.process.client_res[1]]:
                self.click_point(point)
                if point == "search":
                    self.process.write(server)

    def determine_state(self) -> str | None:

        found_points: list = []

        for point in points[self.process.client_res[1]]:
            x, y = points[self.process.client_res[1]][point]["xy"]
            rgb = points[self.process.client_res[1]][point]["rgb"]

            if self.process.await_pixel((x, y), rgb, 2, timeout=0.1):
                found_points.append(point)

        if found_points:
            return found_points[-1]

    def setup(self) -> None:
        
        next = self.determine_state()

        if next == "home":
            self.click_point("home")
        
        elif next == "select":
            return

    def start(self, server: str) -> None:
        
        if not self.running:
            self.running = True
            self.run(server)

    def stop(self) -> None:
        if self.running:
            self.running = False

    def validate_points(self, points: dict) -> bool:
        
        for key in points:

            x, y = points[key]["xy"]

            if x <= 0 or y <= 0 or x > self.process.client_res[0] or y > self.process.client_res[1]:            
                return False
            
        return True
    
    def click_point(self, point: str) -> None:

        x, y = points[self.process.client_res[1]][point]["xy"]
        rgb = points[self.process.client_res[1]][point]["rgb"]

        if self.process.await_pixel((x, y), rgb, 2, timeout=0.1):
            self.process.set_window_foreground()
            time.sleep(0.05)
            self.process.click(x, y)


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
        "home": {"xy": [1250, 1170], "rgb": [0, 0, 0]}, #good
        "select": {"xy": [630, 1029], "rgb": [125, 254, 246]}, #good 
        "search": {"xy": [2423,417], "rgb": [4, 34, 51]}, #good 
        "result": {"xy": [144, 437], "rgb": [218, 218, 149]}, #good
        "join": {"xy": [2255, 1262], "rgb": [254, 254, 254]}, #good
        "join_confirm": {"xy": [790, 1246], "rgb": [134, 79, 23]},
        "failed": {"xy": [1504, 974], "rgb": [2, 50, 79]},
        "back": {"xy": [246, 1176], "rgb": [146, 224, 236]},
    }
}