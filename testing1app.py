


from geocoder import bulk_geocode
from algorithm import Location, build_distance_matrix, nearest_neighbour, two_opt

import tkinter as tk
import mysql.connector
from datetime import datetime, timedelta
import tkinter.simpledialog as simpledialog




#Dictionary created Config for all the connection parameters to the database

config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Hassan2008',
    'database': 'db1'
}



#THEME FONTs AND COLOURS

BG = "#0a0a0f"
SURFACE = "#12121a"
ACCENT = "#e8ff47"
RED = "#ff4757"
GREEN = "#2ecc71"
TEXT = "#e8e8f0"

BUTTON_BG = ACCENT
BUTTON_FG = "#0a0a0f"

FONT_TITLE = ("Helvetica", 20, "bold")
FONT_BODY = ("Helvetica", 11)



#GLOBAL VARIABLES
stop_postcodes = []
depot_postcode = None
current_user_id = None

AVG_SPEED = 40

delivery_labels = []
estimated_times = []
delay_reasons = []

delivery_index = 0
original_distance_global = 0
start_time = None

root = None

current_route = None
current_depot = None
route_distances = []


#LOADING THE POSTCODES
def load_postcodes():
    global stop_postcodes

    conn = mysql.connector.connect(**config) #connecting to the database 
    cursor = conn.cursor()
    
    #selects postcodes from deliveries for the currently logged in driver and the current date
    cursor.execute(
       "SELECT postcode FROM deliveries WHERE driver=%s AND deliverydate=CURDATE()", 
       (current_user_id,)
    )   
    
    #fetches all of the postcodes which fufill the SELECT statement conditions
    stop_postcodes = []
    for row in cursor.fetchall():
        stop_postcodes.append(row[0])
        
    cursor.close() # ends the SQL cursor
    conn.close() # ends the database connection



#Runs SQL to check userid/password entered from login screen

def check_login(userid, password):
    conn = mysql.connector.connect(**config) #Config Dictionary
    cursor = conn.cursor() #Connect to DB
    #Execute the SQL
    cursor.execute(
        "SELECT depot FROM usertable WHERE userid=%s AND password=%s",
        (userid, password)
    )
    #Fetch first row returned from DB
    result = cursor.fetchone()
    #Close cursor and DB connection
    cursor.close()
    conn.close()
    
    #Return row from DB (valid login) or None if no result from the SQL (invalid login)
    if result:
       return result[0]
    else:
       return None


# Build and show the login screen
def login_screen():
    global login_root, depot_postcode, current_user_id
    
    #Title and size and colour of window
    login_root = tk.Tk()
    login_root.title("Route Master Login")
    login_root.geometry("500x250")
    login_root.configure(bg=BG)

    #Add User ID label and entry box
    tk.Label(login_root, text="User ID", bg=BG, fg=TEXT).pack()
    user_entry = tk.Entry(login_root)
    user_entry.pack()
    
    #Add Password label and entry box - hide the password as *
    tk.Label(login_root, text="Password", bg=BG, fg=TEXT).pack()
    pass_entry = tk.Entry(login_root, show="*")
    pass_entry.pack()

    #Setup a label without text if we need it to show an eeror on login
    error = tk.Label(login_root, fg=RED, bg=BG)
    error.pack()
   
    #This function called when Login button selected (Button command)
    def login_button():
        global depot_postcode, current_user_id

         #Call check_login function passing it userid and password and result returned to depot
        depot = check_login(user_entry.get(), pass_entry.get())


        if depot:
            #set global variables, close login screen and call main_app function
            depot_postcode = depot #given depot from check login function
            current_user_id = user_entry.get()   
            login_root.destroy()
            main_app()
        else:
            #show error on login screen
            error.config(text="Invalid userid/password")
    
    #Create login button
    tk.Button(
        login_root,
        text="Login",
        command=login_button,
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        relief="flat"
    ).pack(pady=10)

    #Keep login screen open until it is closed at a valid login
    login_root.mainloop()



#a
#Get depot and stop data
def get_data():
    #call bulk_geocode function to get all lon/lat coordinates for the depot and stop postcodes
    results = bulk_geocode([depot_postcode] + stop_postcodes)

    #Store all depot data returned from buld_geocode

    depot_data = results[0] #set depot_data dictionary = first item in results which is the depot information
    
    depot = Location(**depot_data) #Create an instance of the Location class for the depot
   
    stops = []
    for d in results[1:]:
        stops.append(Location(**d)) #adds into a list of stops and each stop is an instance of location class
   
    return depot, stops



