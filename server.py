'''
Author: Aakash Subedi
Date: 12/8/2023
'''

import sys
import socket
import random
from dataclasses import dataclass

#create global variables for the various suits
SPADE = 0
CLOVER = 1
HEART = 2
DIAMOND = 3
SUITS = [SPADE, CLOVER, HEART, DIAMOND]
SUIT_STRING = ["SPADE", "CLOVER", "HEART", "DIAMOND"]

#create global variables for game states
STATE_PLAY_HAND = 0
STATE_ENTER_BET = 1
STATE_HIT_DOUBLE_STAND = 2
STATE_DEAD = 3

@dataclass
class Card:
    suit: int
    number: int

@dataclass
class GameState:
    deck: list
    dealer_cards: list
    player_cards: list
    player_doubled: bool = False
    state: int = STATE_PLAY_HAND

#validates arguments passed into server.py
#if they are valid, return a server port that 
def validateArguments(arguments):
    #only expecting "python server.py {port number}", which has 2 arguments passed
    #returns negative number to indicate this is an invalid call to server.py
    if len(arguments) > 2:
        return -1
    
    #expecting to recieve a port number to start the program with.
    #if there is only the argument for "server.py", we also return negative number
    if len(arguments) == 1:
        return -1
    
    potential_port = arguments[1]
    try:
        potential_port_int = int(potential_port)
        #if port is not within
        if 1024 <= potential_port_int <= 65535:
            return potential_port_int
        else:
            return -1
    except:
        return -1

#validates client response so it isnt gibberish
def validateClientResponse(client_response):
    #create list of all strings within client_response
    response_list = client_response.split()
    
    #if there are more than one elements in the client's response, it is invalid
    if len(response_list) > 1:
        return "INVALID"
    
    #try to see if the element inside the client's response is an integer >= 0
    try:
        client_val = int(response_list[0])

        if client_val >= 0:
            return response_list[0]
        else:
            return "INVALID"
    except:
        return "INVALID"
    
#return passed_card in format "CARDNUM of CARDSUIT"
def cardToString(passed_card):
    passed_value = ""
    passed_suit = ""
    passed_suit = SUIT_STRING[passed_card.suit] + "S"
    if passed_card.number == 1:
        passed_value = "ACE"
    elif passed_card.number == 11:
        passed_value = "JACK"
    elif passed_card.number == 12:
        passed_value = "QUEEN"
    elif passed_card.number == 13:
        passed_value = "KING"
    else:
        passed_value = str(passed_card.number)

    return f"{passed_value} of {passed_suit}"

#return readable version of an entire hand
def handString(hand):
    hand_str = ""
    for card in hand:
        hand_str += cardToString(card) + "\n"
    hand_str += "\n"
    return hand_str

#return dealer's shown card and players full hand
def bothHandString(dealer_cards, player_cards):
    hands_string = "\nDealer shows: \n"
    hands_string += cardToString(dealer_cards[0]) + "\n"

    hands_string += "\nYou show: \n"
    for player_card in player_cards:
        hands_string += cardToString(player_card) + "\n"

    return hands_string

#return the integer value of the value of a hand, taking into account hard/soft hands
def handVal(passed_hand):
    hand_sum = 0
    num_aces = 0

    # sum cards in passed_hand, ace = 11 (1 if hard hand), face card = 10
    for card in passed_hand:
        if card.number == 1:  # Ace
            hand_sum += 11
            num_aces += 1
        elif card.number > 10:  # Face cards
            hand_sum += 10
        else:
            hand_sum += card.number

    # if players have have soft hand but it goes above 21, the aces count as 1
    while hand_sum > 21 and num_aces > 0:
        hand_sum -= 10
        num_aces -= 1

    return hand_sum

