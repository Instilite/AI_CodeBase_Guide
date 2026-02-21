ENCRYPTION_SOURCE = r"7elL2GJVkrv0dQ%Eb?N6uw*#t!@hYAop&O^a3FWCyKUT4PR5zBjDH8XgZnf9qMm1cSIsi$x "

#input validation for password
def password_validation(password):
    
    #finds the lenght of the password
    length = len(password)
    correct_length = False
    if length > 8:
        correct_length = True
    
    #bool statements if the password had something
    has_upper = False
    has_lower = False
    has_special = False
    has_digit = False
    has_space = " " in password
    has_invalid = False
    
    #strings of valid and invalid special characters
    valid_special_characters = "!@#$%^&*?"
    invalid_special_characters = "[,/"
    
    #checks if the password has met a condition. if it has, it changes it to true
    for char in password:
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char.isdigit():
            has_digit = True
        elif char in valid_special_characters:
            has_special = True
        elif char in invalid_special_characters:
            has_invalid = True
            

    issues = []  # List to collect issues

    # Collect issues based on the checks
    if not correct_length:
        issues.append("Password should be at least 8 characters")
    if not has_upper:
        issues.append("Missing an uppercase letter in the password")
    if not has_lower:
        issues.append("Missing a lowercase letter in the password")
    if not has_special:
        issues.append("Missing a special character in the password")
    if not has_digit:
        issues.append("Missing a digit in the password")
    if has_space:
        issues.append("Password should not have any spaces")
    if has_invalid:
        issues.append("[, / are not allowed in the password")

    # Print issues if any are found
    if issues:  # Only print "Issues:" if there are any collected issues
        print("\nIssues:")
        for issue in issues:
            print(f"     {issue}")

    return correct_length, has_upper, has_lower, has_digit, has_special, not has_space

#encrypts the website and password (initially was designed for passwords)
def password_encryption(password, key):    
    
    #stores the encrypted letter in a list
    encrypted_password = ""
    len_source = len(ENCRYPTION_SOURCE)
    
    #increments the letter based on the key
    for char in password:
        if char in ENCRYPTION_SOURCE:
            orignal_pos = ENCRYPTION_SOURCE.index(char)
            
            new_pos = (orignal_pos - key) % len_source
            
            encrypted_char = ENCRYPTION_SOURCE[new_pos]
            
            encrypted_password = encrypted_password + encrypted_char
        
        else:
            encrypted_password = encrypted_password + char
    
    return encrypted_password
        
def main():
    #asks for the key shift input
    key = int(input("Enter encryption key: "))
    
    #opens the file to write the kay
    with open('saved_passwords.txt', 'a') as file:
            file.write(str(key) + '\n')
    file.close()
    
    #loops until the user says that they dont want to add any more passwords
    while True:
        
        #stores the website, striping and lowering it
        website = (str(input("\nEnter website: "))).lower().strip()
        
        #loops unitl the user gets the password right, and matches the input validation requirements
        while True:
            password = str(input("Enter password: "))
            
            correct_lenght, has_upper, has_lower, has_digit, has_special, has_space = password_validation(password)
            
            #checks if any of the input validation is false and if it is, it prompts the user to enter the password again
            if correct_lenght and has_upper and has_lower and has_digit and has_special and has_space:
                break
            else:
                print("\nPlease enter a strong valid password")
        
        #calls the function to encrypt the password and website
        encry_password = password_encryption(password, key)
        encry_website = password_encryption(website,key)

        #stores the encrypted password in a text file
        with open('saved_passwords.txt', 'a') as file:
            file.write(encry_website + '\n')
            file.write(encry_password + '\n')

        file.close()
        
        print(f"\nPassword for {website} has been encrypted and stored successfully")

        #prompts the user if they want to add another password for another website
        another_password = input("Add another password? (y/n): ")
        if another_password == "n":
            print("Goodbye")
            break
        


if __name__ == "__main__":
    main()