#Calculate the original route distance

def calculate_original_distance(all_locs, matrix, depot, stops):
    #setting initial distance to 0
    total = 0
    prev = depot #initial stop is depot

    for stop in stops:
        i = all_locs.index(prev) #last stop visited
        j = all_locs.index(stop) #current stop
        dist_between_stops = matrix[i][j] #calculating the distance between previous and current stop
        total += dist_between_stops #tallying distances
        prev = stop #setting the current stop to the new previous

    return total







#Optimise route functiona called from the Optimise Route button


def optimise_route():
    global original_distance_global, start_time
    global current_route, current_depot, route_distances

    depot, stops = get_data() #getting depot and stop data

    all_locs = [depot] + stops #concatenate depot and stop list
    matrix = build_distance_matrix(all_locs)  #create distance matrix

    original_distance_global = calculate_original_distance(all_locs, matrix, depot, stops) #calculate distance before optimisation

    nn = nearest_neighbour(stops, depot, matrix, all_locs) #call nearest neighbour function
    final = two_opt(nn, depot, matrix, all_locs) #call two_opt function

    #Set the start time of the route
    start_time = datetime.now() 

    current_route = final #final is an instance of the OptimisationResult class returned from two_opt function
    current_depot = depot 

    #Call function to show optimised route in delivery window
    show_delivery_window(final, depot, all_locs, matrix)



#delivery window
def show_delivery_window(route_obj, depot, all_locs, matrix):
    global delivery_labels, estimated_times, delay_reasons, delivery_index, route_distances

    delivery_labels = []
    estimated_times = []
    delay_reasons = [None] * len(route_obj.route)
    route_distances = []
    delivery_index = 0
    
    #Create a new child window (win) on top of previous window (root)
    win = tk.Toplevel(root)
    win.title("Optimised Route")
    win.geometry("650x600")
    win.configure(bg=BG)

    tk.Label(win, text="Optimised Delivery Route", font=FONT_TITLE, bg=BG, fg=TEXT).pack()
    tk.Label(win, text="Optimised at: {}".format(start_time.strftime('%H:%M:%S')), bg=BG, fg=TEXT).pack()
   # tk.Label(win, text=f"Optimised at: {start_time.strftime('%H:%M:%S')}", bg=BG, fg=TEXT).pack()
 #a

   #Add a frame to contain the optimised route postcode list
    scroll_frame = tk.Frame(win, bg=BG)
    scroll_frame.pack(fill="both", expand=True)

    prev = depot
    total = 0
    current = start_time

    for stop in route_obj.route:

        i = all_locs.index(prev)
        j = all_locs.index(stop)

        dist = matrix[i][j]
        route_distances.append(dist)
        total += dist

        current += timedelta(hours=dist / AVG_SPEED)
        estimated_times.append(current)
        
        #For each stop in the route add a label to the frame
        lbl = tk.Label(
            scroll_frame,
            text="{} ({:.2f} km) ETA {}".format(stop.postcode, dist,current.strftime('%H:%M' ),
            width=55,
            anchor="w",
            bg=SURFACE,
            fg=TEXT
        ))
        lbl.pack(pady=2)
        #Append label to array so we know which label needs to be changed when delivered
        delivery_labels.append(lbl)
        prev = stop
    #Calculate improvement of optimised route in % and display as a label
    improvement = ((original_distance_global - total) / original_distance_global) * 100

    tk.Label(
        win,
        text="Total: {:.2f} km | Improvement: {:.2f}%".format(total, improvement),
        fg=ACCENT,
        bg=BG
    ).pack(pady=5)
    #Add Mark Delivered button to window
    tk.Button(win, text="Mark Delivered", command=mark_delivered, bg=BUTTON_BG).pack(pady=3)
  



#Mark stop as delivered
def mark_delivered():
    global delivery_index
    #Starts at first label in the delivery_index
    if delivery_index < len(delivery_labels):
        now = datetime.now()
        eta = estimated_times[delivery_index]
        lbl = delivery_labels[delivery_index]

        if now <= eta:
            #For early or ontime delivery change background to green
            lbl.config(bg=GREEN)
        else:
            #For late delivery background is red
            lbl.config(bg=RED)
            #Show Tkinter simpledialog.askstring to get reason for delay
            #Could not change the background colour of this dialog
            reason = simpledialog.askstring("Delay Reason", "Why was it late?")
            delay_reasons[delivery_index] = reason


