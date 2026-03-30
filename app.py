"""
Main application controller and GUI.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import datetime, timedelta

import geocoder
import algorithm
import map_canvas
import report as report_module


# Colours / fonts 

BG       = "#0a0a0f"
SURFACE  = "#12121a"
SURFACE2 = "#1a1a26"
BORDER   = "#2a2a40"
ACCENT   = "#e8ff47"
ACCENT2  = "#47ffe8"
RED      = "#ff4757"
TEXT     = "#e8e8f0"
MUTED    = "#6b6b8a"
GREEN    = "#2ecc71"

FONT_TITLE  = ("Helvetica", 22, "bold")
FONT_BODY   = ("Helvetica", 11)
FONT_SMALL  = ("Helvetica", 9)
FONT_MONO   = ("Courier", 10)
FONT_MONO_S = ("Courier", 9)


# Widget helpers

def style_entry(e):
    e.configure(bg=BG, fg=TEXT, insertbackground=TEXT,
                relief="flat", font=FONT_MONO,
                highlightthickness=1, highlightbackground=BORDER,
                highlightcolor=ACCENT)


def make_button(parent, text, cmd, accent=True, button_width=None):
    bg = ACCENT if accent else SURFACE2
    fg = "#000" if accent else TEXT
    button = tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg=fg, activebackground=bg,
                  font=("Helvetica", 10, "bold"),
                  relief="flat", bd=0, padx=14, pady=8,
                  cursor="hand2")
    if button_width:
        button.configure(width=button_width)
    return button


def make_label(parent, text, font=FONT_BODY, fg=TEXT, **kw):
    bg = kw.pop("bg", BG)
    return tk.Label(parent, text=text, font=font, bg=bg, fg=fg, **kw)


def make_card(parent):
    return tk.Frame(parent, bg=SURFACE,
                    highlightthickness=1, highlightbackground=BORDER)


#Main App 

class RouteMaxApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RouteMaster")
        self.root.geometry("960x700")
        self.root.configure(bg=BG)
        self.root.minsize(800, 600)

        # Shared state
        self.depot = None
        self.stops = []
        self.opt_result = None
        self.delivery_records = []
        self.start_time = None
        self.current_stop_idx = 0
        self.driver_name = ""

        self._build_header()

        self._container = tk.Frame(self.root, bg=BG)
        self._container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.frames = {}
        for FrameClass in (InputFrame, OptimiseFrame, DeliveryFrame, ReportFrame):
            name = FrameClass.__name__
            frame = FrameClass(self._container, self)
            self.frames[name] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_frame("InputFrame")

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=SURFACE,
                       highlightthickness=1, highlightbackground=BORDER)
        hdr.pack(fill="x")
        inner = tk.Frame(hdr, bg=SURFACE)
        inner.pack(fill="x", padx=20, pady=12)
        tk.Label(inner, text="Route", font=("Helvetica", 16, "bold"),
                 bg=SURFACE, fg=TEXT).pack(side="left")
        tk.Label(inner, text="Max", font=("Helvetica", 16, "bold"),
                 bg=SURFACE, fg=ACCENT).pack(side="left")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

    def run(self):
        self.root.mainloop()


# Frame 1: Input

class InputFrame(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        # Title
        title_row = tk.Frame(self, bg=BG)
        title_row.pack(fill="x", pady=(20, 16))
        make_label(title_row, "Plan Your Route", FONT_TITLE, ACCENT).pack(side="left")

        # Two columns
        cols = tk.Frame(self, bg=BG)
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        left  = tk.Frame(cols, bg=BG)
        right = tk.Frame(cols, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Depot card
        depot_card = make_card(left)
        depot_card.pack(fill="x", pady=(0, 10))

        tk.Label(depot_card, text="DEPOT (START POINT)", font=("Courier", 8),
                 bg=SURFACE, fg=ACCENT).pack(anchor="w", padx=14, pady=(12, 4))

        depot_row = tk.Frame(depot_card, bg=SURFACE)
        depot_row.pack(fill="x", padx=14, pady=(0, 6))

        self.depot_var = tk.StringVar()
        self.depot_entry = tk.Entry(depot_row, textvariable=self.depot_var, width=14)
        style_entry(self.depot_entry)
        self.depot_entry.pack(side="left", ipady=6)
        self.depot_entry.bind("<Return>", lambda e: self._set_depot())

        make_button(depot_row, "Set", self._set_depot).pack(side="left", padx=(8, 0))

        self.depot_status = make_label(
            depot_card, "No depot set", FONT_MONO_S, MUTED, bg=SURFACE)
        self.depot_status.pack(anchor="w", padx=14, pady=(0, 10))

        #  Stops card 
        stop_card = make_card(left)
        stop_card.pack(fill="both", expand=True, pady=(0, 10))

        tk.Label(stop_card, text="DELIVERY STOPS", font=("Courier", 8),
                 bg=SURFACE, fg=ACCENT).pack(anchor="w", padx=14, pady=(12, 4))

        stop_row = tk.Frame(stop_card, bg=SURFACE)
        stop_row.pack(fill="x", padx=14)

        self.stop_var = tk.StringVar()
        self.stop_entry = tk.Entry(stop_row, textvariable=self.stop_var, width=14)
        style_entry(self.stop_entry)
        self.stop_entry.pack(side="left", ipady=6)
        self.stop_entry.bind("<Return>", lambda e: self._add_stop())

        make_button(stop_row, "Add", self._add_stop).pack(side="left", padx=(8, 0))

        self.stop_error = make_label(stop_card, "", FONT_MONO_S, RED, bg=SURFACE)
        self.stop_error.pack(anchor="w", padx=14, pady=(4, 0))

        list_frame = tk.Frame(stop_card, bg=SURFACE)
        list_frame.pack(fill="both", expand=True, padx=14, pady=8)

        sb = tk.Scrollbar(list_frame, bg=SURFACE, troughcolor=BG)
        sb.pack(side="right", fill="y")

        self.stop_listbox = tk.Listbox(
            list_frame, bg=SURFACE2, fg=TEXT,
            selectbackground=ACCENT, selectforeground="#000",
            font=FONT_MONO, relief="flat", bd=0,
            highlightthickness=0, activestyle="none",
            yscrollcommand=sb.set
        )
        self.stop_listbox.pack(side="left", fill="both", expand=True)
        sb.configure(command=self.stop_listbox.yview)

        make_button(stop_card, "Remove Selected", self._remove_stop,
                 accent=False).pack(anchor="w", padx=14, pady=(0, 12))

        # ── Time card ─────────────────────────────────────────────────────────
        time_card = make_card(left)
        time_card.pack(fill="x")

        tk.Label(time_card, text="START TIME", font=("Courier", 8),
                 bg=SURFACE, fg=ACCENT).pack(anchor="w", padx=14, pady=(10, 4))

        self.time_var = tk.StringVar(value="09:00")
        time_entry = tk.Entry(time_card, textvariable=self.time_var, width=8)
        style_entry(time_entry)
        time_entry.pack(anchor="w", padx=14, pady=(0, 4), ipady=6)
        make_label(time_card, "Format: HH:MM  e.g. 09:00",
                   FONT_SMALL, MUTED, bg=SURFACE).pack(anchor="w", padx=14, pady=(0, 10))

        # Driver name card
        name_card = make_card(left)
        name_card.pack(fill="x", pady=(10, 0))
        tk.Label(name_card, text="DRIVER NAME", font=("Courier", 8),
                 bg=SURFACE, fg=ACCENT).pack(anchor="w", padx=14, pady=(10, 4))
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(name_card, textvariable=self.name_var, width=24)
        style_entry(name_entry)
        name_entry.pack(anchor="w", padx=14, pady=(0, 4), ipady=6)
        make_label(name_card, "Printed on the report",
                   FONT_SMALL, MUTED, bg=SURFACE).pack(anchor="w", padx=14, pady=(0, 10))

        # ── Optimise button ───────────────────────────────────────────────────
        self.go_btn = tk.Button(
            self, text="Optimise Route  [set depot + add 2 stops]",
            command=self._start_optimise,
            bg=SURFACE2, fg=MUTED,
            activebackground=ACCENT, activeforeground="#000",
            font=("Helvetica", 11, "bold"),
            relief="flat", bd=0, padx=14, pady=12,
            cursor="hand2", state="disabled"
        )
        self.go_btn.pack(fill="x", pady=(12, 0))

    # ── Depot actions ─────────────────────────────────────────────────────────

    def _set_depot(self):
        pc = self.depot_var.get().strip()
        if not pc:
            self.depot_status.configure(text="Please enter a postcode", fg=RED)
            return
        self.depot_status.configure(text="Looking up...", fg=MUTED)
        self.depot_entry.configure(state="disabled")

        def lookup():
            result = geocoder.geocode(pc)
            self.after(0, lambda: self._on_depot_result(result))

        threading.Thread(target=lookup, daemon=True).start()

    def _on_depot_result(self, result):
        self.depot_entry.configure(state="normal")
        if not result:
            self.depot_status.configure(
                text="Postcode not found - check spelling", fg=RED)
            return
        self.app.depot = algorithm.Location(
            postcode=result["postcode"],
            lat=result["lat"],
            lng=result["lng"],
            district=result["district"],
            ward=result["ward"]
        )
        self.depot_var.set("")
        txt = "OK  " + result["postcode"] + "  -  " + result["district"]
        self.depot_status.configure(text=txt, fg=ACCENT)
        self._update_go_btn()

    # ── Stop actions ──────────────────────────────────────────────────────────

    def _add_stop(self):
        pc = self.stop_var.get().strip()
        self.stop_error.configure(text="")
        if not pc:
            self.stop_error.configure(text="Please enter a postcode")
            return

        clean = pc.replace(" ", "").upper()
        existing = [s.postcode.replace(" ", "").upper() for s in self.app.stops]
        depot_pc = ""
        if self.app.depot:
            depot_pc = self.app.depot.postcode.replace(" ", "").upper()

        if clean in existing or clean == depot_pc:
            self.stop_error.configure(text="Postcode already added")
            return

        self.stop_error.configure(text="Looking up...")
        self.stop_entry.configure(state="disabled")

        def lookup():
            result = geocoder.geocode(pc)
            self.after(0, lambda: self._on_stop_result(result))

        threading.Thread(target=lookup, daemon=True).start()

    def _on_stop_result(self, result):
        self.stop_entry.configure(state="normal")
        if not result:
            self.stop_error.configure(
                text="Postcode not found - check spelling")
            return
        loc = algorithm.Location(
            postcode=result["postcode"],
            lat=result["lat"],
            lng=result["lng"],
            district=result["district"],
            ward=result["ward"]
        )
        self.app.stops.append(loc)
        self.stop_var.set("")
        self.stop_error.configure(text="")
        self._refresh_listbox()
        self._update_go_btn()

    def _remove_stop(self):
        sel = self.stop_listbox.curselection()
        if not sel:
            return
        self.app.stops.pop(sel[0])
        self._refresh_listbox()
        self._update_go_btn()

    def _refresh_listbox(self):
        self.stop_listbox.delete(0, "end")
        for i, s in enumerate(self.app.stops):
            area = s.district[:18] if s.district else ""
            entry = ("  " + str(i + 1).rjust(2) + ".  "
                     + s.postcode.ljust(10) + "  " + area)
            self.stop_listbox.insert("end", entry)

    def _update_go_btn(self):
        ready = (self.app.depot is not None) and (len(self.app.stops) >= 2)
        if ready:
            self.go_btn.configure(
                state="normal", bg=ACCENT, fg="#000",
                text="Optimise Route  ->")
        else:
            needed = []
            if self.app.depot is None:
                needed.append("set depot")
            rem = 2 - len(self.app.stops)
            if rem > 0:
                needed.append("add " + str(rem) + " more stop(s)")
            self.go_btn.configure(
                state="disabled", bg=SURFACE2, fg=MUTED,
                text="Optimise Route  [" + ", ".join(needed) + "]")

    # ── Sample data ───────────────────────────────────────────────────────────

    def _load_samples(self):
        self.app.depot = None
        self.app.stops = []
        self.depot_status.configure(text="Loading samples...", fg=MUTED)
        self._refresh_listbox()
        self._update_go_btn()

        def load():
            depot_data = geocoder.geocode("SW1A 1AA")
            stops_data = geocoder.bulk_geocode(
                ["EC1A 1BB", "W1A 1AA", "SE1 7PB", "N1 9GU", "E1 6RF", "WC2N 5DU"])
            self.after(0, lambda: self._on_samples_loaded(depot_data, stops_data))

        threading.Thread(target=load, daemon=True).start()

    def _on_samples_loaded(self, depot_data, stops_data):
        if depot_data:
            self.app.depot = algorithm.Location(**depot_data)
            txt = "OK  " + depot_data["postcode"] + "  -  " + depot_data["district"]
            self.depot_status.configure(text=txt, fg=ACCENT)
        for r in stops_data:
            if r:
                self.app.stops.append(algorithm.Location(**r))
        self._refresh_listbox()
        self._update_go_btn()

    # ── Start optimise ────────────────────────────────────────────────────────

    def _start_optimise(self):
        try:
            parts = self.time_var.get().strip().split(":")
            h = int(parts[0])
            m = int(parts[1])
            self.app.start_time = datetime.now().replace(
                hour=h, minute=m, second=0, microsecond=0)
        except Exception:
            self.app.start_time = datetime.now().replace(
                hour=9, minute=0, second=0, microsecond=0)

        self.app.driver_name = self.name_var.get().strip()
        self.app.delivery_records = []
        self.app.current_stop_idx = 0
        self.app.show_frame("OptimiseFrame")


# ── Frame 2: Optimising ───────────────────────────────────────────────────────

class OptimiseFrame(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        wrapper = tk.Frame(self, bg=BG)
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        make_label(wrapper, "Optimising Route", FONT_TITLE, ACCENT).pack(pady=(0, 4))
        make_label(wrapper, "Running nearest-neighbour + 2-opt swap...",
                   FONT_BODY, MUTED).pack()

        self.progress = ttk.Progressbar(wrapper, length=420, mode="indeterminate")
        self.progress.pack(pady=28)

        self.log_var = tk.StringVar(value="Starting...")
        make_label(wrapper, "", FONT_MONO_S, MUTED, textvariable=self.log_var).pack()

    def on_show(self):
        self.progress.start(12)
        self.log_var.set("Building distance matrix...")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        def cb(msg):
            self.after(0, lambda m=msg: self.log_var.set(m))

        result = algorithm.optimise_route(
            self.app.depot, self.app.stops, progress_callback=cb)
        self.app.opt_result = result
        self.after(600, self._done)

    def _done(self):
        self.progress.stop()
        self.app.show_frame("DeliveryFrame")

# ── Frame 3: Delivery ─────────────────────────────────────────────────────────

class DeliveryFrame(tk.Frame):
    """
    Delivery tracking screen. Rebuilt each time on_show() is called
    so it always reflects the current route data cleanly.
    """

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        # Wipe and rebuild completely each time so layout is always fresh
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        result = self.app.opt_result
        stops  = result.route
        done   = set(r.stop_index for r in self.app.delivery_records)
        current    = self.app.current_stop_idx
        total  = len(stops)
        n_done = len(done)

        # ── Title row ─────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", pady=(12, 4))
        make_label(hdr, "On the Road", FONT_TITLE, ACCENT).pack(side="left")

        # ── Progress bar ──────────────────────────────────────────────────────
        prog_frame = tk.Frame(self, bg=BG)
        prog_frame.pack(fill="x", pady=(0, 6))

        pct = int(n_done / total * 100) if total > 0 else 0
        make_label(prog_frame,
                   str(n_done) + " of " + str(total) + " stops delivered  (" + str(pct) + "%)",
                   FONT_MONO_S, MUTED).pack(anchor="w")

        bar_bg = tk.Frame(prog_frame, bg=BORDER, height=8)
        bar_bg.pack(fill="x", pady=(4, 0))
        bar_bg.update_idletasks()
        fill_w = max(1, int(bar_bg.winfo_reqwidth() * pct / 100))
        tk.Frame(bar_bg, bg=ACCENT, height=8, width=fill_w).place(x=0, y=0, relheight=1,
                                                                    relwidth=pct/100)

        # ── Stats row ─────────────────────────────────────────────────────────
        stats_row = tk.Frame(self, bg=BG)
        stats_row.pack(fill="x", pady=(0, 8))

        elapsed_min = 0
        km_done = 0.0
        if self.app.delivery_records:
            delta = self.app.delivery_records[-1].arrived_at - self.app.start_time
            elapsed_min = int(delta.total_seconds() / 60)
            km_done = sum(r.distance_from_prev_km for r in self.app.delivery_records)

        chips = [
            (str(n_done) + " / " + str(total),               "STOPS DONE"),
            (str(elapsed_min) + " min",                       "TIME ELAPSED"),
            (str(round(km_done, 1)) + " km",                  "DIST COVERED"),
            (str(round(result.total_distance_km, 1)) + " km", "TOTAL ROUTE"),
        ]
        for val, lbl in chips:
            chip = make_card(stats_row)
            chip.pack(side="left", padx=(0, 8))
            tk.Label(chip, text=val, font=("Helvetica", 12, "bold"),
                     bg=SURFACE, fg=ACCENT2).pack(padx=10, pady=(6, 1))
            tk.Label(chip, text=lbl, font=("Courier", 7),
                     bg=SURFACE, fg=MUTED).pack(padx=10, pady=(0, 6))

        # ── Main area: map left, stop list right ──────────────────────────────
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        # Map
        map_card = make_card(main)
        map_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        make_label(map_card, "ROUTE MAP", font=("Courier", 8),
                   fg=ACCENT, bg=SURFACE).pack(anchor="w", padx=8, pady=(6, 2))
        map_c = tk.Canvas(map_card, bg=map_canvas.COLOUR_BG,
                          highlightthickness=0, width=300, height=300)
        map_c.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        # Draw after layout settles
        map_c.update_idletasks()
        map_canvas.draw_route(map_c, self.app.depot, stops, done,
                               current if current < total else None)

        # Stop list (right column)
        right = tk.Frame(main, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        make_label(right, "DELIVERY STOPS", font=("Courier", 8),
                   fg=ACCENT).grid(row=0, column=0, sticky="w", pady=(0, 4))

        # Scrollable stop cards
        outer = tk.Frame(right, bg=BG)
        outer.grid(row=1, column=0, sticky="nsew")
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        scroll_bar = tk.Scrollbar(outer, bg=SURFACE, troughcolor=BG)
        scroll_bar.grid(row=0, column=1, sticky="ns")

        sc = tk.Canvas(outer, bg=BG, highlightthickness=0,
                       yscrollcommand=scroll_bar.set)
        sc.grid(row=0, column=0, sticky="nsew")
        scroll_bar.configure(command=sc.yview)

        inner = tk.Frame(sc, bg=BG)
        window_id = sc.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_resize(e):
            sc.configure(scrollregion=sc.bbox("all"))
        def _on_canvas_resize(e):
            sc.itemconfig(window_id, width=e.width)

        inner.bind("<Configure>", _on_inner_resize)
        sc.bind("<Configure>", _on_canvas_resize)

        # Build one card per stop
        for i, stop in enumerate(stops):
            is_done = i in done
            is_currrent  = (i == current) and not is_done
            is_future = not is_done and not is_currrent

            if is_currrent:
                border_col = ACCENT
                card_bg    = "#1a1a10"
            elif is_done:
                border_col = GREEN
                card_bg    = SURFACE2
            else:
                border_col = BORDER
                card_bg    = SURFACE

            card = tk.Frame(inner, bg=card_bg,
                            highlightthickness=2,
                            highlightbackground=border_col)
            card.pack(fill="x", padx=4, pady=3)

            # Left badge
            if is_done:
                badge_bg = GREEN;  badge_fg = "#000"; badge_txt = "DONE"
            elif is_currrent:
                badge_bg = ACCENT; badge_fg = "#000"; badge_txt = str(i + 1)
            else:
                badge_bg = SURFACE2; badge_fg = MUTED; badge_txt = str(i + 1)

            tk.Label(card, text=badge_txt,
                     font=("Helvetica", 10, "bold"),
                     bg=badge_bg, fg=badge_fg,
                     width=5, pady=10).pack(side="left")

            # Centre info
            info = tk.Frame(card, bg=card_bg)
            info.pack(side="left", fill="both", expand=True, padx=8, pady=6)

            postcode_colour = MUTED if is_done else (ACCENT if is_currrent else TEXT)
            tk.Label(info, text=stop.postcode,
                     font=("Courier", 12, "bold"),
                     bg=card_bg, fg=postcode_colour,
                     anchor="w").pack(fill="x")

            area = stop.district
            if stop.ward:
                area = area + " - " + stop.ward
            tk.Label(info, text=area or "-",
                     font=("Courier", 8),
                     bg=card_bg, fg=MUTED,
                     anchor="w").pack(fill="x")

            # Status line
            if is_done:
                record = next(r for r in self.app.delivery_records if r.stop_index == i)
                status = ("Delivered at " + record.arrived_at.strftime("%H:%M")
                          + "   |   " + str(round(record.distance_from_prev_km, 2)) + " km"
                          + "   |   " + str(round(record.travel_minutes, 1)) + " min travel")
                tk.Label(info, text=status,
                         font=("Courier", 8), bg=card_bg, fg=GREEN,
                         anchor="w").pack(fill="x")
            elif is_currrent:
                prev_loc = self.app.depot if i == 0 else stops[i - 1]
                dist = round(algorithm.haversine(prev_loc, stop), 2)
                tk.Label(info,
                         text=">> DELIVER NOW  -  ~" + str(dist) + " km from previous stop",
                         font=("Courier", 8, "bold"),
                         bg=card_bg, fg=ACCENT,
                         anchor="w").pack(fill="x")
            else:
                prev_loc = self.app.depot if i == 0 else stops[i - 1]
                dist = round(algorithm.haversine(prev_loc, stop), 2)
                tk.Label(info,
                         text="Upcoming  -  ~" + str(dist) + " km from previous",
                         font=("Courier", 8),
                         bg=card_bg, fg=MUTED,
                         anchor="w").pack(fill="x")

            # Right: deliver button or done label
            right_side = tk.Frame(card, bg=card_bg)
            right_side.pack(side="right", padx=10, pady=6)

            if is_done:
                tk.Label(right_side, text="DELIVERED",
                         font=("Courier", 8, "bold"),
                         bg=card_bg, fg=GREEN).pack()
            elif is_currrent:
                # Big prominent deliver button
                tk.Button(right_side,
                          text="MARK\nDELIVERED",
                          command=lambda idx=i: self._tick(idx),
                          bg=ACCENT, fg="#000",
                          font=("Helvetica", 10, "bold"),
                          relief="flat", bd=0,
                          padx=16, pady=10,
                          cursor="hand2",
                          activebackground="#c8df20",
                          activeforeground="#000").pack()
            else:
                # Greyed out button for future stops
                tk.Button(right_side,
                          text="Deliver",
                          command=lambda idx=i: self._tick(idx),
                          bg=SURFACE2, fg=MUTED,
                          font=("Helvetica", 9),
                          relief="flat", bd=0,
                          padx=10, pady=6,
                          cursor="hand2",
                          activebackground=ACCENT,
                          activeforeground="#000").pack()

        # Scroll to current stop after a moment
        if current > 0 and current < total:
            self.after(150, lambda: self._scroll_to_stop(sc, inner, current))

    def _scroll_to_stop(self, sc, inner, idx):
        cards = inner.winfo_children()
        if idx < len(cards):
            inner.update_idletasks()
            inner_h = inner.winfo_height()
            if inner_h > 0:
                frac = cards[idx].winfo_y() / inner_h
                sc.yview_moveto(max(0.0, frac - 0.05))

    def _tick(self, idx):
        stops = self.app.opt_result.route

        if not self.app.delivery_records:
            prev_loc  = self.app.depot
            prev_time = self.app.start_time
        else:
            last      = self.app.delivery_records[-1]
            prev_loc  = stops[last.stop_index]
            prev_time = last.arrived_at

        dist_km     = algorithm.haversine(prev_loc, stops[idx])
        travel_secs = (dist_km / 40.0) * 3600
        arrived_at  = prev_time + timedelta(seconds=travel_secs)
        travel_mins = travel_secs / 60.0

        rec = report_module.StopRecord(
            stop_index=idx,
            location=stops[idx],
            arrived_at=arrived_at,
            distance_from_prev_km=dist_km,
            travel_minutes=travel_mins,
        )
        self.app.delivery_records.append(rec)
        self.app.current_stop_idx = idx + 1

        if len(self.app.delivery_records) == len(stops):
            # All done — go to report
            self.after(200, lambda: self.app.show_frame("ReportFrame"))
        else:
            # Rebuild the screen with updated state
            self.on_show()



# Frame 4: Report
class ReportFrame(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._report = None

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        records = self.app.delivery_records
        result  = self.app.opt_result
        stops   = result.route

        report = report_module.DeliveryReport(
            depot=self.app.depot,
            route=stops,
            records=records,
            start_time=self.app.start_time,
            opt_result=result,
            driver_name=self.app.driver_name,
        )
        self._report = report

        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", pady=(16, 8))
        title_col = tk.Frame(header, bg=BG)
        title_col.pack(side="left")
        make_label(title_col, "Delivery Report", FONT_TITLE, ACCENT).pack(anchor="w")
        driver_txt = report.driver_name if report.driver_name else "Driver not specified"
        make_label(title_col, "Driver: " + driver_txt, FONT_MONO_S, MUTED).pack(anchor="w")

        btn_row = tk.Frame(header, bg=BG)
        btn_row.pack(side="right")
        make_button(btn_row, "Save Report", self._save_report).pack(side="left", padx=(0, 8))
        make_button(btn_row, "Save CSV", self._save_csv, accent=False).pack(side="left", padx=(0, 8))
        make_button(btn_row, "New Route", self._new_route, accent=False).pack(side="left")

        stats_f = tk.Frame(self, bg=BG)
        stats_f.pack(fill="x", pady=(0, 10))

        saved = result.initial_distance_km - result.total_distance_km
        percentage   = saved / result.initial_distance_km * 100 \
                if result.initial_distance_km > 0 else 0

        stat_data = [
            (str(round(report.total_minutes)),                   "TOTAL MINUTES"),
            (str(round(report.total_km, 1)) + " km",            "KM TRAVELLED"),
            (str(len(records)),                                "STOPS DONE"),
            (str(round(report.avg_minutes_per_stop, 1)),         "AVG MIN/STOP"),
            (str(round(report.fastest_stop.travel_minutes, 1)), "FASTEST (MIN)"),
            (str(round(report.slowest_stop.travel_minutes, 1)), "SLOWEST (MIN)"),
        ]
        for val, label in stat_data:
            c = make_card(stats_f)
            c.pack(side="left", padx=(0, 6), fill="y")
            tk.Label(c, text=val, font=("Helvetica", 16, "bold"),
                     bg=SURFACE, fg=ACCENT).pack(padx=12, pady=(10, 2))
            tk.Label(c, text=label, font=("Courier", 7),
                     bg=SURFACE, fg=MUTED).pack(padx=12, pady=(0, 10))

        paned = tk.PanedWindow(self, orient="horizontal", bg=BG,
                                sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True)

        map_frame = make_card(paned)
        paned.add(map_frame, minsize=280)
        make_label(map_frame, "OPTIMISED ROUTE", font=("Courier", 8),
                   fg=ACCENT, bg=SURFACE).pack(anchor="w", padx=10, pady=(8, 4))
        self.report_map = tk.Canvas(
            map_frame, bg=map_canvas.COLOUR_BG,
            highlightthickness=0, width=300, height=300)
        self.report_map.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.after(120, self._draw_report_map)

        right = tk.Frame(paned, bg=BG)
        paned.add(right, minsize=280)

        algo_card = make_card(right)
        algo_card.pack(fill="x", pady=(0, 8))

        make_label(right, "STOP-BY-STOP", font=("Courier", 8), fg=ACCENT).pack(anchor="w")

        table_frame = tk.Frame(right, bg=BG)
        table_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(table_frame, bg=SURFACE, troughcolor=BG)
        scrollbar.pack(side="right", fill="y")

        cols = ("#", "Postcode", "Area", "Dist km", "Mins", "Arrived")
        table = ttk.Treeview(table_frame, columns=cols, show="headings",
                            yscrollcommand=scrollbar.set, height=10)
        scrollbar.configure(command=table.yview)

        widths = [30, 90, 140, 65, 55, 60]
        for col, w in zip(cols, widths):
            table.heading(col, text=col)
            table.column(col, width=w, anchor="w")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background=SURFACE, foreground=TEXT,
                        fieldbackground=SURFACE, rowheight=22, font=FONT_MONO_S)
        style.configure("Treeview.Heading",
                        background=SURFACE2, foreground=ACCENT,
                        font=("Courier", 8, "bold"))
        style.map("Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "#000")])

        fast_idx = report.fastest_stop.stop_index
        slow_idx = report.slowest_stop.stop_index

        for rec in records:
            tag = ""
            if rec.stop_index == fast_idx:
                tag = "fast"
            elif rec.stop_index == slow_idx:
                tag = "slow"
            table.insert("", "end", values=(
                rec.stop_index + 1,
                rec.location.postcode,
                (rec.location.district or "-")[:18],
                str(round(rec.distance_from_prev_km, 2)),
                str(round(rec.travel_minutes, 1)),
                rec.arrived_at.strftime("%H:%M"),
            ), tags=(tag,))

        table.tag_configure("fast", foreground=GREEN)
        table.tag_configure("slow", foreground=RED)
        table.pack(side="left", fill="both", expand=True)

    def _draw_report_map(self):
        done = set(r.stop_index for r in self.app.delivery_records)
        map_canvas.draw_route(
            self.report_map, self.app.depot,
            self.app.opt_result.route, done, current_index=None)

    def _save_report(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Delivery Report",
            initialfile="delivery_report_" + datetime.now().strftime("%Y%m%d_%H%M") + ".txt"
        )
        if filepath:
            saved_path = report_module.save_report(self._report, filepath)
            messagebox.showinfo("Report Saved", "Report saved to:\n" + saved_path)

    def _save_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save CSV Report",
            initialfile="delivery_report_" + datetime.now().strftime("%Y%m%d_%H%M") + ".csv"
        )
        if filepath:
            saved_path = report_module.save_csv(self._report, filepath)
            messagebox.showinfo("CSV Saved", "CSV saved to:\n" + saved_path)

    def _new_route(self):
        self.app.depot = None
        self.app.stops = []
        self.app.opt_result = None
        self.app.delivery_records = []
        self.app.current_stop_idx = 0

        self.app.driver_name = ""
        inp = self.app.frames["InputFrame"]
        inp.depot_status.configure(text="No depot set", fg=MUTED)
        inp.stop_listbox.delete(0, "end")
        inp.name_var.set("")
        inp._update_go_btn()

        self.app.show_frame("InputFrame")