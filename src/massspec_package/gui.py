# massspec_package/gui.py

import os
import json
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from PIL import Image, ImageTk

from .data_processor import DataProcessor
from .voltage_plotter import VoltagePlotter

# paths to assets/settings
_LOGO_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'settings.json')


class App:
    def __init__(self, root):
        self.root = root

        # Base (unscaled) window size
        self.base_width = 800
        self.base_height = 500

        # Load settings
        self.cfg = {}
        if os.path.exists(_SETTINGS_PATH):
            try:
                self.cfg = json.load(open(_SETTINGS_PATH))
            except Exception:
                pass
        self.ui_scale = float(self.cfg.get('ui_scale', 1.0))

        # Initialize state vars
        self.measurement_folder = (
            self.cfg.get('measurement_folder')
            if self.cfg.get('measurement_folder') and os.path.isdir(self.cfg.get('measurement_folder'))
            else None
        )
        self.background_folder = (
            self.cfg.get('background_folder')
            if self.cfg.get('background_folder') and os.path.isdir(self.cfg.get('background_folder'))
            else None
        )
        self.data_processed = False
        self.total_files = 0
        self.processed_files = 0
        self.stop_event = threading.Event()

        # Placeholders for plot canvas and toolbar
        self.plot_canvas = None
        self.toolbar = None

        # Apply initial scaling to Tk widgets & fonts
        self.root.tk.call('tk', 'scaling', self.ui_scale)
        for fn in (
            "TkDefaultFont", "TkTextFont", "TkMenuFont",
            "TkHeadingFont", "TkCaptionFont", "TkSmallCaptionFont"
        ):
            try:
                f = tkfont.nametofont(fn)
                f.configure(size=int(f.cget('size') * self.ui_scale))
            except tk.TclError:
                pass
        self.root.option_add("*Font", tkfont.nametofont("TkDefaultFont"))

        # Window config and scaled geometry
        self.root.title('Background Substractor')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        icon = tk.PhotoImage(file=_LOGO_PATH)
        self.root.iconphoto(True, icon)
        self._icon_ref = icon
        self.root.geometry(f"{int(self.base_width * self.ui_scale)}x{int(self.base_height * self.ui_scale)}")

        # Load logo image once for footer use
        self.pil_logo = Image.open(_LOGO_PATH)
        ow, oh = self.pil_logo.size
        self.base_inner_size = (ow // 12, oh // 12)

        # Build UI components
        self._build_menu()
        self._build_tabs()
        self._build_setup_tab_widgets()
        self._build_plot_tab_widgets()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label='Open Measurement...', command=self.select_measurement_folder)
        filem.add_command(label='Open Background...', command=self.select_background_folder)
        filem.add_separator()
        filem.add_command(label='Exit', command=self.on_closing)
        menubar.add_cascade(label='File', menu=filem)

        settingsm = tk.Menu(menubar, tearoff=0)
        settingsm.add_command(label='Scale...', command=self.open_scale_dialog)
        menubar.add_cascade(label='Settings', menu=settingsm)

        self.root.config(menu=menubar)

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.tab_setup = ttk.Frame(self.notebook)
        self.tab_plot  = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_setup, text='Setup')
        self.notebook.add(self.tab_plot,  text='Plot')
        self.notebook.pack(fill='both', expand=True)

    def _build_setup_tab_widgets(self):
        # Title
        title_font = tkfont.Font(size=int(14 * self.ui_scale), weight='bold')
        ttk.Label(self.tab_setup,
                  text='Background Substractor',
                  font=title_font).pack(pady=10)

        # Folder selection
        frame = ttk.Frame(self.tab_setup, padding=10)
        frame.pack(fill='x')
        ttk.Label(frame,
                  text='Select Measurement Data Folder:').grid(row=0, column=0, sticky='w')
        ttk.Button(frame,
                   text='Browse',
                   command=self.select_measurement_folder).grid(row=0, column=1, padx=5)
        self.measurement_label = ttk.Label(
            frame,
            text=os.path.basename(self.measurement_folder)
                 if self.measurement_folder else 'No folder selected'
        )
        self.measurement_label.grid(row=1, column=0, columnspan=2,
                                    sticky='w', pady=(2,10))

        ttk.Label(frame,
                  text='Select Background Data Folder:').grid(row=2, column=0, sticky='w')
        ttk.Button(frame,
                   text='Browse',
                   command=self.select_background_folder).grid(row=2, column=1, padx=5)
        self.background_label = ttk.Label(
            frame,
            text=os.path.basename(self.background_folder)
                 if self.background_folder else 'No folder selected'
        )
        self.background_label.grid(row=3, column=0, columnspan=2,
                                    sticky='w', pady=(2,10))

        # Progress bar
        self.progress = ttk.Progressbar(self.tab_setup,
                                        orient='horizontal',
                                        length=500,
                                        mode='determinate')
        self.progress.pack(pady=20)

        # Action buttons
        btnf = ttk.Frame(self.tab_setup)
        btnf.pack(pady=10)
        self.process_button = ttk.Button(btnf,
                                         text='Process and Plot',
                                         command=self.start_processing)
        self.process_button.grid(row=0, column=0, padx=5)
        # "Plot Only" button removed

        self._toggle_process_button()

        # Logo & copyright only in Setup tab
        logo_img = ImageTk.PhotoImage(
            self.pil_logo.resize(self.base_inner_size,
                                 getattr(Image, 'Resampling', Image).LANCZOS)
        )
        self.logo_lbl = ttk.Label(self.tab_setup,
                                  image=logo_img,
                                  background='#f0f0f5')
        self.logo_lbl.image = logo_img
        self.logo_lbl.place(relx=1.0, rely=1.0,
                             anchor='se', x=-5, y=-5)
        self.cr_lbl = ttk.Label(self.tab_setup,
                                text='© 2025 MassSpec Package',
                                background='#f0f0f5')
        self.cr_lbl.place(relx=0.0, rely=1.0,
                          anchor='sw', x=5, y=-5)

    def _build_plot_tab_widgets(self):
        # Save button above plot
        self.save_button = ttk.Button(self.tab_plot,
                                      text='Save Data',
                                      command=self.save_data,
                                      state='disabled')
        self.save_button.pack(pady=5)
        # Container for toolbar and plot
        self.plot_container = ttk.Frame(self.tab_plot)
        self.plot_container.pack(fill='both', expand=True)

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
            self.apply_full_scale(save.get())
            dlg.destroy()
        ttk.Button(btnf, text='OK', command=on_ok).grid(row=0, column=0, padx=5)
        ttk.Button(btnf, text='Cancel', command=dlg.destroy).grid(row=0, column=1, padx=5)

    def apply_full_scale(self, save_default=False):
        # apply tk scaling and window size
        self.root.tk.call('tk', 'scaling', self.ui_scale)
        self.root.geometry(f"{int(self.base_width * self.ui_scale)}x{int(self.base_height * self.ui_scale)}")
        # scale fonts
        for fn in (
            "TkDefaultFont", "TkTextFont", "TkMenuFont",
            "TkHeadingFont", "TkCaptionFont", "TkSmallCaptionFont"
        ):
            try:
                f = tkfont.nametofont(fn)
                base = self.cfg.get(f'base_size_{fn}', f.cget('size'))
                f.configure(size=int(base * self.ui_scale))
                self.cfg[f'base_size_{fn}'] = base
            except tk.TclError:
                pass
        self.root.option_add("*Font", tkfont.nametofont("TkDefaultFont"))
        self.root.update_idletasks()
        if save_default:
            self.cfg['ui_scale'] = self.ui_scale
            with open(_SETTINGS_PATH, 'w') as f:
                json.dump(self.cfg, f)

    def select_measurement_folder(self):
        d = filedialog.askdirectory(title='Select Measurement Folder')
        if d:
            self.measurement_folder = d
            self.measurement_label.config(text=os.path.basename(d))
            self.cfg['measurement_folder'] = d
            self._toggle_process_button()

    def select_background_folder(self):
        d = filedialog.askdirectory(title='Select Background Folder')
        if d:
            self.background_folder = d
            self.background_label.config(text=os.path.basename(d))
            self.cfg['background_folder'] = d
            self._toggle_process_button()

    def _toggle_process_button(self):
        state = 'normal' if self.measurement_folder and self.background_folder else 'disabled'
        self.process_button.config(state=state)

    def count_total_files(self):
        meas = len([f for f in os.listdir(self.measurement_folder) if f.endswith('.data32')])
        back = len([f for f in os.listdir(self.background_folder) if f.endswith('.data32')])
        self.total_files = meas + back
        self.processed_files = 0

    def update_progress(self, _):
        self.processed_files += 1
        self.progress['value'] = (self.processed_files / self.total_files) * 100
        self.root.update_idletasks()

    def start_processing(self):
        if not (self.measurement_folder and self.background_folder):
            messagebox.showwarning('Folders Not Selected', 'Please select both folders first.')
            return
        self.count_total_files()
        self.progress['value'] = 0
        # Removed disabling of plot-only button
        self.save_button.config(state='disabled')
        self.data_processed = False
        self.stop_event.clear()
        threading.Thread(target=self._process_and_prepare, daemon=True).start()

    def _process_and_prepare(self):
        meas = DataProcessor(self.measurement_folder, self.update_progress, self.stop_event)
        back = DataProcessor(self.background_folder, self.update_progress, self.stop_event)
        vp = VoltagePlotter(meas, back)
        vp.calculate_difference()
        self.difference = vp.difference
        self.data_processed = True
        # Removed re-enabling of plot-only button
        self.root.after(0, lambda: self.save_button.config(state='normal'))
        self.root.after(0, lambda: self.notebook.select(self.tab_plot))
        self.root.after(0, self._embed_plot)

    def _embed_plot(self):
        if not self.data_processed:
            return
        # Clear previous toolbar and canvas
        for child in self.plot_container.winfo_children():
            child.destroy()

        # Create figure & axes
        fig, ax = plt.subplots(figsize=(3, 2))
        ax.plot(np.arange(len(self.difference)), self.difference)
        ax.set_xlabel('Index')
        ax.set_ylabel('Intensity')
        ax.grid(True)

        # Instantiate canvas
        self.plot_canvas = FigureCanvasTkAgg(fig, master=self.plot_container)

        # Add interactive toolbar above canvas
        self.toolbar = NavigationToolbar2Tk(self.plot_canvas, self.plot_container)
        self.toolbar.update()
        self.toolbar.pack(side='top', fill='x')

        # Pack canvas below toolbar
        self.plot_canvas.draw()
        self.plot_canvas.get_tk_widget().pack(fill='both', expand=True)

    def save_data(self):
        if not self.data_processed:
            messagebox.showwarning('No Data', 'Process data before saving.')
            return
        fpath = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text Files', '*.txt'), ('CSV Files', '*.csv')]
        )
        if not fpath:
            return
        try:
            with open(fpath, 'w') as f:
                for v in self.difference:
                    f.write(f"{v}\n")
            messagebox.showinfo('Saved', f'Data saved to:\n{fpath}')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def on_closing(self):
        self.stop_event.set()
        try:
            with open(_SETTINGS_PATH, 'w') as f:
                json.dump(self.cfg, f)
        except Exception:
            pass
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
