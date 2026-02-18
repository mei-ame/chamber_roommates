import tkinter as tk
from tkinter import filedialog, messagebox
import roommate_optimizer

class RoommateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Room Assignment Tool")
        self.root.geometry("400x400")
        
        self.file_path = ""
        self.room_entries = []

        # File Section
        tk.Button(root, text="Select CSV File", command=self.select_file).pack(pady=20)
        self.file_label = tk.Label(root, text="No file selected", fg="blue")
        self.file_label.pack()

        # Room Section
        self.entry_frame = tk.Frame(root)
        self.entry_frame.pack(pady=10)
        
        btn_frame = tk.Frame(root)
        btn_frame.pack()
        tk.Button(btn_frame, text="+ Room", command=self.add_entry).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="- Room", command=self.remove_entry).pack(side=tk.LEFT, padx=5)

        # Action
        tk.Button(root, text="START OPTIMIZER", bg="green", fg="white", 
                  command=self.execute, font=("Arial", 12, "bold")).pack(pady=40)

        # Default to four per room
        for size in [4, 4, 4]: self.add_entry(size)

    def select_file(self):
        self.file_path = filedialog.askopenfilename()
        self.file_label.config(text=self.file_path.split("/")[-1])

    def add_entry(self, val=4):
        f = tk.Frame(self.entry_frame)
        f.pack()
        e = tk.Entry(f, width=10)
        e.insert(0, str(val))
        e.pack(side=tk.LEFT, pady=2)
        tk.Label(f, text=" People").pack(side=tk.LEFT)
        self.room_entries.append((f, e))

    def remove_entry(self):
        if self.room_entries:
            f, e = self.room_entries.pop()
            f.destroy()

    def execute(self):
        if not self.file_path:
            return messagebox.showerror("Error", "Select a file first!")
        
        try:
            caps = [int(item[1].get()) for item in self.room_entries]
            # Call the function from the other file!
            df_result, error = roommate_optimizer.assign_rooms(self.file_path, caps)
            
            if error:
                messagebox.showerror("Math Error", error)
            else:
                df_result.to_csv("RoomAssignments.csv", index=False)
                messagebox.showinfo("Success", "Saved to RoomAssignments.csv")
        except ValueError:
            messagebox.showerror("Input Error", "Enter valid numbers for room sizes.")

if __name__ == "__main__":
    root = tk.Tk()
    app = RoommateGUI(root)
    root.mainloop()