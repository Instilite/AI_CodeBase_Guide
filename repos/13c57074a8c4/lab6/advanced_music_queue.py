# =================================================================
# CMPUT 175 - Introduction to the Foundations of Computation II
# Lab 6 - Advanced Music Queue
#
# ~ Created by CMPUT 175 Team ~
# ============================================================

# Install ytmusicapi using pip
from ytmusicapi import YTMusic
from structures import DLinkedListNode, DLinkedList, Song, time_to_seconds
import os

NO_OF_RESULTS = 5

def clear():
    '''
    Clears the screen based on the operating system.
    '''
    if os.name == "posix":
        os.system('clear')
    else:
        os.system('cls')

def extract_artists(song):
    """
    Input: A dictionary containing song information
    Returns: A string of artist names separated by commas
    Working:
    This function extracts and returns a comma-separated string of artist names from the song dictionary.
    """
    # TODO: Implement this function
    if "artists" in song:
        artists_info = ", ".join(artist["name"] for artist in song["artists"])
        return artists_info
    else:
        return "NA"

def song_search(query):
    """
    Input: Search query
    Returns: Top "NO_OF_RESULTS" i.e. 5 results from the retrieved data
    Working:
    This function invokes the search method on YTMusic object with required arguments
    """
    # TODO: Implement this function
    ytmusic = YTMusic()
    results = ytmusic.search(query, filter="songs")
    return results[:NO_OF_RESULTS]

def filter_info(results):
    """
    Input: Search results in a JSON like format
    Returns: List of Song Objects
    Working:
    This function is supposed to extract the required information from the JSON,
    create Song objects and append them to a list. If an error occurs, raise an
    exception.
    """
    # TODO: Implement this function
    song_list = []
    for song in results:
        title = song.get("title", "Unknown Title")
        artist = extract_artists(song)
        duration = song.get("duration", "0:00")
        duration_sec = time_to_seconds(duration)
        song_object = Song(title, artist, duration_sec)
        song_list.append(song_object)
    return song_list

def print_song_results(results):
    """
    Input: A list of Song objects
    Returns: None
    Working:
    This function prints the list of Song objects in a formatted manner.
    """
    assert type(results[0]) == Song, "The list to be printed doesn't have the items of type 'Song'"

    print("RESULTS:")
    for i in range(len(results)):
        print(f"{i+1}. {results[i]}")

def search():
    """
    Input: None
    Return: A Song object representing the song the user wants to add into the Queue, or None if the user wants to go back
    Working:
    1. This function takes search query from the user
    2. Searches for the song using song_search function
    3. Filters the information using filter_info function
    4. Prints the song results using print_song_results function
    5. Asks for user choice
    6. Returns the chosen song information
    7. If the user wants to go back, it returns None
    """
    # TODO: Implement this function
    clear()
    number_picked = f"""Choose one of the following options:
                    \tEnter a number (1-{NO_OF_RESULTS}) to add a song to playlist
                    \tEnter "0" to search again
                    \tEnter "q" to go back
>>"""
    query = input("Search: ").strip()
    
    result_of_search = song_search(query)
    filtered_search = filter_info(result_of_search)
    
    print_song_results(filtered_search)
    while True:
        choice = input(number_picked).strip().lower()

        if choice == "q":
            return None

        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= NO_OF_RESULTS:
                return filtered_search[choice - 1]
            elif choice == 0:
                return None

        print("Invalid input. Please enter a valid number, '0' to search again, or 'q' to go back.")
        

def main():
    """
    Initializes the music queue and provides an interactive menu to manage songs.
    Users can add songs, navigate to next or previous songs, remove the current song,
    display or clear the queue, and quit the program.

    NOTE: You need to modify the main function to use the DLinkedList class to manage the music queue. 
          Add the new features that are needed for this Lab assignment as per the description.

          ** MAKE SURE YOU READ THE DESCRIPTION CAREFULLY AND UNDERSTAND THE REQUIREMENTS. **
    """
    queue = DLinkedList()
    clear()
    print("WELCOME\n")
    choice_str = """Choose one of the following options:
                    \t1. Add Song
                    \t2. Next Song
                    \t3. Previous Song
                    \t4. Remove Current Song
                    \t5. Show Queue
                    \t6. Clear Queue
                    \t7. Quit
                    \tEnter the choice (eg: 2)
                """
    contBuild = True
    try:
        while contBuild:

            print('Currently playing:')
            if queue.is_empty() == False: 
                print('  ',queue.get_current(),'\n')
            else: 
                print('  ',"None",'\n')

            print(choice_str)
            choice = input('>> ')
            while choice not in ['1','2','3','4','5','6','7']:
                print('Invalid Input.')
                choice = input('>> ')
            
            if choice == '1':
                song = search()
                if song is not None:
                    if queue.is_empty():
                        queue.add_last(song)
                    else:
                        place = input("Where would you like to add the song:\n\t1. Top\n\t2. End\n>> ")
                        while place not in ['1','2']:
                            print('Invalid Input.')
                            place = input('>> ')
                        
                        if place == '1':
                            queue.add_next(song)
                        elif place == '2':
                            queue.add_last(song)
                    print("Song added successfully!")
                    input("\nPress enter key to continue...")

            elif choice == '2':
                clear()
                queue.play_next()
                print('Now playing:')
                if queue.get_size() > 0:
                    print("  ",queue.get_current())
                else:
                    print("   None")
                input("\nPress enter key to continue...")

            elif choice == '3':
                clear()
                queue.play_previous()
                print('Now playing:')
                if queue.get_size() > 0:
                    print("  ",queue.get_current())
                else:
                    print("   None")
                input("\nPress enter key to continue...")
            
            elif choice == '4':
                clear()
                if not queue.is_empty():
                    removed_song = queue.remove_current()
                    print(f"{removed_song.get_data().get_name()} removed successfully!")
                    input("\nPress enter key to continue...")
                else:
                    print("No songs to remove")
                    input("\nPress enter key to continue...")
            
            elif choice == '5':
                clear()
                try:
                    print(queue)
                    input("\nPress enter key to continue...")
                except Exception as e:
                    print(e)        
                        
            elif choice == '6':
                clear()
                queue.clear()
                print('The queue has been cleared!')
                input("\nPress enter key to continue...")
                
            elif choice == '7':
                contBuild = False
            
            clear()

    except Exception as e:
        print(e)

    print("Thanks for listening!")

if __name__ == "__main__":
    main()