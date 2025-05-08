# intensity_over_time.py

import os
import re
import json
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from PIL import Image, ImageTk

# compatibility for Pillow <10 and >=10
try:
    resample_filter = Image.Resampling.LANCZOS
except AttributeError:
    resample_filter = Image.LANCZOS

# paths
_LOGO_PATH     = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'settings.json')

class DataProcessor:
    """
    Load .data32 files sorted in natural (human) order.
    """
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def load_file(self, file_path):
        try:
            return np.fromfile(file_path, dtype=np.uint32)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return np.array([])

    def get_files(self):
        if not self.folder_path:
            return []
        raw = [f for f in os.listdir(self.folder_path) if f.endswith(".data32")]
        def natural_key(fname):
            parts = re.split(r'(\d+)', fname)
            return [int(p) if p.isdigit() else p.lower() for p in parts]
        return sorted(raw, key=natural_key)

class VoltagePlotter:
    def __init__(self, processor):
        self.processor = processor
        self.x_min = 0
        self.x_max = None
        self.skip = 1

    def set_params(self, x_min, x_max, skip):
        self.x_min = x_min
        self.x_max = x_max
        self.skip = max(1, skip)

    def get_first_data(self):
        files = self.processor.get_files()
        if not files:
            return None, None
        path = os.path.join(self.processor.folder_path, files[0])
        data = self.processor.load_file(path)
        return files[0], data

    def get_intensity_over_time(self, progress_callback=None):
        files = self.processor.get_files()[::self.skip]
        xs, vals = [], []
        for i, fname in enumerate(files, start=1):
            arr = self.processor.load_file(os.path.join(self.processor.folder_path, fname))
            if arr.size:
                end = self.x_max if self.x_max and self.x_max < arr.size else arr.size
                vals.append(np.max(arr[self.x_min:end]))
            else:
                vals.append(np.nan)
            xs.append(i)
            if progress_callback:
                progress_callback(i)
        return xs, vals

