# -*- coding: utf-8 -*-
"""
Generates a plain-text delivery report and saves it to a .txt file.
Also provides data structures for the report summary shown in the GUI.
"""

import os
from datetime import datetime, timedelta
from dataclasses import dataclass

from algorithm import Location, OptimisationResult


# Data model

@dataclass
class StopRecord:
    """Records the outcome of a single delivery stop."""
    stop_index: int         
    location: Location
    arrived_at: datetime
    estimated_arrival: datetime
    distance_from_prev_km: float
    travel_minutes: float
    is_late: bool = False


@dataclass
class DeliveryReport:
    depot: Location
    route: list[Location]
    records: list[StopRecord]
    start_time: datetime
    opt_result: OptimisationResult
    driver_name: str = ""

    # Computed properties

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


# Report generation 

def generate_text_report(report: DeliveryReport) -> str:
    """
    Produce a formatted plain-text report string.
    """
    seperator = "=" * 60
    thin = "-" * 60
    lines = []

    lines.append(seperator)
    lines.append("  ROUTEMASTER - DELIVERY REPORT")
    lines.append(f"  Driver:    {report.driver_name if report.driver_name else 'Not specified'}")
    lines.append(f"  Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append(seperator)
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


    # Highlights
    lines.append("HIGHLIGHTS")
    lines.append(thin)
    fastest = report.fastest_stop
    slowest = report.slowest_stop
    lines.append(f"  Fastest stop:  Stop {fastest.stop_index + 1} - {fastest.location.postcode} "
                 f"({fastest.travel_minutes:.1f} min, {fastest.distance_from_prev_km:.2f} km)")
    lines.append(f"  Slowest stop:  Stop {slowest.stop_index + 1} - {slowest.location.postcode} "
                 f"({slowest.travel_minutes:.1f} min, {slowest.distance_from_prev_km:.2f} km)")
    lines.append("")

    # Stop-by-stop table
    lines.append("STOP-BY-STOP BREAKDOWN")
    lines.append(thin)
    header = f"  {'#':<4} {'Postcode':<12} {'Area':<18} {'Dist':<8} {'Est.':<8} {'Actual':<8} {'Status'}"
    lines.append(header)
    lines.append(f"  {'-'*4} {'-'*12} {'-'*18} {'-'*8} {'-'*8} {'-'*8} {'-'*7}")

    for rec in report.records:
        area   = rec.location.district[:16] if rec.location.district else "-"
        status = "LATE" if rec.is_late else "ON TIME"
        row = (f"  {rec.stop_index + 1:<4} "
               f"{rec.location.postcode:<12} "
               f"{area:<18} "
               f"{rec.distance_from_prev_km:<8.2f} "
               f"{rec.estimated_arrival.strftime('%H:%M'):<8} "
               f"{rec.arrived_at.strftime('%H:%M'):<8} "
               f"{status}")
        lines.append(row)

    lines.append("")

    lines.append(seperator)

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


def save_csv(report, filepath):
    """
    Save the stop-by-stop data as a CSV file. Returns the filepath used.
    """
    import csv

    if not filepath.endswith(".csv"):
        filepath += ".csv"

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header metadata
        writer.writerow(["RouteMaster Delivery Report"])
        writer.writerow(["Driver", report.driver_name if report.driver_name else "Not specified"])
        writer.writerow(["Generated", datetime.now().strftime("%d/%m/%Y %H:%M")])
        writer.writerow(["Depot", report.depot.postcode, report.depot.district])
        writer.writerow(["Start Time", report.start_time.strftime("%H:%M")])
        writer.writerow(["Total Distance (km)", round(report.total_km, 2)])
        writer.writerow(["Total Time (min)", round(report.total_minutes, 0)])
        writer.writerow(["Stops Completed", len(report.records)])
        writer.writerow(["NN Seed Distance (km)", round(report.opt_result.initial_distance_km, 2)])
        writer.writerow(["2-opt Distance (km)", round(report.opt_result.total_distance_km, 2)])
        writer.writerow(["2-opt Iterations", report.opt_result.iterations])
        writer.writerow([])

        # Stop-by-stop data
        writer.writerow(["Stop #", "Postcode", "Area", "Distance (km)", "Est. Arrival", "Actual Arrival", "Travel (min)", "Status"])
        for rec in report.records:
            writer.writerow([
                rec.stop_index + 1,
                rec.location.postcode,
                rec.location.district or "",
                round(rec.distance_from_prev_km, 2),
                rec.estimated_arrival.strftime("%H:%M"),
                rec.arrived_at.strftime("%H:%M"),
                round(rec.travel_minutes, 1),
                "LATE" if rec.is_late else "ON TIME",
            ])

    return filepath