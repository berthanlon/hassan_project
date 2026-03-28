"""
map_canvas.py
Draws a 2D route map onto a tkinter Canvas widget.
Converts lat/lng to screen pixels using min-max normalisation.
"""

import tkinter as tk

COLOUR_BG         = "#0f0f18"
COLOUR_GRID       = "#1a1a2e"
COLOUR_ROUTE_DONE = "#e8ff47"
COLOUR_ROUTE_TODO = "#2a2a40"
COLOUR_DEPOT      = "#e8ff47"
COLOUR_STOP_DONE  = "#2ecc71"
COLOUR_STOP_NEXT  = "#e8ff47"
COLOUR_STOP_TODO  = "#3a3a5a"
COLOUR_STOP_MUTED = "#6b6b8a"


def _to_screen(lat, lng, min_lat, max_lat, min_lng, max_lng, width, height, pad):
    """Convert lat/lng to canvas (x, y) pixel coordinates."""
    usable_width = width  - 2 * pad
    usable_height = height - 2 * pad

    lat_range = max_lat - min_lat
    lng_range = max_lng - min_lng

    x = width  // 2 if lng_range < 1e-9 else pad + int((lng - min_lng) / lng_range * usable_width)
    y = height // 2 if lat_range < 1e-9 else height - pad - int((lat - min_lat) / lat_range * usable_height)

    return x, y


def draw_route(canvas, depot, route, done_indices, current_index=None):
    """
    Render the route on a tkinter Canvas.
    """
    canvas.delete("all")

    width = canvas.winfo_width()
    height = canvas.winfo_height()
    if width < 10:
        width = int(canvas["width"])
        height = int(canvas["height"])

    pad = 36

    all_locs = [depot] + route
    lats = [loc.lat for loc in all_locs]
    lngs = [loc.lng for loc in all_locs]
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)

    lat_margin = (max_lat - min_lat) * 0.12 or 0.01
    lng_margin = (max_lng - min_lng) * 0.12 or 0.01
    min_lat -= lat_margin
    max_lat += lat_margin
    min_lng -= lng_margin
    max_lng += lng_margin

    def coords(loc):
        return _to_screen(loc.lat, loc.lng,
                          min_lat, max_lat, min_lng, max_lng, width, height, pad)

    # Background
    canvas.create_rectangle(0, 0, width, height, fill=COLOUR_BG, outline="")

    # Grid lines
    for i in range(5):
        grid_y = pad + (height - 2 * pad) * i // 4
        grid_x = pad + (width - 2 * pad) * i // 4
        canvas.create_line(pad, grid_y, width - pad, grid_y, fill=COLOUR_GRID, width=1)
        canvas.create_line(grid_x, pad, grid_x, height - pad, fill=COLOUR_GRID, width=1)

    # Full route lines
    all_stops = [depot] + route + [depot]
    for i in range(len(all_stops) - 1):
        x1, y1 = coords(all_stops[i])
        x2, y2 = coords(all_stops[i + 1])
        canvas.create_line(x1, y1, x2, y2,
                           fill=COLOUR_ROUTE_TODO, width=2, dash=(6, 4))

    # Completed segments
    if done_indices:
        prev_loc = depot
        for idx in sorted(done_indices):
            x1, y1 = coords(prev_loc)
            x2, y2 = coords(route[idx])
            canvas.create_line(x1, y1, x2, y2,
                               fill=COLOUR_ROUTE_DONE, width=2)
            prev_loc = route[idx]

    # Stop nodes
    r_stop  = 10
    r_depot = 13

    for i, stop in enumerate(route):
        x, y    = coords(stop)
        is_done = i in done_indices
        is_next = (i == current_index)

        if is_done:
            fill     = COLOUR_STOP_DONE
            outline  = COLOUR_STOP_DONE
            text_col = "#000"
            label    = "v"
        elif is_next:
            fill     = COLOUR_STOP_NEXT
            outline  = COLOUR_STOP_NEXT
            text_col = "#000"
            label    = str(i + 1)
        else:
            fill     = COLOUR_STOP_TODO
            outline  = "#4a4a6a"
            text_col = COLOUR_STOP_MUTED
            label    = str(i + 1)

        # Outer ring for current stop
        if is_next:
            canvas.create_oval(x - r_stop - 6, y - r_stop - 6,
                               x + r_stop + 6, y + r_stop + 6,
                               fill="", outline=COLOUR_STOP_NEXT, width=2)

        canvas.create_oval(x - r_stop, y - r_stop,
                           x + r_stop, y + r_stop,
                           fill=fill, outline=outline, width=2)
        canvas.create_text(x, y, text=label,
                           fill=text_col, font=("Courier", 8, "bold"))

    # Depot node
    dx, dy = coords(depot)
    canvas.create_oval(dx - r_depot, dy - r_depot,
                       dx + r_depot, dy + r_depot,
                       fill=COLOUR_DEPOT, outline=COLOUR_DEPOT, width=2)
    canvas.create_text(dx, dy, text="D", fill="#000", font=("Courier", 9, "bold"))

    # Legend
    canvas.create_oval(8, height - 50, 18, height - 40, fill=COLOUR_DEPOT,     outline="")
    canvas.create_text(22, height - 45, text="Depot", anchor="w",
                       fill=COLOUR_STOP_MUTED, font=("Courier", 8))
    canvas.create_oval(8, height - 35, 18, height - 25, fill=COLOUR_STOP_DONE, outline="")
    canvas.create_text(22, height - 30, text="Done",  anchor="w",
                       fill=COLOUR_STOP_MUTED, font=("Courier", 8))
    canvas.create_oval(8, height - 20, 18, height - 10, fill=COLOUR_STOP_NEXT, outline="")
    canvas.create_text(22, height - 15, text="Next",  anchor="w",
                       fill=COLOUR_STOP_MUTED, font=("Courier", 8))