# =================================================================
# CMPUT 175 - Introduction to the Foundations of Computation II
# Lab 6 - Advanced Music Queue
#
# ~ Created by CMPUT 175 Team ~
# ============================================================

def time_to_seconds(time_str):
    """
    Input: A string representing time in the format "hh:mm:ss"
    Returns: Total seconds in the time string
    Working:
    This function converts the time string into total seconds.
    """
    parts = time_str.split(":")

    if len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
    elif len(parts) == 2:
        minutes, seconds = map(int, parts)
        hours = 0
    else:
        raise ValueError("Invalid time format")
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

def seconds_to_time_format(seconds):
    """
    Input: Total seconds
    Returns: Time string in the format "hh:mm:ss"
    Working:
    This function converts the total seconds into a time string.
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes}:{seconds:02}"

class Song:
    def __init__(self, name, artist, dur):
        """
        Input: Name of the song, Artist of the song, Duration of the song
        Returns: None
        Working:
        This function initializes the Song object with the name, artist, and duration
        """
        assert type(name) == str
        assert type(artist) == str
        assert type(dur) == int

        self.__name = name
        self.__artist = artist
        self.__duration = dur

    def get_name(self):
        """
        Input: None
        Returns: Name of the song
        """
        return self.__name

    def get_artist(self):
        """
        Input: None
        Returns: Artist of the song
        """
        return self.__artist

    def get_duration(self):
        """
        Input: None
        Returns: Duration of the song
        """
        return self.__duration
    
    def __str__(self):
        """
        Input: None
        Returns: String representation of the song
        """
        return f"{self.__name}\n   Artists: {self.__artist}\n   Duration: {seconds_to_time_format(self.__duration)}"

class DLinkedListNode:
    def __init__(self,initData,initNext,initPrevious):
        """
        Input: Data to be stored in the node, Next node in the list, Previous node in the list
        Returns: None
        Working:
        Initializes the node with the given data, next node, and previous node.
        """
        self.data = initData
        self.next = initNext
        self.previous = initPrevious
        
        if initNext != None:
            self.next.previous = self
        if initPrevious != None:
            self.previous.next = self
            
    def get_data(self):
        """
        Input: None
        Returns: Data stored in the node
        """
        return self.data
    
    def set_data(self,newData):
        """
        Input: New data to be stored in the node`
        Returns: None
        Working:
        Sets the data in the node to the given data.
        """
        self.data = newData
        
    def get_next(self):
        """
        Input: None
        Returns: Next node in the list
        """
        return self.next
    
    def get_previous(self):
        """
        Input: None
        Returns: Previous node in the list
        """
        return self.previous
    
    def set_next(self,newNext):
        """
        Input: New next node in the list
        Returns: None
        Working:
        Sets the next node in the list to the given node.
        """
        self.next = newNext
        
    def set_previous(self,newPrevious):
        """
        Input: New previous node in the list
        Returns: None
        Working:
        Sets the previous node in the list to the given node.
        """
        self.previous = newPrevious

class DLinkedList:
    # An instance of this class represents the Doubly-Linked List
    def __init__(self):
        """
        Input: None
        Returns: None
        Working:
        Initializes the Doubly-Linked List with head, tail, current, size, and duration.
        """
        self.__head=None
        self.__tail=None
        self.__current = None
        self.__size=0
        self.__duration = 0             
         
    def add_next(self, item: Song):
        """
        Input: A Song object
        Returns: None
        Working:
        Add a song right next to the current song.
        """
        # TODO: Implement this method
        newNode = DLinkedListNode(item, None, None)
    
        if self.__current is None:  # If queue is empty
            self.__head = self.__tail = self.__current = newNode
        else:
            newNode.previous = self.__current
            newNode.next = self.__current.next

            if self.__current.next is not None:
                self.__current.next.previous = newNode
            
            self.__current.next = newNode
            
            if self.__current == self.__tail:
                self.__tail = newNode

        self.__size += 1
        self.__duration += item.get_duration()
    
    def add_last(self, item: Song):
        """
        Input: A Song object
        Returns: None
        Working:
        Add a song at the end of the Queue.
        """
        # TODO: Implement this method
        newNode = DLinkedListNode(item, None, None)
        
        if self.__current == None:
            self.__head = self.__tail = self.__current = newNode
        else:
            self.__tail.next = newNode
            newNode.previous = self.__tail
            self.__tail = newNode
            
        self.__size += 1
        self.__duration += item.get_duration()
        

    def get_current(self):
        """
        Input: None
        Returns: The current song.
        Working:
        Returns the current song.
        """
        # TODO: Implement this method
        if self.__current is None:
            raise Exception("The queue is empty. No song is currently playing.")
        return self.__current.get_data()
    def play_next(self):
        """
        Input: None
        Returns: None
        Working:
        Moves the current pointer to the next song.
        """
        # TODO: Implement this method

        if self.__current is None:
            raise Exception("No songs in the queue to play next.")  # ✅ Handle empty queue

        if self.__current.next is not None:  # ✅ Only move if there is a next song
            self.__current = self.__current.next


    def play_previous(self):
        """
        Input: None
        Returns: None
        Working:
        Moves the current pointer to the previous song.
        """
        # TODO: Implement this method
        if self.__current and self.__current.previous:
            self.__current = self.__current.previous

    def remove_current(self):
        """
        Input: None
        Returns: The current song
        Working:
        Removes the current song from the Queue.
        By Default, after removing the current song, the next song becomes current.
        If last song is being removed, the previous one becomes current.
        """
        # TODO: Implement this method
        if self.__current is None:
            raise Exception("No song to remove.")

        removed_song = self.__current

        if self.__current == self.__head:
            self.__head = self.__current.next
            if self.__head:
                self.__head.previous = None
            self.__current = self.__head

        elif self.__current == self.__tail:
            self.__tail = self.__current.previous
            if self.__tail:
                self.__tail.next = None
            self.__current = self.__tail

        else:
            self.__current.previous.next = self.__current.next
            self.__current.next.previous = self.__current.previous
            self.__current = self.__current.next

        self.__size -= 1
        self.__duration -= removed_song.get_data().get_duration()

        return removed_song
            
    def get_size(self):
        """
        Input: None
        Returns: The number of songs in the Queue.
        Working:
        Returns the number of songs in the Queue.        
        """
        # TODO: Implement this method
        
        return self.__size
    
    def is_empty(self):
        """
        Input: None       
        Returns: True if the Queue is empty, False otherwise.
        """
        # TODO: Implement this method
        
        return self.__size == 0

    def clear(self):
        """
        Clears the Queue.
        """
        # TODO: Implement this method
        
        self.__head=None
        self.__tail=None
        self.__current = None
        self.__size=0
        self.__duration = 0 
      
    def __str__(self):
        """
        Input: None
        Returns: A string representation of the Queue.
        Working:
        Returns a string representation of the Queue.
        """
        current = self.__head
        str_exp = f"\nQUEUE LENGTH: {seconds_to_time_format(self.__duration)}\nSONGS QUEUED: {self.__size}\n"
        for i in range(self.__size):
            if current == self.__current:
                str_exp += f"\033[32m{i+1}. {current.get_data()}\n\033[0m"
            else:
                str_exp += f"{i+1}. {current.get_data()}\n"
            current = current.get_next()
        return str_exp.strip('\n')

def main():
    """
    Main function to test the Doubly-Linked List implementation.
    ** You can add more test cases to test the implementation further. **
    ** You can add print statements to see the output in-between the test cases. **
    """
                  
    music_queue = DLinkedList()
    song1 = Song("I Want It That Way", "Backstreet Boys", time_to_seconds("3:39"))
    song2 = Song("Baby Shark", "CoComelon", time_to_seconds("2:24"))
    song3 = Song("The Time Is Now", "John Cena", time_to_seconds("2:56"))
    song4 = Song("Wavy", "Karan Aujla", time_to_seconds("2:40"))
    song5 = Song("Espresso", "Sabrina Carpenter", time_to_seconds("2:56"))

    # Testing add_last(), get_current() and remove_current()
    music_queue.add_last(song1)
    assert music_queue.get_current() == song1, "Test Case 1 Failed: get_current() or add_last() is not working properly"
    assert music_queue.remove_current().get_data() == song1, "Test Case 1 Failed: remove_current() is not working properly"
    print("Test Case 1 Passed: add_last(), get_current() and remove_current() are working properly")

    # Testing add_next() and get_size()
    music_queue.add_next(song2)
    music_queue.add_last(song5)
    assert music_queue.get_size() == 2, "Test Case 1 Failed: get_size() is not working properly"
    print("Test Case 2 Passed: add_next() and get_size() are working properly")

    # Testing play_next() and play_previous()
    music_queue.add_next(song3)
    music_queue.add_next(song4)
    music_queue.play_next()
    assert music_queue.get_current() == song4, "Test Case 3 Failed: play_next() is not working properly"
    print("Test Case 3 Passed: play_next() is working properly")

    # Testing play_previous()
    music_queue.play_previous()
    assert music_queue.get_current() == song2, "Test Case 4 Failed: play_previous() is not working properly"
    print("Test Case 4 Passed: play_previous() is working properly")

    # Testing clear() and is_empty()
    music_queue.clear()
    assert music_queue.is_empty() == True, "Test Case 5 Failed: is_empty() is not working properly"
    print("Test Case 5 Passed: clear() and is_empty() are working properly")

    print("\n**All test cases passed successfully!**\n")
                
if __name__ == '__main__':
    main()