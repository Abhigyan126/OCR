import os
import threading
from tkinter import Tk, PhotoImage, Label, Entry, Button, Canvas, Frame, Scrollbar, Toplevel, Text
from tkinter.messagebox import showerror
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import easyocr


class OCRApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR Image Viewer")
        self.default_path = "/Users/abhigyan/Desktop"  # Default folder path
        self.ocr = None
        self.load_icon()
        self.setup_ui()

    def load_icon(self):
        self.open_folder_icon = PhotoImage(file='Icons/icons8-folder-50.png').subsample(2, 2)
        self.scan_icon = PhotoImage(file='Icons/icons8-look-50.png').subsample(2, 2)
        self.ocr_icon = PhotoImage(file='Icons/icons8-ocr-50.png').subsample(2, 2)
        self.view_icon = PhotoImage(file='Icons/icons8-image-50.png').subsample(2, 2)

    def setup_ui(self):
        self.root.configure(bg="#f5deb3")

        Label(self.root, text="Folder Location:", bg="#f5deb3", fg="#8b4513").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.location_entry = Entry(self.root, width=50, bg="#f5deb3", fg="#8b4513")
        self.location_entry.grid(row=0, column=1, padx=5, pady=5)
        self.location_entry.insert(0, self.default_path)

        Button(self.root, image=self.open_folder_icon, command=self.browse_folder, bg="#f5deb3").grid(row=0, column=2, padx=5, pady=5)
        Button(self.root, image=self.scan_icon, command=self.scan_folder, bg="#f5deb3").grid(row=0, column=3, padx=5, pady=5)

        self.canvas = Canvas(self.root, bg="#f5deb3")
        self.canvas.grid(row=1, column=0, columnspan=4, sticky="nsew")

        self.scrollbar = Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=1, column=4, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.table_frame = Frame(self.canvas, bg="#f5deb3")
        self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")

        self.table_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Configure root grid for responsiveness
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.location_entry.delete(0, "end")
            self.location_entry.insert(0, folder_path)

    def scan_folder(self):
        folder_path = self.location_entry.get()
        if not os.path.exists(folder_path):
            showerror("Error", "The folder does not exist!")
            return

        self.clear_table()

        images = [f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        if not images:
            showerror("Error", "No images found in the folder!")
            return

        for idx, image_name in enumerate(images, start=1):
            image_path = os.path.join(folder_path, image_name)
            file_size = os.path.getsize(image_path) // 1024

            Label(self.table_frame, text=idx, relief="solid", width=5, bg="#f5deb3", fg="#8b4513").grid(row=idx, column=0, padx=5, pady=5)
            Label(self.table_frame, text=image_name, relief="solid", width=30, bg="#f5deb3", fg="#8b4513").grid(row=idx, column=1, padx=5, pady=5)
            Label(self.table_frame, text=f"{file_size} KB", relief="solid", width=10, bg="#f5deb3", fg="#8b4513").grid(row=idx, column=2, padx=5, pady=5)

            Button(self.table_frame, image=self.ocr_icon, command=lambda img=image_path: self.threaded_ocr(img), bg="#f5deb3").grid(
                row=idx, column=3, padx=5, pady=5
            )
            Button(self.table_frame, image=self.view_icon, command=lambda img=image_path: self.view_image(img), bg="#f5deb3").grid(
                row=idx, column=4, padx=5, pady=5
            )

    def clear_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

    def view_image(self, image_path):
        top = Toplevel(self.root, bg="#f5deb3")
        top.title(f"View Image - {os.path.basename(image_path)}")

        img = Image.open(image_path)
        img.thumbnail((800, 600))
        img_tk = ImageTk.PhotoImage(img)

        label = Label(top, image=img_tk, bg="#f5deb3")
        label.image = img_tk
        label.pack(padx=10, pady=10)

    def open_image(self, image_path):
        image = Image.open(image_path)
        img_arr = np.array(image, dtype=np.uint8)

        if self.ocr is None:
            self.ocr = easyocr.Reader(
                lang_list=["en"],
                gpu=True,
                model_storage_directory="EasyOCR\\model",
                download_enabled=False,
                user_network_directory="EasyOCR\\user_network",
            )

        response = self.ocr.readtext(image=img_arr)

        top = Toplevel(self.root, bg="#f5deb3")
        top.title(f"OCR Result - {os.path.basename(image_path)}")

        detected_text = "\n".join([text for _, text, _ in response])

        text_area = Text(top, wrap="word", height=15, width=50, bg="#f5deb3", fg="#8b4513")
        text_area.insert("1.0", detected_text)
        text_area.grid(row=0, column=0, padx=5, pady=5, columnspan=2)

        Button(top, text="Copy All", command=lambda: self.copy_to_clipboard(detected_text), bg="#f5deb3", borderwidth=0, highlightthickness=0).grid(row=1, column=0, padx=5, pady=5)
        Button(top, text="Close", command=top.destroy, bg="#f5deb3", borderwidth=0, highlightthickness=0).grid(row=1, column=1, padx=5, pady=5)

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def threaded_ocr(self, image_path):
        threading.Thread(target=self.open_image, args=(image_path,), daemon=True).start()


if __name__ == "__main__":
    root = Tk()
    app = OCRApplication(root)
    root.mainloop()
