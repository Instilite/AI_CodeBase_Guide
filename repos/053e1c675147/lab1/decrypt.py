ENCRYPTION_SOURCE = r"7elL2GJVkrv0dQ%Eb?N6uw*#t!@hYAop&O^a3FWCyKUT4PR5zBjDH8XgZnf9qMm1cSIsi$x "

#function that divides the companies and passwords into two lists
def div_companies_passwords(list):
    length = len(list)
    i = 0
    companies = []
    passwords = []
    
    while i < length:
        element = list[i].strip()
        if i % 2 == 0:
            companies.append(element)
        else:
            passwords.append(element)
        i = i + 1
    
    return companies, passwords

#a function that is designed to decrypt the list
def decrypt(list, key):
    variable_list = []
    key = int(key)
    i = 0
    
    #loops until the end of the list
    while i < len(list):
        encrypted_variable = list[i]
        variable = ""
        len_source = len(ENCRYPTION_SOURCE)
        
        #decrypts the letter
        for encrypted_char in encrypted_variable:
            if encrypted_char in ENCRYPTION_SOURCE:
                orignal_pos = ENCRYPTION_SOURCE.index(encrypted_char)
                
                new_pos = (orignal_pos + key) % len_source
                
                char = ENCRYPTION_SOURCE[new_pos]
                
                variable = variable + char
            
            else:
                variable = variable + encrypted_char
        
        i = i + 1
        
        #stores the final letter into the main word
        variable_list.append(variable)
    
    #returns the list of decrypted words
    return variable_list

#creates a dictionary which takes in elements of two list and combines them into key-value pairs
def create_dict(list1, list2):
    i = 0
    dictonary = {
        
    }
    
    while i < len(list1):
        dictonary[list1[i]] = list2[i]
        i = i + 1
    
    return dictonary

def main():
    
    #asks the user to input the file name
    filename = input("Enter filename: ")
    
    #reads all the lines in the files and stores each line in a list
    with open(filename, "r") as file:
        lines = file.readlines()
    
    file.close
    
    #stores the first element of the list as a key
    key = lines[0].strip()
    list_c_and_p = lines[1:]
    
    #stores the data from the text in two sepetate lists
    encrypted_companies, encrypted_passwords = div_companies_passwords(list_c_and_p)
    
    decrypted_companies = decrypt(encrypted_companies, key)
    decrypted_passwords = decrypt(encrypted_passwords, key)
    
    companies_password_dict = create_dict(decrypted_companies, decrypted_passwords)
    
    website = input("\nEnter a website: ").lower()
    
    while True:        
        in_dict = website in companies_password_dict
        
        if in_dict == False:
            print("The website doesn’t exist. ")
        else:
            password = companies_password_dict.get(website)
            print(f"Password for {website} is '{password}'")
        
        another_password = input("\nGet another password? (y/n): ")
        if another_password == "n":
            print("Goodbye!")
            break
        else:
            website = input("Enter a website: ").lower()
            
        
    
    
if __name__ == "__main__":
    main()