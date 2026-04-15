# Importing algorithms 

from algorithm import Location, optimise_route, two_opt_swap, two_opt
from geocoder import bulk_geocode







def main():

    # Hard coding stops and depot
    depot_postcode = "SW1A 1AA"
    stop_postcodes = [
        "LE16 8HN",
        "B29 7AY",
        "L3 6BU",
        "NN18 8SP"
    ]

    # Converting postcodes into longitude and latitude coordinates
    all_postcodes = [depot_postcode] + stop_postcodes
    results = bulk_geocode(all_postcodes)
    if results[0] is None:
        print(f"Could not geocode depot postcode: {depot_postcode}")
        return
    
    # Creating instances of location class for stops and depot. 
    depot_data = results[0]
    depot = Location(
        postcode=depot_data["postcode"],
        lat=depot_data["lat"],
        lng=depot_data["lng"],
        district=depot_data["district"],
        ward=depot_data["ward"],
    )

    stops = []
    for original, data in zip(stop_postcodes, results[1:]):
        if data is None:
            print(f"Could not geocode stop postcode: {original}")
            return

        stops.append(Location(
            postcode=data["postcode"],
            lat=data["lat"],
            lng=data["lng"],
            district=data["district"],
            ward=data["ward"],
        ))

    
    # Running route optimisation
    result = optimise_route(depot, stops)

    # Printing optimised code.
    print("Optimised route:")
    print(depot.postcode)
    for stop in result.route:
        print(stop.postcode)
    print(depot.postcode)

    print(f"\nTotal distance: {result.total_distance_km:.2f} km")


if __name__ == "__main__":
    main()