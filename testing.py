from geocoder import bulk_geocode
from algorithm import Location, build_distance_matrix, nearest_neighbour, route_distance, two_opt_swap, two_opt

depot_postcode = "SW1A 1AA"
stop_postcodes = [
        "LE16 8HN",
        "B29 7AY",
        "L3 6BU",
        "NN18 8SP",
        "YO12 5DF",
        "WS10 8LF",
        "SO53 3LD",
        "WS6 6HA",
        "KY99 9PP",
        "DH9 9PE",
        "SG12 7EG"
    ]

def test_geocoder(depot, stops):
    all_postcodes = [depot] + stops
    result = bulk_geocode(all_postcodes)
    print(result)
    return result


def test_distance_matrix(all_locs):
    dist_matrix = build_distance_matrix(all_locs)
    print("distance matrix:")
    print(dist_matrix)
    return dist_matrix


def test_nearest_neighbour(stops, depot, matrix, all_locs):
    nearest_neighbour_route = nearest_neighbour(stops, depot, matrix, all_locs)
    original_distance = route_distance(stops, depot, matrix, all_locs)
    nearest_neighbour_distance = route_distance(nearest_neighbour_route, depot, matrix, all_locs)
    percentage_improvement = ((original_distance - nearest_neighbour_distance)/original_distance)*100
    print("Orignal Route: ")
    print(stops)
    print("Nearest Neighbour Route: ")
    print(nearest_neighbour_route)
    print("Orignal distance: ")
    print(original_distance)
    print("Nearest Neigbour distance")
    print(nearest_neighbour_distance)
    print("% imporovemnt")
    print(f"{percentage_improvement}%")
    return nearest_neighbour_route


def test_2opt_swap():
    test_list = ["A", "B","C", "D", "E"]
    swap_loc_1 = 0
    swap_loc_2 = 2
    new_list = two_opt_swap(test_list, swap_loc_1, swap_loc_2)
    print("Starting test list:")
    print(test_list)
    print("New List:")
    print(new_list)
    

def test_2opt_optimiser(stops, depot, matrix, all_locs):
    print("two opt log: ")
    two_opt_route = two_opt(stops, depot, matrix, all_locs)
    print(f"\n\n Orignal Route: {stops} with a distance: {two_opt_route.initial_distance_km} km")
    print(f"New route {two_opt_route.route} with a distance: {two_opt_route.total_distance_km} km")

    percentage_improvement = ((two_opt_route.initial_distance_km - two_opt_route.total_distance_km)/two_opt_route.initial_distance_km)*100
    print(f"Impoved by: {percentage_improvement}%")


def test_nearest_neighbour_efficiency(stops, depot, matrix, all_locs):
    without_nearest_neihbour = two_opt(stops, depot, matrix, all_locs)
    nearest_neighbour_route = nearest_neighbour(stops, depot, matrix, all_locs)
    with_nearest_neighbour = two_opt(nearest_neighbour_route, depot, matrix, all_locs)
    print(f"Iterations without nearest neighbour: {without_nearest_neihbour.iterations}")
    print(f"Iterations with nearest neighbour: {with_nearest_neighbour.iterations}")
    print(f"Distance wihtout nearest neighbour: {without_nearest_neihbour.total_distance_km}")
    print(f"Distance with nearest neighbour: {with_nearest_neighbour.total_distance_km}")

def main():
    print("Testing Geocoder functionality\n")
    results = test_geocoder(depot_postcode, stop_postcodes)
    print("\n\n============================================================\n\n")
    print("Testing Distance Matrix")
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
        stops.append(Location(
            postcode=data["postcode"],
            lat=data["lat"],
            lng=data["lng"],
            district=data["district"],
            ward=data["ward"],
        ))
    
    all_locs = [depot] + stops

    matrix = test_distance_matrix(all_locs)
    print("\n\n============================================================\n\n")
    print("Testing Nearest Neighbour")
    nearest_neigbour_route = test_nearest_neighbour(stops, depot, matrix, all_locs)
    print("\n\n============================================================\n\n")
    print("Testing 2-opt swap: \n")
    test_2opt_swap()
    print("\n\n============================================================\n\n")
    print("Test 2-opt optimiser: ")
    test_2opt_optimiser(nearest_neigbour_route, depot, matrix, all_locs)
    print("\n\n============================================================\n\n")
    print("Testing speed improvement by using nearest neighbour first")
    test_nearest_neighbour_efficiency(stops, depot, matrix, all_locs)

    


if __name__ == "__main__":
    main()
