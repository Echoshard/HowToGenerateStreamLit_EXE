#pip install pillow pywin32

import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import win32api
import win32con
import win32gui
import ctypes

def convert_to_ico(image_path):
    # Convert PNG/JPEG to ICO file (256x256)
    img = Image.open(image_path)
    img = img.resize((256, 256), Image.LANCZOS)
    temp_ico = tempfile.NamedTemporaryFile(delete=False, suffix='.ico')
    img.save(temp_ico.name, format='ICO', sizes=[(256,256)])
    return temp_ico.name

def change_icon(exe_path, ico_path):
    # Load icon resource from ICO file
    ICOGROUP_ICON = 1
    # handle to the exe file
    hExe = win32api.BeginUpdateResource(exe_path, False)

    # Load icon data from ICO file, split into ICONDIR, ICONIMAGE, etc.
    with open(ico_path, 'rb') as f:
        ico_data = f.read()

    # Parse ICO file structure
    # We need to extract icon group and individual icon images

    # ICO header (ICONDIR)
    # typedef struct {
    #  WORD idReserved;   // Reserved (must be 0)
    #  WORD idType;       // Resource Type (1 for icons)
    #  WORD idCount;      // Number of images
    #  ICONDIRENTRY idEntries[idCount]; // Image directory entries
    # } ICONDIR;

    # ICONDIRENTRY structure
    #  BYTE bWidth;
    #  BYTE bHeight;
    #  BYTE bColorCount;
    #  BYTE bReserved;
    #  WORD wPlanes;
    #  WORD wBitCount;
    #  DWORD dwBytesInRes;
    #  DWORD dwImageOffset;

    import struct

    reserved, icon_type, count = struct.unpack('<HHH', ico_data[0:6])

    if reserved != 0 or icon_type != 1:
        raise ValueError("Not a valid ICO file")

    # Extract icon directory entries
    entries = []
    for i in range(count):
        entry_data = ico_data[6 + i * 16 : 6 + (i + 1) * 16]
        bWidth, bHeight, bColorCount, bReserved, wPlanes, wBitCount, dwBytesInRes, dwImageOffset = struct.unpack('<BBBBHHII', entry_data)
        entries.append({
            'bWidth': bWidth,
            'bHeight': bHeight,
            'bColorCount': bColorCount,
            'bReserved': bReserved,
            'wPlanes': wPlanes,
            'wBitCount': wBitCount,
            'dwBytesInRes': dwBytesInRes,
            'dwImageOffset': dwImageOffset,
            'entry_data': entry_data,
            'id': i + 1  # EXE icon group IDs start at 1
        })

    # Update RT_ICON resources
    for entry in entries:
        img_data = ico_data[entry['dwImageOffset']: entry['dwImageOffset'] + entry['dwBytesInRes']]
        win32api.UpdateResource(hExe, win32con.RT_ICON, entry['id'], img_data)

    # Create group icon resource (RT_GROUP_ICON)
    # It consists of an ICONDIR structure *without* dwImageOffset, replaced by resource IDs

    # Structure: WORD idReserved, WORD idType, WORD idCount
    # Then array of GRPICONDIRENTRY:
    # typedef struct {
    #   BYTE bWidth;
    #   BYTE bHeight;
    #   BYTE bColorCount;
    #   BYTE bReserved;
    #   WORD wPlanes;
    #   WORD wBitCount;
    #   DWORD dwBytesInRes;
    #   WORD nID;   <--- resource ID (icon image)
    # } GRPICONDIRENTRY;

    # Build header
    group_icon_header = struct.pack('<HHH', 0, 1, count)

    group_icon_entries = b''
    for entry in entries:
        group_icon_entries += struct.pack(
            '<BBBBHHIH',
            entry['bWidth'],
            entry['bHeight'],
            entry['bColorCount'],
            entry['bReserved'],
            entry['wPlanes'],
            entry['wBitCount'],
            entry['dwBytesInRes'],
            entry['id']  # resource ID
        )

    group_icon_resource = group_icon_header + group_icon_entries

    # Update group icon resource - name is 1 to replace the main icon
    win32api.UpdateResource(hExe, win32con.RT_GROUP_ICON, 1, group_icon_resource)

    win32api.EndUpdateResource(hExe, False)

    messagebox.showinfo("Success", "Icon changed successfully!")

class IconChangerGUI:
    def __init__(self, master):
        self.master = master
        master.title("EXE Icon Changer")

        self.image_path = None
        self.exe_path = None

        self.label1 = tk.Label(master, text="Select Image (PNG, JPEG):")
        self.label1.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        self.btn_select_image = tk.Button(master, text="Browse...", command=self.select_image)
        self.btn_select_image.grid(row=0, column=1, padx=5, pady=5)

        self.label2 = tk.Label(master, text="Select EXE file:")
        self.label2.grid(row=1, column=0, padx=5, pady=5, sticky='w')

        self.btn_select_exe = tk.Button(master, text="Browse...", command=self.select_exe)
        self.btn_select_exe.grid(row=1, column=1, padx=5, pady=5)

        self.btn_change = tk.Button(master, text="Change Icon", command=self.change_icon)
        self.btn_change.grid(row=2, column=0, columnspan=2, pady=10)

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if path:
            self.image_path = path
            self.label1.config(text=f"Image: {os.path.basename(path)}")

    def select_exe(self):
        path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if path:
            self.exe_path = path
            self.label2.config(text=f"EXE: {os.path.basename(path)}")

    def change_icon(self):
        if not self.image_path or not self.exe_path:
            messagebox.showwarning("Missing input", "Please select both an image and an EXE file.")
            return

        try:
            ico_file = convert_to_ico(self.image_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert image to ico:\n{e}")
            return

        try:
            change_icon(self.exe_path, ico_file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change EXE icon:\n{e}")
        finally:
            if os.path.exists(ico_file):
                os.remove(ico_file)

if __name__ == '__main__':
    root = tk.Tk()
    gui = IconChangerGUI(root)
    root.mainloop()