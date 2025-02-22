import tkinter as tk
from process import ProcessWindow
from logic import JoinSim

class App(tk.Tk):
    def __init__(self, process: ProcessWindow) -> None:
        super().__init__()
        self.title("ARK: Ascended Join-sim")
        self.geometry("400x180")
        self.configure(bg="#d9d9d9")
        self.resizable(False, False)
        self.join_sim = JoinSim(process)
        self.join_sim.ensure_compatablility()
        
        self.is_on = False
        
        self.entry_label = tk.Label(self, text="Server Number:", font=("Arial", 12), bg="#d9d9d9")
        self.entry_label.pack(pady=5)
        
        self.server_entry = tk.Entry(self, font=("Arial", 10), width=18)
        self.server_entry.pack(pady=5)
        
        self.button = tk.Button(self, text="OFF", font=("Arial", 12, "bold"), bg="#0275d8", fg="white", command=self.toggle, width=10, height=1)
        self.button.pack(pady=10)
        
        self.debug_label = tk.Label(self, text=f"{process.resolution[0]}x{process.resolution[1]}", font=("Arial", 8), bg="#d9d9d9", fg="black")
        self.debug_label.pack(pady=10)
    
    def toggle(self):
        if self.server_entry.get() or self.is_on:
            self.is_on = not self.is_on
            self.button.config(text="ON" if self.is_on else "OFF", bg="#5cb85c" if self.is_on else "#0275d8")

            if self.is_on:
                self.join_sim.start(self.server_entry.get().strip())

            if not self.is_on:
                self.join_sim.stop()