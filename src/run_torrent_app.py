from tkinter import Tk, messagebox
from torrent_gui import TorrentGUI

def main():
    try:
        root = Tk()
        app = TorrentGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"The application crashed: {str(e)}")

if __name__ == "__main__":
    main()