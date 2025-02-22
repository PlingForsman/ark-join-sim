import ctypes, win32gui, win32ui, win32api, win32con
from pathlib import Path
import cv2 as cv
import numpy as np
from pytesseract import pytesseract as ocr
import time
import subprocess

from typing import Literal
from tools import threaded, State


class ProcessWindow:

    def __init__(self) -> None:
        ctypes.windll.user32.SetProcessDPIAware()

        self.launched: bool = False
        self.hwnd: int = 0
        self.find_window("UnrealWindow", "ArkAscended")
        self.resolution: tuple[int, int] = self.get_resolution()
        self.template_path: str = f"{Path(__file__).parent}/templates"
        ocr.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"

    def __repr__(self) -> str:
        return (
            f"HWND: {self.hwnd}",
            f"Resolution: {self.resolution[0]}x{self.resolution[1]}",
            f"Template Path: {self.template_path}",
            f"OCR Path: {ocr.tesseract_cmd}"
        )
    
    def find_window(self, PyResourceId: str | None, window_title: str) -> int:

        hwnd = win32gui.FindWindow(PyResourceId, window_title)

        if hwnd == 0 and not self.launched:
            self.launch_game()

        elif hwnd == 0 and self.launched:
            raise ValueError(f"Window '{window_title}' was not found")
        
        elif hwnd != 0:
            self.launched = True
            self.hwnd = hwnd

    def get_resolution(self) -> tuple[int, int]:

        left, top, right, bot = win32gui.GetWindowRect(self.hwnd)

        return (right - left, bot - top)
    
    def set_window_foreground(self) -> None:

        win32gui.SetForegroundWindow(self.hwnd)

    def has_crashed(self) -> bool:

        crash_str: list[str] = ["The UE-ShooterGame Game has crashed and will close", "Crash!"]

        for crash in crash_str:
            try:
                if self.find_window(None, crash): # Crash has been detected
                    self.launched = False
                    return True 

            except:
                pass # Crash window not found

        return False # No crash window was found 
    
    def screenshot(self) -> cv.Mat:

        # I dont recommend touching this shit

        hwnd_dc = win32gui.GetWindowDC(self.hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        
        save_bit_map = win32ui.CreateBitmap()
        save_bit_map.CreateCompatibleBitmap(mfc_dc, self.resolution[0], self.resolution[1])
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
            return cv.cvtColor(screenshot, cv.COLOR_BGRA2BGR)

    def locate_template(self, template: str, confidence: float) -> tuple[int, int]:
        
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
        
        start = time.time()

        while time.time() - start <= timeout:

            if self.locate_template(template, confidence):
                return True

        return False
            
    def match_pixel(self, xy: tuple[int, int], rgb: tuple[int, int, int], variance: int) -> bool:

        img: cv.Mat = cv.cvtColor(self.screenshot(), cv.COLOR_BGR2RGB)
        pixel_rgb: cv.Mat = img[xy[1], xy[0]]
                
        return all(abs(pixel_rgb[i] - rgb[i]) <= variance for i in range(3))
    
    def crop(self, screenshot: cv.Mat, region: tuple[int, int, int, int]) -> cv.Mat:

        return screenshot[region[0]:region[1], region[2]:region[3]]

    def press(self, key: int, duration: float = 0.05) -> None:

        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_KEYDOWN, key, 0)
        time.sleep(duration)
        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_KEYUP, key, 0)

    def post_char(self, char: int) -> None:

        ctypes.windll.user32.PostMessageW(self.hwnd, win32con.WM_CHAR, char, 0)

    def await_pixel_match(self, xy: tuple[int, int], rgb: tuple[int, int, int], variance: int, timeout: float) -> bool:

        start = time.time()

        while time.time() - start <= timeout:

            if self.match_pixel(xy, rgb, variance):
                return True
            
        return False

    @threaded
    def hold(self, key: int, duration: float) -> None:

        self.press(key, duration)

    def click(self, button: Literal["left", "right"] = "left", xy: tuple[int, int] = None, clicks: int = 1, interval: float = 0) -> None:

        for i in range(clicks):
            ctypes.windll.user32.PostMessageW(
                self.hwnd, 
                win32con.WM_LBUTTONDOWN if button == "left" else win32con.WM_RBUTTONDOWN, 
                win32con.MK_LBUTTON if button == "left" else win32con.MK_RBUTTON, 
                xy[1] << 16 | xy[0] if xy else 0
            )
            time.sleep(0.05)
            ctypes.windll.user32.PostMessageW(
                self.hwnd, 
                win32con.WM_LBUTTONUP if button == "left" else win32con.WM_RBUTTONUP, 
                win32con.MK_LBUTTON if button == "left" else win32con.MK_RBUTTON,  
                xy[1] << 16 | xy[0] if xy else 0
            )
            time.sleep(interval)

    def read_text(self, region: tuple[int, int, int, int], config: str | None) -> str:  

        img: cv.Mat = self.screenshot()[region[0]:region[1], region[2]:region[4]]
        
        return ocr.image_to_string(
            image=img,
            lang="eng",
            config=config
        )
    
    def launch_game(self) -> None:

        subprocess.run(f"start steam://rungameid/2399830",  shell=True)
        start = time.time()
        self.launched = True
        print("Process: Launching ArkAscended")
        
        while time.time() - start <= 50:

            try:
                self.find_window("UnrealWindow", "ArkAscended")
                return 

            except ValueError:
                time.sleep(1)

        raise ValueError("Window 'ArkAscended' was not found within 50 seconds after being started")
    
    def str_to_key(self, string: str) -> int | list[int]:

        if len(string) == 1:
            result = win32api.VkKeyScan(string)
            vk_code = result & 0xFF
            return vk_code
        
        else:
            vk_codes: list = []
            for char in string:
                result = win32api.VkKeyScan(char)
                vk_code = result & 0xFF
                vk_codes.append(vk_code)

            return vk_codes
        
    def write(self, string: str, interval: float = 0) -> None:

        key_int = self.str_to_key(string)

        for char in key_int:
            self.post_char(char)
            time.sleep(interval)

        
if __name__ == "__main__": 
    window = ProcessWindow()
    print(window.__repr__())
