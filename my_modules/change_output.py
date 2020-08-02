import sys
import time

class SetIO():
    """with構文でI/Oを切り替えるためのクラス"""
    def __init__(self, filename: str):
        self.filename = filename

    def __enter__(self):
        sys.stdout = _STDLogger(out_file=self.filename)

    def __exit__(self, *args):
        sys.stdout = sys.__stdout__

class _STDLogger():
    """カスタムI/O"""
    def __init__(self, out_file='out.log'):
        self.log = open(out_file, "a+")

    def write(self, message):
        self.log.write(message)

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        pass
if __name__ == "__main__":
    """for i in range(10):
        with SetIO('test.log'):
            print(i)
            time.sleep(4)"""
    from tkinter import *
    from tkinter import ttk

    pbval = 0
    root = Tk()
    root.title('Progress')
    root.columnconfigure(0, weight=1);
    root.rowconfigure(0, weight=1);

    # Frame
    frame1 = ttk.Frame(root, padding=10)
    frame1.grid(sticky=(N,W,S,E))
    frame1.columnconfigure(0, weight=1);
    frame1.rowconfigure(0, weight=1);

    # プログレスバー (確定的)
    pb = ttk.Progressbar(
        frame1,
        orient=HORIZONTAL,
        length=200,
        mode='determinate')
    pb.configure(maximum=10, value=pbval)
    pb.grid(row=0, column=0, sticky=(N,E,S,W))

    root.mainloop()

    for i in range(20):
        time.sleep(4)
        pbval = pbval + 1
        pb.configure(value=pbval)
