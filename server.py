import configparser
import logging
import socket
import json


def print_help():
    print("""            Usage\n
    add <list item>      -Adds an items to the current list\n
    create <list>        -Creates a new list\n
    delete <list>        -Deletes a list\n
    help                 -Displays a message showing all available commands\n
    quit                 -Gracefully shuts down both server and client applications\n
    remove <list item>   -Removes an item from the current list\n
    show                 -Displays a numbered list of the list items""")


def action(command, item="", l1=[], list_exists=False, list_name=""):
    # Add an element to the list if it exists
    serverResponse = ""
    serverResponseType = ""
    if command == "ADD":
        if list_exists and item not in l1:
            l1.append(item)
            list_exists = True
            serverResponse = item + " added to " + list_name + "!"
            serverResponseType = "ADD"
            logging.info("%s added to the list", item)
        elif not list_exists:
            serverResponse = "No list exists!"
            serverResponseType = "WARNING"
            logging.warning("No list exists")
        else:
            serverResponse = item + " is already in the list!"
            serverResponseType = "WARNING"
            logging.warning("%s is already in the list")
    # Create a list if one does not already exist
    if command == "CREATE":
        if not list_exists:
            l1 = []
            list_exists = True
            list_name = item
            serverResponse = "Created list " + list_name
            serverResponseType = "CREATE"
            logging.debug("%s created")
        else:
            serverResponse = "List " + list_name + " already exists!"
            serverResponseType = "WARNING"
            logging.warning("List already exists")

    # Delete the list if it exists
    if command == "DELETE":
        if list_exists and list_name == item:
            l1 = []
            list_exists = False
            serverResponse = list_name + " deleted!"
            list_name = ""
            serverResponseType = "DELETE"
            logging.debug("%s deleted")

        elif list_name != item:
            serverResponse = "List " + item + " does not exist!"
            serverResponseType = "WARNING"
            logging.warning("%s does not exist", list_name)
        else:
            serverResponse = "There is no list to delete!"
            serverResponseType = "WARNING"
            logging.warning("There is no list to delete")

    # Remove an element from the list if it exists
    if command == "REMOVE":
        if list_exists:
            if l1.count(item) == 0:
                serverResponse = item + " is not in the list!"
                serverResponseType = "WARNING"
                logging.warning("%s is not in the list", item)
            else:
                serverResponse = "Item " + item + " removed!"
                l1.remove(item)
                list_exists = True
                serverResponseType = "REMOVE"
                logging.debug("%s removed from list", item)
        else:
            serverResponse = "No list to remove item from!"
            serverResponseType = "ERROR"
            logging.warning("No list to remove item from")

    # Show all the elements of the list
    if command == "SHOW":
        if not list_exists:
            serverResponse = "No list exists!"
            serverResponseType = "WARNING"
            logging.warning("No list exists")
        elif list_exists and len(l1) == 0:
            serverResponse = "The list is empty"
            serverResponseType = "WARNING"
            logging.warning("The list is empty")
        else:
            for i, item in enumerate(l1):
                logging.debug("List items gathered")
                # print(i + 1, ":", item)
                serverResponse = serverResponse + \
                    "\n" + str(i + 1) + ": " + item
                list_exists = True

    return l1, list_exists, list_name, serverResponse, serverResponseType


# Read the configuration file
config = configparser.ConfigParser()
config.read("server.conf")

# Get the name of the log file
logFile = config["logger"]["logFile"]
logLevel = config["logger"]["logLevel"]
logFileMode = config["logger"]["logFileMode"]

# Initialize the logger
logging.basicConfig(filename=logFile, level=logging.INFO, filemode=logFileMode,
                    format='%(asctime)s: %(levelname)s %(message)s')

logging.info("Server application starting")
print("Server application starting...\nAwaiting client connection...")
logging.debug("Logging to %s", logFile)
logging.debug("Log level set to %s", logLevel)
logging.debug("Log filemode set to %s", logFileMode)

# Get the server IP address and port number
serverHost = config["project2"]["serverHost"]
serverPort = int(config["project2"]["serverPort"])
logging.debug("Server IP is %s", serverHost)
logging.debug("Server Port is %s", serverPort)

# Open the socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
logging.info("Opened TCP socket")

# Bind and listen for connections
s.bind((serverHost, serverPort))
s.listen(1)
logging.info("Listening for client connections")

# Accept the request
conn, address = s.accept()

print("Connection to client successful\nAwaiting client request...")
logging.info("Connection to client successful")
logging.info("Awaiting client request...")

# Iterate while client sending requests
l1 = []
list_exists = False
list_name = ""
list_file = open("list_contents.txt", "r")
line = list_file.readline().split(",")
j = 2
if line[0] == "T":
    list_exists = True
    list_name = line[1]
    while j < len(line):
        l1.append(line[j])
        j += 1

i = 0
serverResponse = ""
serverReponseType = ""
while True:
    data = conn.recv(1024).decode('utf-8')
    client_data = json.loads(data)

    # Ensure client request prints one time
    if i != 1:
        # print("Client request received: ", json.dumps(client_data))
        logging.info("Client request received: %s", json.dumps(client_data))
    i = i + 1

    logging.info("Processing client request %s", client_data["request"])

    # Check to see if client request contains quit
    if client_data["request"] == 'QUIT':
        # Fill in null parameter and send
        client_data["parameter"] = "NULL"
        client_data = json.dumps(client_data)
        conn.send(bytes(client_data, encoding="utf-8"))
        break
    else:
        if client_data["request"] == "CREATE" and not list_exists:
            list_name = client_data["parameter"]

        l1, list_exists, list_name, serverResponse, serverResponseType = action(
            client_data["request"], client_data["parameter"], l1, list_exists, list_name)

        client_data["request"] = serverResponseType
        client_data["parameter"] = serverResponse
        client_data = json.dumps(client_data)
        conn.send(bytes(client_data, encoding="utf-8"))

    # Ensure response prints one time
    # if i != 1:
        # print("Sending server response: ", client_data)
    logging.info("Sending server response: %s", client_data)

print("Server shutting down...")
logging.info("Server shutting down")

# If the list still exists keep the contents
list_file = open("list_contents.txt", "w")
if list_exists:
    list_file.write("T")
    list_file.write("," + list_name)

    for item in l1:
        list_file.write("," + item)

    print("Storing list contents")
else:
    list_file.write("F")

list_file.close()

conn.close()