#takes in client response, and the state of the game
# STATE_PLAY_HAND -> ask user if they want to play hand, enter "enter_bet" state
# STATE_ENTER_BET -> ask user for their bet, enter "hit_double_stand" state
# STATE_HIT_DOUBLE_STAND -> ask user for their action, either stay in this statee or go to "play_hand" state depending on card values
# STATE_DEAD = 3 -> game is over, do nothing and program will terminate in driving loop
def runGame(response, gamestate):
    if(gamestate.state == STATE_PLAY_HAND):
        #add in an visual to help differentiate games
        server_reply = ""
        #if player wants to play a hand
        if response == "1":
            server_reply += "Enter bet"
            gamestate.state = STATE_ENTER_BET
        #if player doesnt want to play a hand
        elif response == "2":
            server_reply += "End Session"
            gamestate.state = STATE_DEAD
        #if player replied with invalid string
        else:
            server_reply += "Please provide a valid response.\n1) Play a hand\n2) Exit"

        return server_reply
    elif(gamestate.state == STATE_ENTER_BET):
        #if player replied with invalid string
        if response == "INVALID":
            server_reply = "Please provide a valid response.\nEnter bet"
            return server_reply
        #if player wants to see a hand  without the required bu, turn them down. We have to turn a profit in this establishment.
        elif response in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            server_reply = "Our table minimum is $10.\n1) Play a hand\n2) Exit)"
            gamestate.state = STATE_PLAY_HAND
            return server_reply
        else:
            if(len(gamestate.deck) <= 3):
                server_reply = "We ran out of cards!! Shuffling in a new deck, give us a moment.\n"
                addNewDeck(gamestate)

            player_cards = random.sample(gamestate.deck, 2)
            new_deck = [card for card in gamestate.deck if card not in player_cards]
            dealer_cards = random.sample(new_deck, 2)
            new_deck = [card for card in new_deck if card not in dealer_cards]

            gamestate.deck = new_deck
            gamestate.player_cards = player_cards
            gamestate.dealer_cards = dealer_cards
            
            #tell player what they have
            server_reply = bothHandString(dealer_cards, player_cards)
            

            #handle if player (and dealer) have blackjack
            player_hand_val = handVal(gamestate.player_cards)
            if(player_hand_val == 21):
                server_reply += "You got a natural 21!\n"
                dealer_hand_val = handVal(gamestate.dealer_cards)
                if(dealer_hand_val == 21):
                    server_reply += "Unfortunately, the dealer got one too...\n"
                    server_reply += "YOU LOSE!\n"
                    server_reply += "----------------------\n"
                    #reset game
                    server_reply += "\n1) Play a hand\n2) Exit"
                    gamestate.player_cards = []
                    gamestate.dealer_cards = []
                    gamestate.state = STATE_PLAY_HAND
                    return server_reply
                server_reply += "YOU WIN!\n"
                server_reply += "----------------------\n"
                gamestate.player_cards = []
                gamestate.dealer_cards = []
                gamestate.state = STATE_PLAY_HAND
                server_reply += "\n1) Play a hand\n2) Exit"
                return server_reply
            
            #if player doesnt have blackjack, continue game
            server_reply += f"Your hand value: {player_hand_val}\n"
            server_reply += "1) Hit\n2) Stand\n3) Double down\n"

            gamestate.state = STATE_HIT_DOUBLE_STAND
            return server_reply
    elif(gamestate.state == STATE_HIT_DOUBLE_STAND):
        server_reply = "\n"
        if response == "1":
            server_reply = bothHandString(gamestate.dealer_cards, gamestate.player_cards)

            if(len(gamestate.deck) <= 0):
                server_reply += "We ran out of cards!! Shuffling in a new deck, give us a moment.\n"
                addNewDeck(gamestate)

            drawn_card = random.choice(gamestate.deck)
            gamestate.deck.remove(drawn_card)

            gamestate.player_cards.append(drawn_card)
            server_reply += "You draw a "
            server_reply += cardToString(drawn_card) + "\n"

            player_hand_val = handVal(gamestate.player_cards)
            # standoffs result in a draw
            if(player_hand_val == 21):
                server_reply += "You are exactly at 21!\n"
                server_reply += "The dealer reveals their hand: \n"
                server_reply += handString(gamestate.dealer_cards) + "\n"
                
                while dealer_hand_val < 17:
                    if(len(gamestate.deck) <= 0):
                        server_reply += "We ran out of cards!! Shuffling in a new deck, give us a moment.\n"
                        addNewDeck(gamestate)
                    drawn_card = random.choice(gamestate.deck)
                    gamestate.deck.remove(drawn_card)
                    gamestate.dealer_cards.append(drawn_card)
                    dealer_hand_val = handVal(gamestate.dealer_cards)
                    server_reply += "The dealer drew a " + cardToString(drawn_card) + "\n"
    
                server_reply += "The dealers final hand is: \n" + handString(gamestate.dealer_cards)
                server_reply += f"Dealer hand value is {dealer_hand_val}\n"

                if dealer_hand_val == 21:
                    server_reply += "Dealer also has 21\nNO ONE WINS!\n"
                    server_reply += "----------------------\n"
                    server_reply += "\n1) Play a hand\n2) Exit"
                elif dealer_hand_val < player_hand_val:
                    server_reply += "You have a better hand than the dealer\nYOU WIN!\n"
                    server_reply += "----------------------\n"
                    server_reply += "\n1) Play a hand\n2) Exit"
                else:
                    server_reply += "The dealer drawing resulted in a bust.\nYOU WIN!\n"
                    server_reply += "----------------------\n"
                    server_reply += "\n1) Play a hand\n2) Exit"
                gamestate.player_cards = []
                gamestate.dealer_cards = []
                gamestate.state = STATE_PLAY_HAND
            # if player busts
            # reveal both hands, player loses, state -> play_hand
            elif(player_hand_val > 21):
                server_reply += "Drawing resulted in a bust\n"
                server_reply += "YOU LOSE!\n"
                server_reply += "----------------------\n"
                server_reply += "\n1) Play a hand\n2) Exit"
                gamestate.player_cards = []
                gamestate.dealer_cards = []
                gamestate.state = STATE_PLAY_HAND
            else:
                server_reply += f"Your hand value: {player_hand_val}\n"
                server_reply += "1) Hit\n2) Stand\n3) Double down\n"
                #ask to hit double stand      
        elif response == "2":
            server_reply += "The dealer reveals their hand: \n"
            server_reply += handString(gamestate.dealer_cards) + "\n"
            dealer_hand_val = handVal(gamestate.dealer_cards)
            while dealer_hand_val < 17:
                if(len(gamestate.deck) <= 0):
                    server_reply += "We ran out of cards!! Shuffling in a new deck, give us a moment.\n"
                    addNewDeck(gamestate)
                drawn_card = random.choice(gamestate.deck)
                gamestate.deck.remove(drawn_card)
                gamestate.dealer_cards.append(drawn_card)
                dealer_hand_val = handVal(gamestate.dealer_cards)
                server_reply += "The dealer drew a " + cardToString(drawn_card) + "\n"
            
            server_reply += "The dealers final hand is: \n" + handString(gamestate.dealer_cards) + "\n"
            server_reply += f"Dealer hand value is {dealer_hand_val}\n"

            player_hand_val = handVal(gamestate.player_cards)

            if dealer_hand_val > 21:
                #dealer loses, player wins
                server_reply += "The dealer drawing resulted in a bust.\nYOU WIN!\n"
                server_reply += "----------------------\n"
            else:
                if dealer_hand_val < player_hand_val:
                    #dealer loses
                    server_reply += "You have a better hand than the dealer\nYOU WIN!\n"
                    server_reply += "----------------------\n"
                elif dealer_hand_val > player_hand_val:
                    server_reply += "The dealer had a better hand than you\nYOU LOSE\n"
                    server_reply += "----------------------\n"
                    #the dealer wins, the player loses
                else:
                    #equal hand values result in a draw
                    server_reply += "Dealer also has 21\nNO ONE WINS!\n"
                    server_reply += "----------------------\n"
            server_reply += "\n1) Play a hand\n2) Exit"
            gamestate.player_cards = []
            gamestate.dealer_cards = []
            gamestate.state = STATE_PLAY_HAND
        elif response == "3":
            server_reply = bothHandString(gamestate.dealer_cards, gamestate.player_cards)
            if(len(gamestate.deck) <= 0):
                server_reply += "We ran out of cards!! Shuffling in a new deck, give us a moment.\n"
                addNewDeck(gamestate)

            drawn_card = random.choice(gamestate.deck)
            gamestate.deck.remove(drawn_card)

            gamestate.player_cards.append(drawn_card)
            server_reply += "You draw a "
            server_reply += cardToString(drawn_card) + "\n"
            
            player_hand_val = handVal(gamestate.player_cards)
            if(player_hand_val > 21):
                server_reply += "Drawing resulted in a bust\n"
                server_reply += "YOU LOSE!\n"
                server_reply += "----------------------\n"
                gamestate.player_cards = []
                gamestate.dealer_cards = []
                gamestate.state = STATE_PLAY_HAND
            else:
                server_reply += "The dealer reveals their hand: \n"
                server_reply += handString(gamestate.dealer_cards) + "\n"
                dealer_hand_val = handVal(gamestate.dealer_cards)
                while dealer_hand_val < 17:
                    if(len(gamestate.deck) <= 0):
                        server_reply += "We ran out of cards!! Shuffling in a new deck, give us a moment.\n"
                        addNewDeck(gamestate)
                    drawn_card = random.choice(gamestate.deck)
                    gamestate.deck.remove(drawn_card)
                    gamestate.dealer_cards.append(drawn_card)
                    dealer_hand_val = handVal(gamestate.dealer_cards)
                    server_reply += "The dealer drew a " + cardToString(drawn_card) + "\n"
                
                server_reply += "The dealers final hand is: \n" + handString(gamestate.dealer_cards) + "\n"
                server_reply += f"Dealer hand value is {dealer_hand_val}\n"
                if dealer_hand_val > 21:
                    #dealer loses, player wins
                    server_reply += "The dealer drawing resulted in a bust.\nYOU WIN!\n"
                    server_reply += "----------------------\n"
                else:
                    if dealer_hand_val < player_hand_val:
                        #dealer loses
                        server_reply += "You have a better hand than the dealer\nYOU WIN!\n"
                        server_reply += "----------------------\n"
                        
                    elif dealer_hand_val > player_hand_val:
                        server_reply += "The dealer had a better hand than you\nYOU LOSE\n"
                        server_reply += "----------------------\n"
                        #if dealers hand is equal to or greater than players hand while dealer hand is not over 21,
                        #the dealer wins, the player loses
                    else:
                        #equal hand values
                        server_reply += "Dealer also has 21\nNO ONE WINS!\n"
                        server_reply += "----------------------\n"
                        
            server_reply += "\n1) Play a hand\n2) Exit"
            gamestate.player_cards = []
            gamestate.dealer_cards = []
            gamestate.state = STATE_PLAY_HAND
        else:
            player_hand_val = handVal(gamestate.player_cards)
            server_reply += "Please provide a valid response.\n"
            server_reply += f"Your hand value: {player_hand_val}\n"
            server_reply += "1) Hit\n2) Stand\n3) Double down\n"
        return server_reply

