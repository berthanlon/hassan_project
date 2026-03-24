"""
RouteMax — 2-Opt Delivery Route Optimiser
==========================================
A-Level Computer Science Project

Entry point. Run this file to start the application:
    python main.py

Requirements:
    pip install requests
"""

from app import RouteMaxApp

if __name__ == "__main__":
    app = RouteMaxApp()
    app.run()