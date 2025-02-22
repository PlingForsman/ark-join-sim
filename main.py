from process import ProcessWindow
from app import App


if __name__ == "__main__":

    process = ProcessWindow()
    print(process.__repr__())

    gui = App(process)
    gui.mainloop()