class App:
    def __init__(self, root):
        self.root = root
        self.preview_after_id = None  # for debouncing preview updates

        # base (unscaled) window size
        self.base_w = 800
        self.base_h = 500

        # load settings
        self.cfg = {}
        self.ui_scale = 1.0
        if os.path.exists(_SETTINGS_PATH):
            try:
                self.cfg = json.load(open(_SETTINGS_PATH))
                self.ui_scale = float(self.cfg.get('ui_scale', 1.0))
            except Exception:
                pass

        # apply initial scaling
        self.root.tk.call('tk', 'scaling', self.ui_scale)
        self.root.geometry(f"{int(self.base_w * self.ui_scale)}x{int(self.base_h * self.ui_scale)}")

        # scale fonts
        for fn in ("TkDefaultFont","TkTextFont","TkMenuFont",
                   "TkHeadingFont","TkCaptionFont","TkSmallCaptionFont"):
            try:
                f = tkfont.nametofont(fn)
                base_size = self.cfg.get(f'base_size_{fn}', f.cget('size'))
                f.configure(size=int(base_size * self.ui_scale))
                self.cfg[f'base_size_{fn}'] = base_size
            except tk.TclError:
                pass
        self.root.option_add("*Font", tkfont.nametofont("TkDefaultFont"))

        self.root.title("Intensity over Time Analysis")
        # set window icon
        icon = ImageTk.PhotoImage(Image.open(_LOGO_PATH).resize((32,32), resample_filter))
        self.root.iconphoto(True, icon)
        self._icon_ref = icon

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.tab_folder    = ttk.Frame(self.notebook)
        self.tab_params    = ttk.Frame(self.notebook)
        self.tab_intensity = ttk.Frame(self.notebook)
        for tab, text in [
            (self.tab_folder,    'Folder'),
            (self.tab_params,    'Parameters'),
            (self.tab_intensity, 'Intensity')
        ]:
            self.notebook.add(tab, text=text)
        self.notebook.pack(fill='both', expand=True)

        # build menus and tabs
        self._build_menu()
        self._build_folder_tab()
        self._build_params_tab()
        self._build_intensity_tab()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        settingsm = tk.Menu(menubar, tearoff=0)
        settingsm.add_command(label='Scale...', command=self.open_scale_dialog)
        menubar.add_cascade(label='Settings', menu=settingsm)
        self.root.config(menu=menubar)

    def open_scale_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title('UI Scale')
        dlg.transient(self.root)
        dlg.grab_set()
        ttk.Label(dlg, text='UI Scale:').grid(row=0, column=0, padx=10, pady=10)
        var = tk.DoubleVar(value=self.ui_scale)
        ttk.Scale(dlg, from_=0.5, to=2.0, variable=var, orient='horizontal').grid(row=0, column=1, padx=10, pady=10)
        save = tk.BooleanVar()
        ttk.Checkbutton(dlg, text='Save as default', variable=save).grid(row=1, column=0, columnspan=2)
        btnf = ttk.Frame(dlg)
        btnf.grid(row=2, column=0, columnspan=2, pady=10)
        def on_ok():
            self.ui_scale = var.get()
            self.root.tk.call('tk', 'scaling', self.ui_scale)
            self.root.geometry(f"{int(self.base_w * self.ui_scale)}x{int(self.base_h * self.ui_scale)}")
            for fn in ("TkDefaultFont","TkTextFont","TkMenuFont",
                       "TkHeadingFont","TkCaptionFont","TkSmallCaptionFont"):
                try:
                    f = tkfont.nametofont(fn)
                    base_size = self.cfg.get(f'base_size_{fn}', f.cget('size'))
                    f.configure(size=int(base_size * self.ui_scale))
                except tk.TclError:
                    pass
            self.root.option_add("*Font", tkfont.nametofont("TkDefaultFont"))
            if save.get():
                self.cfg['ui_scale'] = self.ui_scale
                with open(_SETTINGS_PATH, 'w') as f:
                    json.dump(self.cfg, f)
            dlg.destroy()
        ttk.Button(btnf, text='OK', command=on_ok).grid(row=0, column=0, padx=5)
        ttk.Button(btnf, text='Cancel', command=dlg.destroy).grid(row=0, column=1, padx=5)

    def _build_folder_tab(self):
        pil_logo = Image.open(_LOGO_PATH)
        iw, ih = pil_logo.size
        logo_img = ImageTk.PhotoImage(pil_logo.resize((iw//12, ih//12), resample_filter))
        lbl_logo = ttk.Label(self.tab_folder, image=logo_img)
        lbl_logo.image = logo_img
        lbl_logo.place(relx=1.0, rely=1.0, anchor='se', x=-5, y=-5)

        lbl_cr = ttk.Label(self.tab_folder, text='© 2025 MassSpec Package')
        lbl_cr.place(relx=0.0, rely=1.0, anchor='sw', x=5, y=-5)

        ttk.Label(self.tab_folder, text="Select Measurement Folder:").pack(pady=10)
        ttk.Button(self.tab_folder, text="Browse...", command=self.select_folder).pack()
        self.folder_label = ttk.Label(self.tab_folder, text="No folder selected", foreground='gray')
        self.folder_label.pack(pady=5)

    def _build_params_tab(self):
        frame = ttk.Frame(self.tab_params, padding=10)
        frame.pack(fill='x')

        ttk.Label(frame, text="X Min:").grid(row=0, column=0)
        self.entry_min = ttk.Entry(frame, width=10)
        self.entry_min.grid(row=0, column=1, padx=5)

        ttk.Label(frame, text="X Max:").grid(row=0, column=2)
        self.entry_max = ttk.Entry(frame, width=10)
        self.entry_max.grid(row=0, column=3, padx=5)

        ttk.Label(frame, text="Skip Interval:").grid(row=1, column=0)
        self.entry_skip = ttk.Entry(frame, width=10)
        self.entry_skip.grid(row=1, column=1, padx=5)

        ttk.Button(frame, text="Proceed", command=self.proceed).grid(row=1, column=3, padx=5)

        self.canvas1_frame = ttk.Frame(self.tab_params)
        self.canvas1_frame.pack(fill='both', expand=True)

        # debounce live preview updates with 0.5s delay
        self.entry_min.bind("<KeyRelease>", self.schedule_preview)
        self.entry_max.bind("<KeyRelease>", self.schedule_preview)

    def _build_intensity_tab(self):
        self.progress = ttk.Progressbar(self.tab_intensity, orient='horizontal', mode='determinate')

        self.save_button = ttk.Button(
            self.tab_intensity,
            text="Save Intensity Data",
            command=self.save_intensity,
            state='disabled'
        )
        self.save_button.pack(pady=5)

        self.canvas2_frame = ttk.Frame(self.tab_intensity)
        self.canvas2_frame.pack(fill='both', expand=True)

    def select_folder(self):
        path = filedialog.askdirectory()
        if not path:
            return
        self.processor = DataProcessor(path)
        self.plotter   = VoltagePlotter(self.processor)
        self.folder_label.config(text=os.path.basename(path), foreground='black')

        self._preview_fname, self._preview_data = self.plotter.get_first_data()
        self.notebook.select(self.tab_params)
        self.update_preview()

    def schedule_preview(self, event=None):
        # reset any pending callback
        if self.preview_after_id:
            self.root.after_cancel(self.preview_after_id)
        # wait 500 ms after typing stops to update
        self.preview_after_id = self.root.after(500, self.update_preview)

    def update_preview(self):
        # clear the pending callback ID
        self.preview_after_id = None

        # clear old preview
        for c in self.canvas1_frame.winfo_children():
            c.destroy()

        data = getattr(self, '_preview_data', None)
        fname = getattr(self, '_preview_fname', '')

        if data is None:
            return

        # parse entries, default to full range if blank or invalid
        try:
            xmin = int(self.entry_min.get())
        except ValueError:
            xmin = 0
        try:
            xmax = int(self.entry_max.get())
        except ValueError:
            xmax = data.size
        # clamp
        xmin = max(0, xmin)
        xmax = min(data.size, xmax)

        fig, ax = plt.subplots(figsize=(5,3), tight_layout=True)
        ax.plot(data)

        # only highlight the selected region
        if xmin < xmax:
            ax.axvspan(xmin, xmax, color='skyblue', alpha=0.3)

        ax.grid(True)
        ax.set_title(fname)
        ax.set_xlabel('Index')
        ax.set_ylabel('Value')

        canvas = FigureCanvasTkAgg(fig, master=self.canvas1_frame)
        toolbar = NavigationToolbar2Tk(canvas, self.canvas1_frame)
        toolbar.update()
        toolbar.pack(side='top', fill='x')
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def proceed(self):
        try:
            xmin = int(self.entry_min.get()) if self.entry_min.get() else 0
            xmax = int(self.entry_max.get()) if self.entry_max.get() else None
            skip = int(self.entry_skip.get()) if self.entry_skip.get() else 1
        except ValueError:
            messagebox.showerror("Error", "Invalid parameters.")
            return

        self.plotter.set_params(xmin, xmax, skip)

        total = len(self.processor.get_files()[::self.plotter.skip])
        self.progress['maximum'] = total
        self.progress['value'] = 0
        self.progress.pack(fill='x', padx=10, pady=5)

        self.plot_intensity()
        self.save_button.config(state='normal')
        self.notebook.select(self.tab_intensity)

    def _update_progress(self, count):
        self.progress['value'] = count
        self.progress.update_idletasks()

    def plot_intensity(self):
        for c in self.canvas2_frame.winfo_children():
            c.destroy()

        xs, vals = self.plotter.get_intensity_over_time(progress_callback=self._update_progress)
        self.progress.pack_forget()

        fig, ax = plt.subplots(figsize=(5,3), tight_layout=True)
        ax.plot(xs, vals, marker='o')
        ax.grid(True)
        ax.set_xlabel('File Index')
        ax.set_ylabel('Max Value')
        ax.set_title('Intensity over Time')

        canvas = FigureCanvasTkAgg(fig, master=self.canvas2_frame)
        toolb = NavigationToolbar2Tk(canvas, self.canvas2_frame)
        toolb.update()
        toolb.pack(side='top', fill='x')
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def save_intensity(self):
        xs, vals = self.plotter.get_intensity_over_time()
        fpath = filedialog.asksaveasfilename(defaultextension='.csv',
            filetypes=[('CSV Files','*.csv'), ('Text Files','*.txt')])
        if not fpath:
            return
        try:
            with open(fpath, 'w') as f:
                f.write('Index,MaxValue\n')
                for x, v in zip(xs, vals):
                    f.write(f"{x},{v}\n")
            messagebox.showinfo('Saved', f'Intensity data saved to:\n{fpath}')
        except Exception as e:
            messagebox.showerror('Error', str(e))

if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
