from helper import create_slice_dict, volume_aggregator
from csv_handler import clean_csv_file_to_df
from config import set_env

import os
import pandas as pd
from socket_handler import start_server, get_data_socket
from conveyor import initialize_arduino, start_conveyor, stop_conveyor, close_conveyor_conn, listen_to_arduino
import threading
import tkinter as tk
from tkinter import messagebox

############################################################################################################
def main(df):
    # Main
    print(
        "-----------------------------\nExecuting Main\n-----------------------------"
    )
    # Calculations are done in mm and mm^3
    volume = volume_aggregator(df)

    # Get slicing information
    num_slices = int(input("Enter the number of slices: "))
    if num_slices <= 1:
        print("Invalid number of slices")
        return
    
    # Get cutting information
    cut_direction = None
    while cut_direction not in ["X", "Y"]:
        cut_direction = input("Which cutting direction X/Y: ").upper()
    set_env(cut_direction)
    
    # Create slice dict
    slice_data = create_slice_dict(
        num_slices=num_slices, volume=volume, cut_direction=cut_direction
    )
    volume_aggregator(df, slice_data=slice_data)

def start_gui(df, stop_event):
    def on_submit():
        try:
            num_slices = int(num_slices_entry.get())
            if num_slices <= 1:
                raise ValueError("Invalid number of slices")
            cut_direction = cut_direction_var.get()
            if cut_direction not in ["X", "Y"]:
                raise ValueError("Invalid cutting direction")
            set_env(cut_direction)
            main(df, num_slices, cut_direction)
            root.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    root = tk.Tk()
    root.title("Meat Slicer Configuration")

    tk.Label(root, text="Enter the number of slices:").pack()
    num_slices_entry = tk.Entry(root)
    num_slices_entry.pack()

    tk.Label(root, text="Select the cutting direction:").pack()
    cut_direction_var = tk.StringVar(value="X")
    tk.Radiobutton(root, text="X", variable=cut_direction_var, value="X").pack()
    tk.Radiobutton(root, text="Y", variable=cut_direction_var, value="Y").pack()

    tk.Button(root, text="Submit", command=on_submit).pack()

    root.mainloop()
    
# please set the filepath
project_path = os.path.dirname(os.path.abspath(__file__))
os.environ["filepath"] = "csv_files/eraser_data.csv"

if __name__ == "__main__":
    # Define for testing env
    env = 'Testing'

    # Initialize Arduino
    initialize_arduino()
    start_conveyor()
    
    # The sensor on the conveyor will auto-detect and stop the object
    if env != 'Testing':
        socket = start_server()
        df = get_data_socket(socket)
    else: # Testing
        df = pd.read_csv(os.path.join(project_path, "csv_files/eraser_data.csv"), header=None, dtype=str) 
        df = clean_csv_file_to_df(df, x_resolution=0.178, y_resolution=0.338)


    stop_event = threading.Event()
    arduino_thread = threading.Thread(target=listen_to_arduino, args=(stop_event,))
    arduino_thread.start()

    df = clean_csv_file_to_df(df, x_resolution=0.178, y_resolution=0.338)
    main(df)
    arduino_thread.join()