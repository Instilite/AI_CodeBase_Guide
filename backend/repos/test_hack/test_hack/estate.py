""" 
estate.py

This program is a location based property report generator, used to process structured real estate data from properties.txt,
ownership.txt, and price_index.txt. First all the information in the aforementioned files is read by the program, and then stored
into different data structures. The data structures will then be used to aggregate price, and area while also providing the number
of available properties in each location. Finally, the program will output the calculated data in the form a formatted table.

"""

def read_price_index_file():
    """
    reads the price_index.txt file

    builds: 
    - avg_sqft_price: a dictionary that intakes the average price per square foot for each location. Stores location as key
    and average price per square foot for each location. 

    returns the dictionary

    """
    avg_sqft_price = {}
    FILE_NAME = "price_index.txt"
    with open(FILE_NAME, "r", encoding="utf-8") as avg_sqft_price_file_obj:
        next(avg_sqft_price_file_obj)
        for line in avg_sqft_price_file_obj:
            line = line.strip()
            if line != "":
                location, price = line.split(",", 1)
                avg_sqft_price[location] = float(price) # allows price to be returned as float
    return avg_sqft_price

def read_ownership_file():
    """
    reads the ownership.txt file

    builds: 
    - ownership: a dictionary that contains the unique ID for each owner and a list as the value with the name, and the year
    the owner company was established

    returns the dictionary

    """
    ownership = {}
    FILE_NAME = "ownership.txt"
    with open(FILE_NAME, "r", encoding="utf-8") as ownership_file_obj:
        next(ownership_file_obj)
        for line in ownership_file_obj:
            line = line.strip()
            if line != "":
                ID, name_and_year = line.split(",", 1)
                name_year_list = name_and_year.split(",")
                ownership[ID] = name_year_list
        return ownership
        
def read_properties_file():
    """
    reads the properties.txt file

    builds: 
    - property_info: a list that contains the location, rooms, area, and owner ID.

    returns the fully compiled list

    """
    property_info = []
    FILE_NAME = "properties.txt"
    with open(FILE_NAME, "r", encoding="utf-8") as property_info_file_obj:
        next(property_info_file_obj)
        for line in property_info_file_obj:
            clean_line = line.strip()
            if clean_line != "":
                parts = clean_line.split(",")
                rooms = int(parts[1])
                area = float(parts[2])
                owner_ID = int(parts[3])
                processed_row = [parts[0], rooms, area, owner_ID]
                property_info.append(processed_row)
        return property_info


def average_area():
    """
    calculates the average area specific to each location

    builds:
    - area_dict: a dictionary that temporarily stores the areas for each location with the
    location as the key and a list of all areas in that location as the value.
    - final_averages: a list that stores the final results in the form
    [location, average_area].

    returns the final_averages list for use in the next function
    """
    property_info = read_properties_file()
    area_dict = {}
    for i in property_info:
        if i[0] not in area_dict:
            area_dict[i[0]] = [i[2]]        
        else:
            area_dict[i[0]].append(i[2]) 
    final_averages = []
    for location, areas in area_dict.items():
        avg = sum(areas)/len(areas)
        final_averages.append([location, avg])
    return final_averages

def average_price():
    """
    calculates the average price for each location based on the average area and
    the price per square foot for that location.

    builds:
    - property_info: a nested list that now contains the location, average area,
    and the calculated average price.

    returns the updated nested list
    """
    property_info = average_area()
    price_info = read_price_index_file()
    
    for key, value in price_info.items():
        for row in property_info:
            if row[0] == key:
                avg_price = value * row[1]
                avg_price = round(avg_price, 2)
                row.append(avg_price)
    
    return property_info


def available_units():
    """
    calculates the number of available properties in each location (which are the properties
    that have 0 as the owner ID), and appends this value to the existing nested list.

    builds:
    - available_dict: a dictionary that stores location as the key, and the number of available
    properties in that location as the value.
    - property_info: a nested list that contains the location name, the average area,
    the average price, and the number of available units.

    returns the updated nested list for use in the main function
    """
    property_info = average_price()
    properties = read_properties_file()

    available_dict = {}
    for row in properties:
        location = row[0]
        owner_id = row[3]
        if owner_id == 0:
            if location not in available_dict:
                available_dict[location] = 1
            else:
                available_dict[location] += 1

    for row in property_info:
        location = row[0]
        if location not in available_dict:
            row.append(0)
        else:
            row.append(available_dict[location])

    return property_info


def main():
    """
    prints the final formatted table for option 1.

    flow:
    - calls the functions that calculate the average area, the average price, and the number of
    available properties for each location.
    - sorts the final list so that locations with the highest number of available units show up first.
    - prints the results in a formatted table that matches the sample output exactly.

    returns nothing
    """
    BORDER = "+---------------+---------------+---------------+-----------+"
    HEADER = "| Location      | Average Area  | Average Price | Available |"
    SQFT = " sqft"
    DOLLAR = "$ "

    final_list = available_units()

    final_list = sorted(final_list, key=lambda row: (-row[3], row[0]))

    print(BORDER)
    print(HEADER)
    print(BORDER)

    for row in final_list:
        location = row[0]
        avg_area = row[1]
        avg_price = row[2]
        available = row[3]

        area_field = f"{avg_area:,.2f}{SQFT}"
        price_field = f"{DOLLAR}{avg_price:>11,.2f}"

        print(f"| {location:<13} | {area_field:^13} | {price_field} | {available:>9} |")

    print(BORDER)

main()

        
