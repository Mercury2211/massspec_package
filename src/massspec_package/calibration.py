import os, json, threading, numpy as np, matplotlib.pyplot as plt, tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.signal import find_peaks
from PIL import Image, ImageTk

# Pillow compatibility
try:
    resample_filter = Image.Resampling.LANCZOS
except AttributeError:
    resample_filter = Image.LANCZOS

_LOGO_PATH     = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'settings.json')

# ───────────────────────── Draggable vertical line ──────────────────────────
class DraggableLine:
    def __init__(self, line, callback):
        self.line, self.callback, self._press = line, callback, None
        fig = line.figure
        fig.canvas.mpl_connect('button_press_event',    self._on_press)
        fig.canvas.mpl_connect('motion_notify_event',   self._on_move)
        fig.canvas.mpl_connect('button_release_event',  self._on_release)

    def _on_press(self, event):
        if event.inaxes != self.line.axes: return
        x0 = self.line.get_xdata()[0]
        tol = (self.line.axes.get_xlim()[1]-self.line.axes.get_xlim()[0])*0.01
        if abs(event.xdata-x0) < tol:
            self._press = (x0, event.xdata)

    def _on_move(self, event):
        if self._press is None or event.inaxes != self.line.axes: return
        x0, xpress = self._press
        newx = x0 + (event.xdata-xpress)
        self.line.set_xdata([newx, newx])
        self.callback(newx)
        self.line.figure.canvas.draw_idle()

    def _on_release(self, _): self._press = None


# ───────────────────────── Simple data processors ───────────────────────────
class DataProcessor:
    def __init__(self, folder, progress_cb=None, stop_ev=None):
        self.folder, self.cb, self.stop = folder, progress_cb, stop_ev
    def _decode(self, path):
        out=[]
        with open(path,'rb') as f:
            while not (self.stop and self.stop.is_set()):
                chunk=f.read(4)
                if not chunk: break
                out.append(int.from_bytes(chunk,'little'))
        return out
    def summed(self):
        mats=[]; files=[f for f in os.listdir(self.folder) if f.endswith('.data32')]
        for i,fn in enumerate(files):
            if self.stop and self.stop.is_set(): return np.array([])
            mats.append(self._decode(os.path.join(self.folder,fn)))
            if self.cb: self.cb(i+1)
        return np.sum(np.array(mats,dtype=np.float64),axis=0) if mats else np.array([])

class VoltagePlotter:
    def __init__(self, mea, bkg): self.mea, self.bkg = mea, bkg
    def calculate(self): self.diff = self.mea.summed() - self.bkg.summed()


