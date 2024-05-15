'''
Author: Aakash Subedi
Date: 12/8/2023
'''
import socket
import sys

#input validation for client, expecting format "python client.py {address} {port number}"
def validateArguments(args):
    if(len(args) != 3):
        #invalid arguments -> too many/ too little arguments passed
        return -1,-1 
        
    server_address = args[1]
    server_port = args[2]

    #make sure server_address is between 0.0.0.0-255.255.255.255 (even if a lot of those values are usable)
    address_list_split = server_address.split('.')
    if(len(address_list_split) != 4):
        #invalid address -> top many / too little sections in address
        return -1, -1
    try:
        for digits in address_list_split:
            potential_addr_section = int(digits)
            if potential_addr_section < 0 or potential_addr_section > 255:
                #invalid address -> digits in address are not usable
                return -1,-1
    except:
        #invald address -> non integer section included
        return -1,-1
    

    try:
        potential_port = int(server_port)
        if 1024 <= potential_port <= 65535:
            return server_address, potential_port
    except:
        return -1,-1
    
    return server_address, int(server_port)

def main(server_addr, server_port):
    #create socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_addr, server_port))
    except:
        print("Error connecting to that address and port.")
        exit()
    
    #driving loop to play blackjack + talk to server, terminates with
    server_reply = ""
    while server_reply != "End Session":
        try:
            #print server reply
            server_reply = client_socket.recv(2048).decode()
            print(server_reply)
            if(server_reply != "End Session"):
                client_reply = input("Enter response: ")
                client_socket.send(client_reply.encode())
        except:
            print("Server closed connection. Ending Process.")
            exit()

if __name__ == "__main__":
    arg_copy = sys.argv.copy()
    server_address, server_port = validateArguments(arg_copy)
    if(server_port != -1 and server_address != -1):
        main(server_address, server_port)
    else:
        printable_args = " ".join(arg_copy)
        print("Please provide valid arguments. Arguments Passed: ", printable_args)
    exit()