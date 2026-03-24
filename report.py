# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 00:16:07 2026

@author: betti
"""
"""
report.py
---------
Generates a plain-text delivery report and saves it to a .txt file.
Also provides data structures for the report summary shown in the GUI.
"""

import os
from datetime import datetime, timedelta
from dataclasses import dataclass

from algorithm import Location, OptimisationResult


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class StopRecord:
    """Records the outcome of a single delivery stop."""
    stop_index: int          # 0-based index in the optimised route
    location: Location
    arrived_at: datetime
    distance_from_prev_km: float
    travel_minutes: float


@dataclass
class DeliveryReport:
    depot: Location
    route: list[Location]
    records: list[StopRecord]
    start_time: datetime
    opt_result: OptimisationResult

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def total_minutes(self) -> float:
        if not self.records:
            return 0.0
        return (self.records[-1].arrived_at - self.start_time).total_seconds() / 60

    @property
    def total_km(self) -> float:
        return sum(r.distance_from_prev_km for r in self.records)

    @property
    def avg_minutes_per_stop(self) -> float:
        if not self.records:
            return 0.0
        return self.total_minutes / len(self.records)

    @property
    def fastest_stop(self) -> StopRecord:
        return min(self.records, key=lambda r: r.travel_minutes)

    @property
    def slowest_stop(self) -> StopRecord:
        return max(self.records, key=lambda r: r.travel_minutes)


# ── Report generation ─────────────────────────────────────────────────────────

def generate_text_report(report: DeliveryReport) -> str:
    """
    Produce a formatted plain-text report string.
    """
    sep = "=" * 60
    thin = "-" * 60
    lines = []

    lines.append(sep)
    lines.append("  ROUTEMAX — DELIVERY REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append(sep)
    lines.append("")

    # Summary
    lines.append("SUMMARY")
    lines.append(thin)
    lines.append(f"  Depot:              {report.depot.postcode} ({report.depot.district})")
    lines.append(f"  Start time:         {report.start_time.strftime('%H:%M')}")
    lines.append(f"  Stops completed:    {len(report.records)}")
    lines.append(f"  Total distance:     {report.total_km:.2f} km")
    lines.append(f"  Total time:         {report.total_minutes:.0f} minutes")
    lines.append(f"  Avg time per stop:  {report.avg_minutes_per_stop:.1f} minutes")
    lines.append("")

    # Algorithm stats
    lines.append("ALGORITHM PERFORMANCE (2-OPT)")
    lines.append(thin)
    lines.append(f"  Initial route (nearest-neighbour): "
                 f"{report.opt_result.initial_distance_km:.2f} km")
    lines.append(f"  Optimised route (2-opt):           "
                 f"{report.opt_result.total_distance_km:.2f} km")
    saved = report.opt_result.initial_distance_km - report.opt_result.total_distance_km
    pct = saved / report.opt_result.initial_distance_km * 100 if report.opt_result.initial_distance_km > 0 else 0
    lines.append(f"  Distance saved:                    {saved:.2f} km ({pct:.1f}%)")
    lines.append(f"  2-opt iterations:                  {report.opt_result.iterations}")
    lines.append("")

    # Highlights
    lines.append("HIGHLIGHTS")
    lines.append(thin)
    f = report.fastest_stop
    s = report.slowest_stop
    lines.append(f"  Fastest stop:  Stop {f.stop_index + 1} — {f.location.postcode} "
                 f"({f.travel_minutes:.1f} min, {f.distance_from_prev_km:.2f} km)")
    lines.append(f"  Slowest stop:  Stop {s.stop_index + 1} — {s.location.postcode} "
                 f"({s.travel_minutes:.1f} min, {s.distance_from_prev_km:.2f} km)")
    lines.append("")

    # Stop-by-stop table
    lines.append("STOP-BY-STOP BREAKDOWN")
    lines.append(thin)
    header = f"  {'#':<4} {'Postcode':<12} {'Area':<22} {'Dist (km)':<12} {'Travel (min)':<14} {'Arrived'}"
    lines.append(header)
    lines.append(f"  {'-'*4} {'-'*12} {'-'*22} {'-'*12} {'-'*14} {'-'*8}")

    for rec in report.records:
        area = rec.location.district[:20] if rec.location.district else "—"
        row = (f"  {rec.stop_index + 1:<4} "
               f"{rec.location.postcode:<12} "
               f"{area:<22} "
               f"{rec.distance_from_prev_km:<12.2f} "
               f"{rec.travel_minutes:<14.1f} "
               f"{rec.arrived_at.strftime('%H:%M')}")
        lines.append(row)

    lines.append("")

    # 2-opt improvement log
    lines.append("2-OPT IMPROVEMENT LOG")
    lines.append(thin)
    for entry in report.opt_result.improvement_log:
        lines.append(f"  {entry}")
    lines.append("")

    # Algorithm explanation (for A-level write-up)
    lines.append("ALGORITHM NOTES")
    lines.append(thin)
    lines.append("  The Travelling Salesman Problem (TSP) asks: given a set of")
    lines.append("  cities, what is the shortest route visiting each exactly once?")
    lines.append("  This is an NP-hard problem — no polynomial-time exact algorithm")
    lines.append("  is known for large inputs.")
    lines.append("")
    lines.append("  This program uses a two-phase approach:")
    lines.append("  1. Nearest-Neighbour Heuristic — O(n²) greedy seed route.")
    lines.append("  2. 2-Opt Local Search — iteratively reverses sub-routes")
    lines.append("     until no improving swap exists (local optimum).")
    lines.append("")
    lines.append("  Distances are computed using the Haversine formula, which")
    lines.append("  accounts for Earth's curvature to give accurate km distances")
    lines.append("  from latitude/longitude coordinate pairs.")
    lines.append("")
    lines.append(sep)

    return "\n".join(lines)


def save_report(report: DeliveryReport, filepath: str) -> str:
    """
    Save the text report to a file. Returns the filepath used.
    """
    if not filepath.endswith(".txt"):
        filepath += ".txt"

    text = generate_text_report(report)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

    return filepath
