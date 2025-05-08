# single_waveform.py

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

_LOGO_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'settings.json')

class DataProcessor:
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
        raw = [f for f in os.listdir(self.folder_path) if f.endswith('.data32')]
        def natural_key(fn):
            parts = re.split(r'(\d+)', fn)
            return [int(p) if p.isdigit() else p.lower() for p in parts]
        return sorted(raw, key=natural_key)

class VoltagePlotter:
    def __init__(self, processor):
        self.processor = processor
        self.selected = []

    def set_selected(self, files):
        self.selected = files

    def get_waveforms(self):
        data = {}
        for fn in self.selected:
            arr = self.processor.load_file(os.path.join(self.processor.folder_path, fn))
            if arr.size > 0:
                data[fn] = arr
        return data

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Single Waveform Analysis")
        
        # base (unscaled) window size
        self.base_w, self.base_h = 800, 600

        # load settings
        self.cfg = {}
        self.ui_scale = 1.0
        if os.path.exists(_SETTINGS_PATH):
            try:
                self.cfg = json.load(open(_SETTINGS_PATH))
                self.ui_scale = float(self.cfg.get('ui_scale', 1.0))
            except Exception:
                pass

        # apply initial scaling and font sizes
        self.root.tk.call('tk', 'scaling', self.ui_scale)
        self.root.geometry(f"{int(self.base_w * self.ui_scale)}x{int(self.base_h * self.ui_scale)}")
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

        # window icon
        icon = ImageTk.PhotoImage(Image.open(_LOGO_PATH).resize((32,32), resample_filter))
        self.root.iconphoto(True, icon)
        self._icon_ref = icon

        # legend option and window placeholder
        self.legend_option = tk.StringVar(value='Inside')
        self.legend_window = None

        # setup notebook
        self.notebook = ttk.Notebook(self.root)
        self.tab_select = ttk.Frame(self.notebook)
        self.tab_plot   = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_select, text='Select')
        self.notebook.add(self.tab_plot,   text='Plot')
        self.notebook.pack(fill='both', expand=True)

        # menus
        self._build_menu()

        # tabs
        self._build_select_tab()
        self._build_plot_tab()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        settings = tk.Menu(menubar, tearoff=0)
        settings.add_command(label='Scale...', command=self.open_scale_dialog)
        menubar.add_cascade(label='Settings', menu=settings)
        self.root.config(menu=menubar)

    def open_scale_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title('UI Scale')
        dlg.transient(self.root)
        dlg.grab_set()
        ttk.Label(dlg, text='UI Scale:').grid(row=0, column=0, padx=10, pady=10)
        var = tk.DoubleVar(value=self.ui_scale)
        ttk.Scale(dlg, from_=0.5, to=2.0, variable=var, orient='horizontal').grid(row=0, column=1, padx=10)
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

    def _build_select_tab(self):
        frame = ttk.Frame(self.tab_select, padding=10)
        frame.pack(fill='x')
        ttk.Label(frame, text='Select Measurement Folder:').grid(row=0, column=0, sticky='w')
        ttk.Button(frame, text='Browse', command=self.select_folder).grid(row=0, column=1, padx=5)
        self.folder_label = ttk.Label(frame, text='No folder selected', foreground='gray')
        self.folder_label.grid(row=1, column=0, columnspan=2, sticky='w', pady=(2,10))

        self.listbox = tk.Listbox(self.tab_select, selectmode='multiple')
        self.listbox.pack(fill='both', expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(self.tab_select)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text='Proceed', command=self.proceed).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text='Close',   command=self.root.destroy).grid(row=0, column=1, padx=5)

        # footer logo
        pil = Image.open(_LOGO_PATH)
        iw, ih = pil.size
        logo = ImageTk.PhotoImage(pil.resize((iw//12, ih//12), resample_filter))
        lbl = ttk.Label(self.tab_select, image=logo)
        lbl.image = logo
        lbl.place(relx=1.0, rely=1.0, anchor='se', x=-5, y=-5)
        # footer copyright
        cr = ttk.Label(self.tab_select, text='© 2025 MassSpec Package')
        cr.place(relx=0.0, rely=1.0, anchor='sw', x=5, y=-5)

    def _build_plot_tab(self):
        opt_frame = ttk.Frame(self.tab_plot, padding=5)
        opt_frame.pack(fill='x')
        ttk.Label(opt_frame, text='Legend:').pack(side='left')
        self.legend_combo = ttk.Combobox(opt_frame, textvariable=self.legend_option,
                                        values=['Inside', 'None', 'Separate Window'],
                                        state='readonly')
        self.legend_combo.pack(side='left', padx=5)
        self.legend_combo.bind('<<ComboboxSelected>>', lambda e: self.update_legend())

        self.plot_container = ttk.Frame(self.tab_plot)
        self.plot_container.pack(fill='both', expand=True)

        self.save_btn = ttk.Button(self.tab_plot, text='Save Data', state='disabled', command=self.save)
        self.save_btn.pack(pady=5)

    def select_folder(self):
        path = filedialog.askdirectory()
        if not path: return
        self.processor = DataProcessor(path)
        self.plotter   = VoltagePlotter(self.processor)
        files = self.processor.get_files()
        self.listbox.delete(0, tk.END)
        for f in files:
            self.listbox.insert(tk.END, f)
        self.folder_label.config(text=os.path.basename(path), foreground='black')

    def proceed(self):
        sel = [self.listbox.get(i) for i in self.listbox.curselection()]
        if not sel:
            messagebox.showwarning('No Selection', 'Please select one or more files.')
            return
        self.plotter.set_selected(sel)
        data = self.plotter.get_waveforms()

        # clear plot container
        for c in self.plot_container.winfo_children():
            c.destroy()

        # initial plot
        self.fig, self.ax = plt.subplots(figsize=(7,4))
        for fn, arr in data.items():
            self.ax.plot(np.arange(len(arr)), arr, label=fn)
        self.ax.set_title('Selected Waveforms')
        self.ax.grid(True)

        # embed
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_container)
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_container)
        toolbar.update(); toolbar.pack(side='top', fill='x')
        self.canvas.draw(); self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # update legend placement
        self.update_legend()

        self.save_btn.config(state='normal')
        self.notebook.select(self.tab_plot)

    def update_legend(self):
        if not hasattr(self, 'ax'):
            return
        # remove existing legend
        if hasattr(self, 'legend') and self.legend:
            try:
                self.legend.remove()
            except:
                pass
            self.legend = None
        # destroy legend window
        if hasattr(self, 'legend_window') and self.legend_window:
            try:
                self.legend_window.destroy()
            except:
                pass
            self.legend_window = None

        opt = self.legend_option.get()
        if opt == 'Inside':
            self.legend = self.ax.legend(loc='best')
        elif opt == 'Separate Window':
            # create a separate legend window with padding
            self.legend_window = tk.Toplevel(self.root)
            self.legend_window.title('Legend')
            self.legend_window.configure(padx=10, pady=10)

            # inner frame for extra padding
            container = ttk.Frame(self.legend_window, padding=(12,12,12,12))
            container.pack(fill='both', expand=True)

            # list each filename with vertical spacing
            for fn in self.plotter.selected:
                ttk.Label(container, text=fn).pack(anchor='w', pady=2)
        # 'None' => no legend

        self.canvas.draw()

    def save(self):
        data = self.plotter.get_waveforms()
        if not data:
            messagebox.showwarning('No Data', 'Nothing to save.')
            return
        fpath = filedialog.asksaveasfilename(defaultextension='.csv',
            filetypes=[('CSV','*.csv'),('Text','*.txt')])
        if not fpath:
            return
        key = lambda fn: [int(p) if p.isdigit() else p.lower() for p in re.split(r'(\d+)', fn)]
        waves = [data[fn] for fn in sorted(data, key=key)]
        maxl = max(len(w) for w in waves)
        with open(fpath, 'w') as f:
            f.write(','.join(sorted(data, key=key)) + '\n')
            for i in range(maxl):
                row = [str(w[i]) if i < len(w) else '' for w in waves]
                f.write(','.join(row) + '\n')
        messagebox.showinfo('Saved', f'Data saved to:\n{fpath}')

if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