#updating the sql database with estimated delivery time, and the delivered column which is boolean for the corresponding logged in user
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()

            postcode = current_route.route[delivery_index].postcode
          
            cursor.execute(
    "UPDATE deliveries SET estimateddelivery=%s, actualdelivery=%s, Delivered=TRUE WHERE postcode=%s AND driver=%s AND deliverydate=CURDATE()",
    (
        eta.strftime('%Y-%m-%d %H:%M'), #Casting - change string to time format
        now.strftime('%Y-%m-%d %H:%M'),
        postcode,
        current_user_id
    )
)

            conn.commit()
            cursor.close()
            conn.close()

        #increment the index on the array for next delivery
        delivery_index += 1
        #If all deliveries complete show the report screen
        if delivery_index == len(delivery_labels):
            total_time = estimated_times[-1] - start_time
            show_delivery_report(current_route, current_depot, total_time)





def show_delivery_report(route_obj, depot, total_time):

    report = tk.Toplevel(root)
    report.title("Delivery Report") #title for the screen
    report.geometry("900x650") #size of the screen
    report.configure(bg=BG) #background colour of the screen

    tk.Label(report, text="FINAL DELIVERY REPORT", font=FONT_TITLE, bg=BG, fg=ACCENT).pack(pady=10) #label for the report screen

    total_distance = sum(route_distances) #sum of the distances 

    tk.Label(report, text="Total Distance: {:.2f} km".format(total_distance), bg=BG, fg=TEXT).pack() #displays the total distance on the screen
    tk.Label(report, text="Total Time: {}".format(total_time), bg=BG, fg=TEXT).pack() #displays the total time on the screen taken

    tk.Label(report, text="\nDistance Between Stops:", bg=BG, fg=ACCENT).pack() #displays the distance next to the postcode

    prev = depot.postcode
    for i, loc in enumerate(route_obj.route): #gives the index of the stops in the list
        dist = route_distances[i]
        tk.Label(
            report,
            text="{}  {} : {:.2f} km".format(prev, loc.postcode, dist), #displays the previous stop next stop and then the distance between them
            bg=BG,
            fg=TEXT
        ).pack()
        prev = loc.postcode

    on_time = sum(1 for r in delay_reasons if r is None) #tally the ontime deliveries
    delayed = sum(1 for r in delay_reasons if r) #tally the late deliveries 

    tk.Label(report, text="\nOn-time deliveries: {}".format(on_time), fg=GREEN, bg=BG).pack() #display label of ontime deliveries 
    tk.Label(report, text="Delayed deliveries: {}".format(delayed), fg=RED, bg=BG).pack() #displays the label of delayed deliveries

    tk.Label(report, text="\nDelay Reasons:", bg=BG, fg=ACCENT).pack()

    for i, r in enumerate(delay_reasons): #an array which holds the reason for delay
        if r:
            tk.Label(
                report,
                text="{}: {}".format(route_obj.route[i].postcode, r),
                bg=BG,
                fg=TEXT
            ).pack()

    tk.Button(report, text="Close", command=report.destroy, bg=BUTTON_BG, fg=BUTTON_FG).pack(pady=20) #closes the delivery report



#main app

def main_app():
    global root, stop_postcodes
  
    #Function to load the postcodes from DB for logged in user
    load_postcodes()

    #Build window to show postcodes for delivery unoptimised
    root = tk.Tk()
    root.title("Route Master")
    root.geometry("1000x1000")
    root.configure(bg=BG)

    tk.Label(root, text="Original Route", font=FONT_TITLE, bg=BG, fg=TEXT).pack()
    
    #Create list box to contain the postcodes
    listbox = tk.Listbox(root, width=60, height=20)
    listbox.pack()

    #Function to populate listbox containing all stops and distances - unoptimised
    def display_original():
     
        depot, stops = get_data()

        all_locs = [depot] + stops
      
        matrix = build_distance_matrix(all_locs)
        
        #Clears contents of listbox
        listbox.delete(0, tk.END)

        prev = depot
        total = 0
        
        #Insert contents to list box, does not add the depot
        for stop in stops:
            i = all_locs.index(prev)
            j = all_locs.index(stop)

            dist = matrix[i][j]
            #Keep a tally of the entire distance
            total += dist
                
            listbox.insert(tk.END, "{} ({:.2f} km)".format(stop.postcode, dist)),
            prev = stop
        #Insert total distance     
        listbox.insert(tk.END, "Total: {:.2f} km".format(total)),

    display_original()
    tk.Button(root, text="Optimise Route", command=optimise_route, bg=BUTTON_BG).pack(pady=10)
    root.mainloop()



#Program start here - call the login_screen function

login_screen()
