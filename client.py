import configparser
import logging
import socket
import json

# Pretty prints the commands and usages to client
def print_help():
    print("""\nusage:\n
    add <list item>      -Adds an items to the current list\n
    create <list>        -Creates a new list\n
    delete <list>        -Deletes a list\n
    help                 -Displays a message showing all available commands\n
    quit                 -Gracefully shuts down both server and client applications\n
    remove <list item>   -Removes an item from the current list\n
    show                 -Displays a numbered list of the list items""")

# Tokenize function that reads the first word of input
def tokenize(tokens):
    words = tokens.split()
    request = words[0]
    return request


def initialize_logger():
    # Open and Read config file
    config = configparser.ConfigParser()
    config.read("client.conf")

    # Get log info
    logFile = config["logger"]["logFile"]
    logLevel = config["logger"]["logLevel"]
    logFileMode = config["logger"]["logFileMode"]

    # Open log file
    logging.basicConfig(filename=logFile, level=logging.INFO,
                        filemode=logFileMode, format='%(asctime)s: %(levelname)s %(message)s')
    logging.info("Client application starting")
    logging.info("Logging to %s", logFile)
    logging.info("Log level set to %s", logLevel)
    logging.info("Log filemode set to %s", logFileMode)

    # Get the server IP address and port number
    serverHost = config["project2"]["serverHost"]
    serverPort = int(config["project2"]["serverPort"])
    return serverHost, serverPort


serverHost, serverPort = initialize_logger()

# Create a list of commands
commands = ['ADD', 'CREATE', 'DELETE', 'HELP', 'QUIT', 'REMOVE', 'SHOW']

# Create socket object and connect to the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((serverHost, serverPort))
print('Connecting to the server at ' + str(serverHost) + ':' + str(serverPort))


# Iterate while processing client info
while True:

    # Get user input
    userInput = input("Please enter a command ('help' for help'): ")
    request = tokenize(userInput).upper()
    logging.info("Command entered: %s", request)

    while request == "HELP":
        print_help()
        userInput = input("Please enter a command ('help' for help): ")
        request = tokenize(userInput).upper()
        logging.info("Command entered: %s", request)

    while request not in commands:
        print("Invalid command entered: ", request)
        logging.warning("Invalid command entered: %s", request)
        print_help()
        userInput = input("Please enter a command ('help' for help): ")
        request = tokenize(userInput).upper()
        logging.info("Command entered: %s", request)

    client_request = tokenize(userInput)
    client_parameter = userInput.replace(client_request, '', 1).strip()

    client_request = client_request.upper()
    while (client_request == "ADD" or client_request == "CREATE" or client_request == "DELETE" or client_request == "REMOVE") and (client_parameter == ""):
        logging.warning("Missing element in command: %s", client_request)
        print("Missing element in command: ", client_request.upper())
        print_help()
        userInput = input("Please enter a command ('help' for help): ")
        client_request = tokenize(userInput)
        logging.info("Command entered: %s", client_request)
        client_parameter = userInput.replace(client_request, '', 1).strip()

    # Need to check if command format is valid
    client_request = client_request.upper()

    # Create client request
    request = {"request": client_request, "parameter": client_parameter}
    request = json.dumps(request)
    logging.info("Sending client request: %s", request)
    s.send(bytes(request, encoding='utf-8'))

    # Get server response
    data = s.recv(1024)
    response = data.decode('utf-8')

    # Check server response for quit
    response_data = json.loads(response)
    logging.info("Server response received %s", response_data)
    client_request = response_data["request"]

    if response_data["request"] == "QUIT":
        break
    else:
        if (response_data["request"] == "WARNING" or response_data["request"] == "ERROR"):
            print("\nServer " + response_data["request"] +
                  ": " + response_data["parameter"] + "\n")
            logging.warning(
                "Server %s: %s", response_data["request"], response_data["parameter"])
        else:
            print("\n" + response_data["parameter"] + "\n")


# Close the socket connection
s.close()
print("Closing socket")
logging.info("Closing socket")

# Print shutting down to console and logger
print("Shutting down...\n")
logging.info("Shutting down...")
