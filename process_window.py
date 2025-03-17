import ctypes, win32gui, win32ui, win32api, win32con
from pathlib import Path
import cv2 as cv
import numpy as np
from pytesseract import pytesseract as ocr
import time
import subprocess
from typing import Literal

from tools import threaded, await_condition


class ProcessWindow:

    def __init__(self, title: str, game_id: int | None) -> None:

        ctypes.windll.user32.SetProcessDPIAware()
        self.hwnd: int = self.find_window(title)
        self.title: str = win32gui.GetWindowText(self.hwnd)
        self.game_id: int | None = game_id
        self.launched: bool = False
        self.client_res: tuple[int, int] = self.get_resolution("client")
        self.window_res: tuple[int, int] = self.get_resolution("window")
        self.display_mode: Literal["windowed", "fullscreen"] = self.get_display_mode()
        self.template_path: str = f"{Path(__file__).parent}/templates"
        ocr.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"

    def __str__(self) -> str:
        return (
            f"HWND: {self.hwnd}",
            f"Title: {self.title}",
            f"Game ID: {self.game_id}",
            f"Game launched: {self.launched}",
            f"Window resolution: {self.window_res[0]}x{self.window_res[1]}",
            f"Client resolution: {self.client_res[0]}x{self.client_res[1]}",
            f"Display Mode: {self.display_mode}",
            f"Template Path: {self.template_path}",
            f"OCR Path: {ocr.tesseract_cmd}"
        )
    
    def find_window(self, title: str) -> None | int:

        hwnd = win32gui.FindWindow(None, title)

        if hwnd == 0:
            return None
        
        return hwnd

    def get_resolution(self, method: Literal["client", "window"]) -> tuple[int, int]:

        if method == "client":
            left, top, right, bot = win32gui.GetClientRect(self.hwnd)

        elif method == "window":
            left, top, right, bot = win32gui.GetWindowRect(self.hwnd)

        return (right - left, bot - top)
    
    def get_display_mode(self) -> Literal["fullscreen", "windowed"]:

        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)

        if style & win32con.WS_OVERLAPPEDWINDOW: # Windows says its a bordered window
            if self.client_res != self.window_res: # if window & client are the same we do not want to change behaviour
                return "windowed"
        
        return "fullscreen"

    def set_window_foreground(self) -> None:

        win32gui.SetForegroundWindow(self.hwnd)

    def has_crashed(self) -> bool:

        crash_str: list[str] = ["The UE-ShooterGame Game has crashed and will close", "Crash!"]

        for crash in crash_str:
            try:
                if self.find_window(crash): # Crash has been detected
                    self.launched = False
                    return True 

            except:
                pass # Crash window not found

        return False # No crash window was found 
    
    def screenshot(self) -> cv.Mat:

        # I dont recommend touching this shit

        width, height = self.window_res

        hwnd_dc = win32gui.GetWindowDC(self.hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        
        save_bit_map = win32ui.CreateBitmap()
        save_bit_map.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(save_bit_map)
        
        result = ctypes.windll.user32.PrintWindow(self.hwnd, save_dc.GetSafeHdc(), 2)
        
        bmp_info = save_bit_map.GetInfo()
        bmp_data = save_bit_map.GetBitmapBits(True)
        
        win32gui.DeleteObject(save_bit_map.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwnd_dc)
        
        if result == 1:
            screenshot = np.frombuffer(bmp_data, dtype=np.uint8)
            screenshot = screenshot.reshape((bmp_info['bmHeight'], bmp_info['bmWidth'], 4))

            if self.display_mode == "windowed":
                screenshot = self.crop(screenshot, (9, 38, (width - 9), (height - 9))) # Removing the window border thats added for some fucking reason

            return cv.cvtColor(screenshot, cv.COLOR_BGRA2BGR)

    def locate_template(self, template: str, confidence: float) -> tuple[int, int] | None:
        
        template: cv.Mat = cv.imread(f"{self.template_path}/{template}", cv.IMREAD_GRAYSCALE)
        image: cv.Mat = cv.cvtColor(self.screenshot(), cv.COLOR_BGR2GRAY)

        result: cv.Mat = cv.matchTemplate(image, template, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)

        if max_val > confidence:
            return (
                    max_loc[0] + (template.shape[1] // 2),
                    max_loc[1] + (template.shape[0] // 2)
                )

    def await_template(self, template: str, confidence: float, timeout: float) -> bool:
        
        return await_condition(lambda: self.locate_template(template, confidence), timeout)
    
    def get_pixel_color(self, xy: tuple[int, int]) -> tuple[int, int, int]:

        img: cv.Mat = cv.cvtColor(self.screenshot(), cv.COLOR_BGR2RGB)
        pixel_rgb: cv.Mat = img[xy[1], xy[0]]

        return pixel_rgb
            
    def match_pixel(self, xy: tuple[int, int], rgb: tuple[int, int, int], variance: int) -> bool:

        pixel_rgb = self.get_pixel_color(xy)
                
        return all(abs(pixel_rgb[i] - rgb[i]) <= variance for i in range(3))
    
    def await_pixel(self, xy: tuple[int, int], rgb: tuple[int, int, int], variance: int, timeout: float) -> bool:

        return await_condition(lambda: self.match_pixel(xy, rgb, variance), timeout)
    
    def crop(self, screenshot: cv.Mat, region: tuple[int, int, int, int]) -> cv.Mat:

        x1, y1, x2, y2 = region
        return screenshot[y1:y2, x1:x2]

    def press(self, key: int, duration: float = 0.05) -> None:

        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_KEYDOWN, key, 0)
        time.sleep(duration)
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_KEYUP, key, 0)

    def post_char(self, char: int) -> None:

        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_CHAR, char, 0)

    @threaded
    def hold(self, key: int, duration: float) -> None:

        self.press(key, duration)

    def click(self, x: int, y: int) -> None:

        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, y << 16 | x)
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_LBUTTONUP, 0,  y << 16 | x)

    def read_text(self, region: tuple[int, int, int, int], config: str | None) -> str:  

        img: cv.Mat = self.screenshot()[region[0]:region[1], region[2]:region[4]]
        
        return ocr.image_to_string(
            image=img,
            lang="eng",
            config=config
        )
    
    def launch_game(self) -> None:

        if not self.game_id:
            raise ValueError(f"Cannot launch '{self.title}' no game_id was provided")

        subprocess.run(f"start steam://rungameid/{self.game_id}",  shell=True)
        self.launched = True
        
        if not await_condition(lambda: self.find_window(self.title), 50):
            raise ValueError(f"Window '{self.title}' was not found within 50 seconds after being started")
        
        self.hwnd = self.find_window(self.title)
    
    def hotkey_to_key(self, hotkey: str) -> int | None:

        result = getattr(win32con, f"VK_{hotkey.upper()}", None)
        
        return result & 0xff
            
    def str_to_key(self, string: str) -> list[int]:
        
        vk_codes: list[int] = []
        for char in string:
            result = win32api.VkKeyScan(char)
            vk_code = result & 0xFF
            vk_codes.append(vk_code)

        return vk_codes
        
    def write(self, string: str, interval: float = 0) -> None:

        key_int: list[int] = self.str_to_key(string)

        for char in key_int:
            self.post_char(char)
            time.sleep(interval)

        
if __name__ == "__main__": 
    window = ProcessWindow("This PC", None)
    [print(i) for i in window.__str__()]
    window.launch_game()