#add 52 cards, 13 of each suit, to dealer's deck
def addNewDeck(gamestate):
    for cur_suit in SUITS:
        #card_val in [1,2,3,4,5,6,7,8,9,10,11,12,13] -> all card values
        for card_val in range(1,14):
            gamestate.deck.append(Card(suit=cur_suit, number=card_val))

    shuffleDeck(gamestate)

#shuffle the deck (including cards that are already present before the new deck was added)
def shuffleDeck(gamestate):
    random.shuffle(gamestate.deck)

#this is code I used while testing. I believe everything works, but in case it breaks, I will leave it here.
# def testGame():
#     testGame = GameState(deck = [],
#     dealer_cards = [],
#     player_cards = [],
#     player_doubled = False)
#     print("1) Play a hand\n2) Exit")
#     while(testGame.state != STATE_DEAD):
#         response = input("GIVE VALUE HERE: ")
#         response = validateClientResponse(response)
#         reply = runGame(response, testGame)
#         print(reply)

#main loop, drives the blackjack game and communicates to client
def main(port):
    #create socket
    localhost = "127.0.0.1"
    #create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #bind server to port
    server_socket.bind((localhost, port))
    
    #set timeout for socket of 30 seconds
    server_socket.settimeout(30)

    #listen for only one connection, from client.py
    server_socket.listen(1) 

    #get client socket
    client_socket, client_address = server_socket.accept()
    

    #run game(s)
    
    #play_game indicates whether a new game wants to be started, starts true
    client_response = ""

    #send initial message for client to respond to
    initial_message = "1) Play a hand\n2) Exit"
    client_socket.send("1) Play a hand\n2) Exit\n".encode())

    gamestate = GameState(deck = [],
                            dealer_cards = [],
                            player_cards = [],
                            player_doubled = False)
    addNewDeck(gamestate)
    try:
        #driving loop, this is what is "running blackjack" and talking to client
        while(gamestate.state != STATE_DEAD):
            client_response = client_socket.recv(2048).decode() #recieve 2048 bytes and decode to turn into string
            validated_client_response = validateClientResponse(client_response)
            message_to_client = runGame(validated_client_response, gamestate)
            client_socket.send(message_to_client.encode())
    except KeyboardInterrupt:
        print("KeyboardInterrupt Occured!")
    except:
        print("Client closed connection. Ending Process.")
        #ensure client socket is closed
        try:
            client_socket.close()
        except:
            print("Error closing client Socket")

    
    #close client socket
    client_socket.close()

    #close server socket
    server_socket.close()
    
    return


if __name__ == "__main__":
    arg_copy = sys.argv.copy()
    server_port = validateArguments(arg_copy)
    if(server_port != -1):
        main(server_port)
    else:
        printable_args = " ".join(arg_copy)
        print("Please provide valid arguments. Arguments Passed: ", printable_args)
    exit()