# ────────────────────────────────── GUI ─────────────────────────────────────
class App:
    def __init__(self, root):
        self.root = root
        self.base_w, self.base_h = 850, 550
        self.stop_ev = threading.Event()
        self.title_var = tk.StringVar(value='TOF‑Calibrated Difference Plot')
        self._debounce_id, self._click_cids = None, []

        # load settings
        self.cfg, self.ui_scale = {}, 1.0
        if os.path.exists(_SETTINGS_PATH):
            try:
                self.cfg = json.load(open(_SETTINGS_PATH))
                self.ui_scale = float(self.cfg.get('ui_scale', 1.0))
            except Exception: pass

        # apply scaling
        root.tk.call('tk', 'scaling', self.ui_scale)
        root.geometry(f"{int(self.base_w*self.ui_scale)}x{int(self.base_h*self.ui_scale)}")
        for fn in ("TkDefaultFont","TkTextFont","TkMenuFont","TkHeadingFont",
                   "TkCaptionFont","TkSmallCaptionFont"):
            try:
                f = tkfont.nametofont(fn)
                f.configure(size=int(f.cget('size') * self.ui_scale))
            except tk.TclError: pass
        root.option_add("*Font", tkfont.nametofont("TkDefaultFont"))
        root.title('Calibration')
        icon = tk.PhotoImage(file=_LOGO_PATH); root.iconphoto(True, icon)

        # folders & Y‑cal mode
        self.meas_dir = self.cfg.get('measurement_folder') if os.path.isdir(self.cfg.get('measurement_folder','')) else None
        self.back_dir = self.cfg.get('background_folder')  if os.path.isdir(self.cfg.get('background_folder','' )) else None
        self.ycal_method = tk.StringVar(value='None')

        # build interface
        self._menu(); self._tabs(); self._footer()

    # ───────────────────────────────── menu ─────────────────────────────────
    def _menu(self):
        menu = tk.Menu(self.root)
        fm = tk.Menu(menu, tearoff=0)
        fm.add_command(label='Open Measurement…', command=self._pick_meas)
        fm.add_command(label='Open Background…',  command=self._pick_back)
        fm.add_separator(); fm.add_command(label='Exit', command=self._close)
        menu.add_cascade(label='File', menu=fm)

        sm = tk.Menu(menu, tearoff=0); sm.add_command(label='Scale…', command=self._scale_dlg)
        menu.add_cascade(label='Settings', menu=sm)
        self.root.config(menu=menu)

    # ───────────────────────────────── tabs ─────────────────────────────────
    def _tabs(self):
        nb = ttk.Notebook(self.root); self.nb = nb
        self.tab_setup, self.tab_raw, self.tab_cal, self.tab_ycal, self.tab_final = \
            (ttk.Frame(nb) for _ in range(5))
        for frame, title in [(self.tab_setup,'Setup'), (self.tab_raw,'Raw Plot'),
                             (self.tab_cal,'X‑Calibration'), (self.tab_ycal,'Y‑Calibration'),
                             (self.tab_final,'Calibrated Spectrum')]:
            nb.add(frame, text=title)
        nb.pack(fill='both', expand=True)
        self._setup_tab(); self._raw_tab(); self._cal_tab(); self._ycal_tab(); self._final_tab()

    def _footer(self):
        pil = Image.open(_LOGO_PATH)
        logo = ImageTk.PhotoImage(pil.resize((pil.width//12,pil.height//12), resample_filter))
        ttk.Label(self.tab_setup, image=logo).place(relx=1,rely=1,anchor='se',x=-5,y=-5)
        ttk.Label(self.tab_setup, text='© 2025 MassSpec Package').place(relx=0,rely=1,anchor='sw',x=5,y=-5)
        self._logo_img = logo  # keep reference

    # ───────────────────────────── setup tab ───────────────────────────────
    def _setup_tab(self):
        lf = ttk.Labelframe(self.tab_setup, text='Data Folders & Calibration', padding=10)
        lf.pack(fill='x', padx=10, pady=10)

        ttk.Label(lf, text='Measurement Folder:').grid(row=0,column=0,sticky='w')
        ttk.Button(lf, text='Browse', command=self._pick_meas).grid(row=0,column=1,padx=5)
        self.meas_lbl = ttk.Label(lf, text=os.path.basename(self.meas_dir or 'Not Selected'))
        self.meas_lbl.grid(row=1,column=0,columnspan=2,sticky='w')

        ttk.Label(lf, text='Background Folder:').grid(row=2,column=0,sticky='w',pady=(8,0))
        ttk.Button(lf, text='Browse', command=self._pick_back).grid(row=2,column=1,padx=5)
        self.back_lbl = ttk.Label(lf, text=os.path.basename(self.back_dir or 'Not Selected'))
        self.back_lbl.grid(row=3,column=0,columnspan=2,sticky='w')

        ttk.Label(lf, text='Y‑axis calibration:').grid(row=4,column=0,sticky='w',pady=(8,0))
        ttk.Combobox(lf,textvariable=self.ycal_method,
                     values=['None','Absolute pressure','Normalize to 100'],
                     state='readonly',width=20).grid(row=4,column=1,sticky='w')

        ttk.Button(lf, text='Process & Plot', command=self._process).grid(row=5,column=0,columnspan=2,pady=15)
        self.progress = ttk.Progressbar(lf, length=400, mode='determinate')
        self.progress.grid(row=6,column=0,columnspan=2,pady=5)

    # ───────────────────────────── raw tab ────────────────────────────────
    def _raw_tab(self):
        ctr = ttk.Frame(self.tab_raw); ctr.pack(fill='x', padx=10, pady=5)
        self.raw_btn = ttk.Button(ctr, text='Edit/Calibrate', state='disabled',
                                  command=self._show_cal)
        self.raw_btn.pack()
        self.raw_canvas = ttk.Frame(self.tab_raw); self.raw_canvas.pack(fill='both', expand=True)

    # ───────────────────────────── cal tab ────────────────────────────────
    def _cal_tab(self):
        self.cal_ctrl = ttk.Frame(self.tab_cal, padding=5); self.cal_ctrl.pack(fill='x')
        self.cal_canvas_frame = ttk.Frame(self.tab_cal); self.cal_canvas_frame.pack(fill='both', expand=True)

    # ───────────────────────────── y‑cal tab ───────────────────────────────
    def _ycal_tab(self):
        ctr = ttk.Frame(self.tab_ycal, padding=5); ctr.pack(fill='x')
        self.h_var     = tk.DoubleVar(value=50000)
        self.win1_var  = tk.DoubleVar()
        self.win2_var  = tk.DoubleVar()
        self.p0_var    = tk.DoubleVar(value=4.43e-7)

        ttk.Label(ctr,text='Detection level (h):').grid(row=0,column=0,sticky='e')
        ttk.Entry(ctr,textvariable=self.h_var,width=10).grid(row=0,column=1,padx=5)
        ttk.Label(ctr,text='Window start:').grid(row=1,column=0,sticky='e')
        ttk.Entry(ctr,textvariable=self.win1_var,width=10).grid(row=1,column=1,padx=5)
        ttk.Label(ctr,text='Window end:').grid(row=1,column=2,sticky='e')
        ttk.Entry(ctr,textvariable=self.win2_var,width=10).grid(row=1,column=3,padx=5)
        ttk.Label(ctr,text='Total pressure (mbar):').grid(row=2,column=0,sticky='e')
        ttk.Entry(ctr,textvariable=self.p0_var,width=10).grid(row=2,column=1,padx=5)

        self.ydetect_btn = ttk.Button(ctr, text='Detect Peaks', state='disabled',
                                      command=self._run_y_detect)
        self.ydetect_btn.grid(row=3,column=0,columnspan=2,pady=10)
        self.yapply_btn = ttk.Button(ctr, text='Apply Calibration', state='disabled',
                                     command=self._run_y_apply)
        self.yapply_btn.grid(row=3,column=2,columnspan=2,pady=10)
        self.ycal_canvas = ttk.Frame(self.tab_ycal); self.ycal_canvas.pack(fill='both', expand=True)

    # ───────────────────────────── final tab ──────────────────────────────
    def _final_tab(self):
        self.final_ctrl   = ttk.Frame(self.tab_final, padding=5); self.final_ctrl.pack(fill='x')
        self.final_canvas = ttk.Frame(self.tab_final); self.final_canvas.pack(fill='both', expand=True)

    # ─────────────────────────── dialogs & folders ─────────────────────────
    def _pick_meas(self):
        d = filedialog.askdirectory(title='Select Measurement Folder')
        if d: self.meas_dir = d; self.meas_lbl['text'] = os.path.basename(d)
    def _pick_back(self):
        d = filedialog.askdirectory(title='Select Background Folder')
        if d: self.back_dir = d; self.back_lbl['text'] = os.path.basename(d)

    def _scale_dlg(self):
        top = tk.Toplevel(self.root); top.title('UI Scale'); top.transient(self.root); top.grab_set()
        ttk.Label(top,text='UI Scale:').grid(row=0,column=0,padx=10,pady=10)
        sv = tk.DoubleVar(value=self.ui_scale)
        ttk.Scale(top,from_=0.5,to=2.0,variable=sv,orient='horizontal').grid(row=0,column=1,padx=10,pady=10)
        keep=tk.BooleanVar(); ttk.Checkbutton(top,text='Save as default',variable=keep).grid(row=1,column=0,columnspan=2)
        def ok():
            self.ui_scale=sv.get(); self.root.tk.call('tk','scaling',self.ui_scale)
            self.root.geometry(f"{int(self.base_w*self.ui_scale)}x{int(self.base_h*self.ui_scale)}")
            if keep.get():
                self.cfg.update({'ui_scale':self.ui_scale,
                                 'measurement_folder':self.meas_dir,
                                 'background_folder':self.back_dir})
                with open(_SETTINGS_PATH,'w') as f: json.dump(self.cfg,f)
            top.destroy()
        btn=ttk.Frame(top); btn.grid(row=2,column=0,columnspan=2,pady=10)
        ttk.Button(btn,text='OK',command=ok).grid(row=0,column=0,padx=5)
        ttk.Button(btn,text='Cancel',command=top.destroy).grid(row=0,column=1,padx=5)

    # ─────────────────────────── processing thread ─────────────────────────
    def _process(self):
        if not self.meas_dir or not self.back_dir:
            messagebox.showwarning('Folders not selected','Select both folders'); return
        n_meas=len([f for f in os.listdir(self.meas_dir) if f.endswith('.data32')])
        n_back=len([f for f in os.listdir(self.back_dir) if f.endswith('.data32')])
        self.total=n_meas+n_back; self.done=0; self.progress['value']=0
        self.raw_btn['state']='disabled'; self.stop_ev.clear()
        threading.Thread(target=self._worker,daemon=True).start()
    def _update(self,_): self.done+=1; self.progress['value']=(self.done/self.total)*100; self.root.update_idletasks()
    def _worker(self):
        mea=DataProcessor(self.meas_dir,self._update,self.stop_ev)
        bkg=DataProcessor(self.back_dir,self._update,self.stop_ev)
        self.vp=VoltagePlotter(mea,bkg); self.vp.calculate()
        self.root.after(0,lambda:self.raw_btn.config(state='normal'))
        self.root.after(0,lambda:self.nb.select(self.tab_raw))
        self.root.after(0,self._draw_raw)

    def _draw_raw(self):
        for w in self.raw_canvas.winfo_children(): w.destroy()
        fig,ax=plt.subplots(figsize=(8,4))
        ax.plot(self.vp.diff); ax.set_ylabel('Intensity'); ax.set_title('Raw Difference'); ax.grid()
        canvas=FigureCanvasTkAgg(fig,master=self.raw_canvas)
        tb=NavigationToolbar2Tk(canvas,self.raw_canvas,pack_toolbar=False); tb.update()
        tb.pack(side=tk.TOP,fill=tk.X)
        canvas.get_tk_widget().pack(fill='both',expand=True); canvas.draw()

    # ───────────────────────── X‑Calibration tab ───────────────────────────
    def _show_cal(self):
        # disconnect old mpl callbacks
        for cid in self._click_cids:
            try: self.cal_canvas.figure.canvas.mpl_disconnect(cid)
            except Exception: pass
        self._click_cids.clear()

        for w in self.cal_ctrl.winfo_children(): w.destroy()
        for w in self.cal_canvas_frame.winfo_children(): w.destroy()
        self.nb.select(self.tab_cal)

        T=np.arange(len(self.vp.diff)); n=len(T)-1
        self.cur_x1,self.cur_x2=n*0.25,n*0.75
        self.x1_var=tk.DoubleVar(value=self.cur_x1)
        self.x2_var=tk.DoubleVar(value=self.cur_x2)

        ttk.Label(self.cal_ctrl,text='T₁:').grid(row=0,column=0,sticky='e')
        ttk.Entry(self.cal_ctrl,textvariable=self.x1_var,width=8).grid(row=0,column=1,padx=5)
        ttk.Label(self.cal_ctrl,text='T₂:').grid(row=0,column=2,sticky='e')
        ttk.Entry(self.cal_ctrl,textvariable=self.x2_var,width=8).grid(row=0,column=3,padx=5)
        self.x1_var.trace_add('write',self._debounce); self.x2_var.trace_add('write',self._debounce)

        # click enable + radio
        self.click_enable=tk.BooleanVar(value=True)
        self.click_mode=tk.StringVar(value='T1')
        box=ttk.Frame(self.cal_ctrl); box.grid(row=1,column=0,columnspan=4,pady=(4,0))
        ttk.Checkbutton(box,text='Enable click selection',variable=self.click_enable).pack(side='left',padx=(0,6))
        for txt,val in [('T₁','T1'),('T₂','T2')]:
            ttk.Radiobutton(box,text=txt,variable=self.click_mode,value=val).pack(side='left',padx=3)

        # m1/m2 inputs
        self.m1_var,self.m2_var=tk.DoubleVar(),tk.DoubleVar()
        ttk.Label(self.cal_ctrl,text='m₁:').grid(row=2,column=0,sticky='e')
        ttk.Entry(self.cal_ctrl,textvariable=self.m1_var,width=8).grid(row=2,column=1,padx=5)
        ttk.Label(self.cal_ctrl,text='m₂:').grid(row=2,column=2,sticky='e')
        ttk.Entry(self.cal_ctrl,textvariable=self.m2_var,width=8).grid(row=2,column=3,padx=5)

        # figure
        fig,ax=plt.subplots(figsize=(8,4))
        ax.plot(T,self.vp.diff); ax.set_ylabel('Intensity'); ax.set_title('Drag lines, edit boxes, or click plot'); ax.grid()
        self.l1=ax.axvline(self.cur_x1,color='r',ls='--',label='T₁')
        self.l2=ax.axvline(self.cur_x2,color='g',ls='--',label='T₂'); ax.legend()
        self.cal_canvas=FigureCanvasTkAgg(fig,master=self.cal_canvas_frame)
        tb=NavigationToolbar2Tk(self.cal_canvas,self.cal_canvas_frame,pack_toolbar=False); tb.update()
        tb.pack(side=tk.TOP,fill=tk.X)
        self.cal_canvas.get_tk_widget().pack(fill='both',expand=True); self.cal_canvas.draw()
        cid=fig.canvas.mpl_connect('button_press_event',self._plot_click); self._click_cids.append(cid)

        ttk.Button(self.cal_ctrl,text='Confirm & Calibrate',command=self._confirm_cal).grid(row=3,column=0,columnspan=4,pady=8)
        DraggableLine(self.l1,self._drag1); DraggableLine(self.l2,self._drag2)

    # --- entry debounce
    def _debounce(self,*_):
        if self._debounce_id: self.root.after_cancel(self._debounce_id)
        self._debounce_id=self.root.after(500,self._apply_entry)
    def _apply_entry(self):
        self._debounce_id=None
        try: t1=float(self.x1_var.get()); t2=float(self.x2_var.get())
        except ValueError: return
        self.cur_x1,self.cur_x2=t1,t2
        self.l1.set_xdata([t1,t1]); self.l2.set_xdata([t2,t2]); self.cal_canvas.draw_idle()

    # --- click
    def _plot_click(self,event):
        if not self.click_enable.get() or event.inaxes is None: return
        x=float(event.xdata)
        if self.click_mode.get()=='T1':
            self.cur_x1=x; self.x1_var.set(x); self.l1.set_xdata([x,x])
        else:
            self.cur_x2=x; self.x2_var.set(x); self.l2.set_xdata([x,x])
        self.cal_canvas.draw_idle()

    # --- drags
    def _drag1(self,x): self.cur_x1=x; self.x1_var.set(x)
    def _drag2(self,x): self.cur_x2=x; self.x2_var.set(x)

    # --- confirm calibration
    def _confirm_cal(self):
        self._apply_entry()
        try: m1=float(self.m1_var.get()); m2=float(self.m2_var.get())
        except ValueError:
            messagebox.showerror('Invalid','m₁,m₂ must be numeric'); return
        if self.cur_x1==self.cur_x2 or m1<=0 or m2<=0:
            messagebox.showerror('Invalid','Ensure T₁≠T₂ and m₁,m₂>0'); return
        C=(self.cur_x1-self.cur_x2)/(np.sqrt(m1)-np.sqrt(m2))
        t0=self.cur_x1-C*np.sqrt(m1)
        T=np.arange(len(self.vp.diff)); self.mq=((T-t0)/C)**2; self.intens=self.vp.diff
        self.cal_m1,self.cal_m2=m1,m2
        self.win1_var.set(self.mq.min()); self.win2_var.set(self.mq.max())

        self._build_final_ctrl()   # final tab controls always prepared
        method=self.ycal_method.get()
        if method=='None':
            self.ydetect_btn['state']='disabled'; self.yapply_btn['state']='disabled'
            self.nb.select(self.tab_final); self._draw_final()
        else:
            self.ydetect_btn['state']='normal'; self.yapply_btn['state']='disabled'
            self.ycal_type=method
            self.nb.select(self.tab_ycal)

    # ─────────────────────────── final tab controls ────────────────────────
    def _build_final_ctrl(self):
        for w in self.final_ctrl.winfo_children(): w.destroy()
        ttk.Button(self.final_ctrl,text='Export Data',
                   command=lambda:self._export(self.mq,self.intens)).pack(side='left',padx=5)
        ttk.Label(self.final_ctrl,text='Plot Title:').pack(side='left',padx=5)
        ttk.Entry(self.final_ctrl,textvariable=self.title_var,width=30).pack(side='left',padx=5)
        ttk.Button(self.final_ctrl,text='Update Title',command=self._draw_final).pack(side='left',padx=5)
        self.show_leg  = tk.BooleanVar(value=True)
        self.show_lines= tk.BooleanVar(value=True)
        self.log_y     = tk.BooleanVar(value=False)
        self.use_ycal  = tk.BooleanVar(value=False)
        for txt,var in [('Legend',self.show_leg),('Lines',self.show_lines),
                        ('Log Y',self.log_y),('Use Y‑Cal',self.use_ycal)]:
            ttk.Checkbutton(self.final_ctrl,text=txt,variable=var,command=self._draw_final)\
                .pack(side='left',padx=5)

    def _draw_final(self):
        for w in self.final_canvas.winfo_children(): w.destroy()
        fig,ax=plt.subplots(figsize=(4,2),tight_layout=True)
        y=self.intens.copy(); ylabel='Intensity'
        if self.use_ycal.get():
            if self.ycal_type=='Absolute pressure':
                y=self.ycal_coeffs(y); ylabel='Pressure (mbar)'
            else:
                y*=self.ycal2_coeff; ylabel='Normalized Intensity'
        if self.log_y.get(): ax.set_yscale('log')
        ax.plot(self.mq,y,label='Spectrum')
        ax.set_xlabel('m/q'); ax.set_ylabel(ylabel); ax.set_title(self.title_var.get())
        if self.show_lines.get():
            ax.axvline(self.cal_m1,ls='--',label=f'm₁={self.cal_m1}')
            ax.axvline(self.cal_m2,ls='--',label=f'm₂={self.cal_m2}')
        if self.show_leg.get(): ax.legend()
        ax.grid(True)
        canvas=FigureCanvasTkAgg(fig,master=self.final_canvas)
        tb=NavigationToolbar2Tk(canvas,self.final_canvas,pack_toolbar=False); tb.update()
        tb.pack(side=tk.TOP,fill=tk.X)
        canvas.get_tk_widget().pack(fill='both',expand=True); canvas.draw()

    # ───────────────────── Y‑axis calibration helpers ──────────────────────
    def calculate_peak_areas(self,x,y,h):
        peaks,_=find_peaks(y,height=h)
        areas,crossings=[],[]
        for p in peaks:
            l,r=p,p
            while l>0 and y[l]>0: l-=1
            while r<len(y)-1 and y[r]>0: r+=1
            areas.append(np.sum(y[l:r+1])); crossings.append((x[l],x[r]))
        return np.array(areas),crossings,peaks
    _calc_peaks=calculate_peak_areas

    def _run_y_detect(self):
        # clear previous content
        for w in self.ycal_canvas.winfo_children(): w.destroy()

        x, y   = self.mq, self.intens
        h      = self.h_var.get()
        w1, w2 = self.win1_var.get(), self.win2_var.get()
        mask   = (x>=w1) & (x<=w2)
        xw, yw = x[mask], y[mask]

        if not xw.size:
            messagebox.showerror("Empty Window", f"No data in m/q window {w1}–{w2}.")
            return

        areas, _, peaks = self._calc_peaks(xw, yw, h)
        if not len(peaks):
            messagebox.showerror("No Peaks Found",
                                 "No peaks detected.\nLower h or widen window.")
            return

        # ----- build the figure depending on mode -----
        if self.ycal_type == 'Absolute pressure':
            p0 = self.p0_var.get()
            total = areas.sum()
            partial = p0 * areas / total
            heights = yw[peaks]

            coeffs = np.polyfit(heights, partial, 1)
            self.ycal_coeffs = np.poly1d(coeffs)

            fig,(ax_spec,ax_fit)=plt.subplots(2,1,constrained_layout=True)
            ax_spec.plot(xw,yw); ax_spec.scatter(xw[peaks],yw[peaks],c='r',s=20)
            ax_spec.set_xlabel('m/q'); ax_spec.set_ylabel('Intensity')
            ax_spec.set_title(f'Peaks @ h={h}'); ax_spec.grid(True)

            xs=np.linspace(heights.min(),heights.max(),200)
            ax_fit.scatter(heights,partial,c='r',label='Data')
            ax_fit.plot(xs,self.ycal_coeffs(xs),
                        label=f'y={coeffs[0]:.3e}x+{coeffs[1]:.3e}')
            ax_fit.set_xlabel('Peak height'); ax_fit.set_ylabel('Partial pressure (mbar)')
            ax_fit.set_title('Y‑calibration fit'); ax_fit.legend(); ax_fit.grid(True)
        else:
            self.ycal2_coeff=100.0 / yw[peaks].max()
            fig,ax_spec=plt.subplots(constrained_layout=True)
            ax_spec.plot(xw,yw); ax_spec.scatter(xw[peaks],yw[peaks],s=20)
            ax_spec.set_xlabel('m/q'); ax_spec.set_ylabel('Intensity')
            ax_spec.set_title(f'Peaks @ h={h}'); ax_spec.grid(True)

        # embed
        canvas=FigureCanvasTkAgg(fig,master=self.ycal_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both',expand=True)

        self.yapply_btn['state']='normal'

    def _run_y_apply(self):
        self.use_ycal.set(True); self.nb.select(self.tab_final); self._draw_final()

    # ─────────────────────────── export helper ─────────────────────────────
    def _export(self,mq,intens):
        if self.use_ycal.get():
            if self.ycal_type=='Absolute pressure':
                y=self.ycal_coeffs(intens); hdr='m/q\tpressure (mbar)'; fmt=('%.6f','%.9e')
            else:
                y=intens*self.ycal2_coeff; hdr='m/q\tnorm intensity'; fmt=('%.6f','%.6f')
        else:
            y=intens; hdr='m/q\tintensity'; fmt=('%.6f','%.6f')
        fp=filedialog.asksaveasfilename(defaultextension='.txt',
                                        filetypes=[('Text files','*.txt'),('All files','*.*')])
        if not fp: return
        np.savetxt(fp,np.vstack([mq,y]).T,delimiter='\t',header=hdr,comments='',fmt=fmt)
        messagebox.showinfo('Saved',fp)

    # ─────────────────────────── utils & close ─────────────────────────────
    def _close(self):
        self.stop_ev.set(); self.root.destroy()
    def on_closing(self): self._close()


# ───────────────────────── run the app ─────────────────────────
if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
