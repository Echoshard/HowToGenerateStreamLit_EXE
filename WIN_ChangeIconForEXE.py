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
from win32com.client import Dispatch
import subprocess
import shutil

def convert_to_ico(image_path, output_path=None):
    # Convert PNG/JPEG to ICO file (256x256)
    img = Image.open(image_path)
    img = img.resize((256, 256), Image.LANCZOS)
    if output_path:
        img.save(output_path, format='ICO', sizes=[(256,256)])
        return output_path
    else:
        temp_ico = tempfile.NamedTemporaryFile(delete=False, suffix='.ico')
        img.save(temp_ico.name, format='ICO', sizes=[(256,256)])
        return temp_ico.name

def change_exe_icon(exe_path, ico_path):
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

    messagebox.showinfo("Success", "EXE Icon changed successfully!")

def find_csc():
    # Common paths for .NET Framework C# compiler
    paths = [
        r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def create_csharp_launcher(bat_path, ico_path):
    csc_path = find_csc()
    if not csc_path:
        # Fallback: try using 'csc' from PATH
        csc_path = "csc.exe"
        try:
           subprocess.run([csc_path, "/?"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
           raise Exception("Could not find C# compiler (csc.exe). Please install .NET Framework or add csc to PATH.")

    bat_filename = os.path.basename(bat_path)
    exe_name = os.path.splitext(bat_filename)[0] + ".exe"
    output_exe_path = os.path.join(os.path.dirname(bat_path), exe_name)

    # C# Source Template
    # We escape curly braces for python format string by doubling them {{ }}
    csharp_code = f"""
using System;
using System.Diagnostics;
using System.IO;

namespace BatLauncher {{
    class Program {{
        static void Main(string[] args) {{
            try {{
                string batFile = "{bat_filename}";
                string exeDir = AppDomain.CurrentDomain.BaseDirectory;
                string batPath = Path.Combine(exeDir, batFile);
                
                if (!File.Exists(batPath)) {{
                    Console.WriteLine("Error: Could not find " + batFile);
                    Console.WriteLine("Expected at: " + batPath);
                    Console.WriteLine("Press any key to exit...");
                    Console.ReadKey();
                    return;
                }}
                
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = batPath;
                psi.UseShellExecute = true;
                
                if (args.Length > 0) {{
                    string allArgs = "";
                    foreach (var arg in args) {{
                         allArgs += " \\"" + arg + "\\"";
                    }}
                    psi.Arguments = allArgs;
                }}
                
                Process p = Process.Start(psi);
                p.WaitForExit();
            }} catch (Exception ex) {{
                Console.WriteLine("Error launching batch file: " + ex.Message);
                Console.ReadKey();
            }}
        }}
    }}
}}
"""
    
    # Create temp directory for compilation
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "launcher.cs")
        with open(source_path, "w") as f:
            f.write(csharp_code)
        
        # Compile command
        # /target:winexe -> Windows app (no console window for the launcher itself)
        # /win32icon:... -> Embeds the icon
        cmd = [
            csc_path,
            "/target:winexe",
            f"/out:{output_exe_path}",
            f"/win32icon:{ico_path}",
            source_path
        ]
        
        # Hide compiler output window logic
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # Run compilation
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Compilation failed:\\n{stdout.decode()}\\n{stderr.decode()}")
            
    return output_exe_path

class IconChangerGUI:
    def __init__(self, master):
        self.master = master
        master.title("Icon Changer (EXE & BAT)")

        self.image_path = None
        self.file_path = None

        self.label1 = tk.Label(master, text="Select Image (PNG, JPEG):")
        self.label1.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        self.btn_select_image = tk.Button(master, text="Browse...", command=self.select_image)
        self.btn_select_image.grid(row=0, column=1, padx=5, pady=5)

        self.label2 = tk.Label(master, text="Select EXE or BAT file:")
        self.label2.grid(row=1, column=0, padx=5, pady=5, sticky='w')

        self.btn_select_file = tk.Button(master, text="Browse...", command=self.select_file)
        self.btn_select_file.grid(row=1, column=1, padx=5, pady=5)

        self.btn_change = tk.Button(master, text="Process", command=self.process_file)
        self.btn_change.grid(row=2, column=0, columnspan=2, pady=10)

        # Instructions label
        self.lbl_info = tk.Label(master, text="Note: For BAT files, a launcher .EXE will be created.", fg="gray")
        self.lbl_info.grid(row=3, column=0, columnspan=2, pady=5)

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if path:
            self.image_path = path
            self.label1.config(text=f"Image: {os.path.basename(path)}")

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Executable or Batch", "*.exe;*.bat"), ("Executable", "*.exe"), ("Batch", "*.bat")])
        if path:
            self.file_path = path
            self.label2.config(text=f"File: {os.path.basename(path)}")

    def process_file(self):
        if not self.image_path or not self.file_path:
            messagebox.showwarning("Missing input", "Please select both an image and a target file.")
            return

        ext = os.path.splitext(self.file_path)[1].lower()

        try:
            if ext == '.exe':
                # For EXEs, we can use a temp ICO and inject it
                ico_file = convert_to_ico(self.image_path)
                try:
                    change_exe_icon(self.file_path, ico_file)
                finally:
                    if os.path.exists(ico_file):
                        os.remove(ico_file)
            
            elif ext == '.bat':
                # For BATs, generate a C# wrapper and compile it
                # We need a temp .ico file for the compiler
                ico_file = convert_to_ico(self.image_path)
                
                try:
                    created_exe = create_csharp_launcher(self.file_path, ico_file)
                    messagebox.showinfo("Success", f"Created exe launcher: {os.path.basename(created_exe)}\n\n(It launches {os.path.basename(self.file_path)})")
                except Exception as e:
                     messagebox.showerror("Error", f"Failed to create EXE launcher:\n{e}")
                finally:
                    if os.path.exists(ico_file):
                        os.remove(ico_file)
            
            else:
                messagebox.showerror("Error", "Unsupported file type. Please select .exe or .bat")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")

if __name__ == '__main__':
    root = tk.Tk()
    gui = IconChangerGUI(root)
    root.mainloop()
