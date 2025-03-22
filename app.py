import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import psycopg2

import os

# Database connection
def get_db_connection():
    try:
        connection = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        print("Database connected successfully!")
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


app = Flask(__name__)

# Trello Configuration
TRELLO_API_KEY = os.getenv('TRELLO_API_KEY')
TRELLO_TOKEN = os.getenv('TRELLO_TOKEN')
BOARD_ID = os.getenv('BOARD_ID')
LIST_ID = os.getenv('LIST_ID')

# In-memory state storage for users
user_state = {}

# Functions to get menus
def get_main_menu():
    return """
    Please select any one of the following options:
    
    1️⃣ **Pricing and Rate Information**
    2️⃣ **Lead Management & RFPs**
    3️⃣ **Reports**
    4️⃣ **Meeting Schedules**
    5️⃣ **Escalations and Support**
    6️⃣ **Others (Type 'Others')**
    
    *Select the option by typing the number next to the option.*
    """

def get_others_menu():
    return """
    ✍️ **For other inquiries, please specify your query, and our support team will assist you.**
    """

def create_trello_ticket(sender, message_body, escalation=False):
    # Fetch property name from the database
    clean_sender = sender.replace('whatsapp:', '').replace('+', '')  # Clean up the sender's number
    property_name = None
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT propertyName FROM users WHERE contactnumber = %s", (clean_sender,))
            user = cursor.fetchone()
            if user:
                property_name = user[0]
            else:
                print(f"No property found for user {sender}")
        except Exception as e:
            print(f"Error fetching property name: {e}")
        finally:
            cursor.close()
            conn.close()

    if not property_name:
        property_name = "Unknown Property"  # Fallback in case the property name is not found
    
    # Default label "P0" - Use the label ID for "P0" (you can find the label ID from the Trello board API or the UI)
    p0_label_id = '67ddbefcd6ea43e469645540'  # Replace with actual "P0" label ID
    
    # Add labels if this is an escalation
    
    url = f"https://api.trello.com/1/cards"
    query = {
        'key': TRELLO_API_KEY,
        'token': TRELLO_TOKEN,
        'idList': LIST_ID,
        'name': f"Support Ticket for {property_name}",  # Title is set to the property name
        'desc': message_body,
        'labels': [p0_label_id]  # Add labels parameter
    }
    
    response = requests.post(url, params=query)
    if response.status_code == 200:
        return "✅ Your ticket has been successfully created. Our support team will reach out to you soon."
    else:
        return f"⚠️ Failed to create ticket: {response.json()}"


@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    incoming_msg = request.values.get('Body', '').strip().lower()  # Get and clean incoming message
    sender = request.values.get('From', '')

    # Debug: print the incoming message to the console to check if it's being received correctly
    print(f"Incoming message from {sender}: '{incoming_msg}'")

    # Discard empty messages
    if not incoming_msg:
        response = MessagingResponse()
        message = response.message()
        message.body("⚠️ Please send a valid message.")
        return str(response)

    # Clean incoming number (remove 'whatsapp:' prefix and '+' sign)
    clean_sender = sender.replace('whatsapp:', '').replace('+', '')

    # Check if the user is authorized - with fixed connection handling
    authorized = False
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE contactnumber = %s", (clean_sender,))
            user = cursor.fetchone()
            
            if user:
                authorized = True
                print(f"User {clean_sender} authorized successfully")
            else:
                print(f"User {clean_sender} not found in database")
        except Exception as e:
            print(f"Database error: {e}")
        finally:
            # Always close the connection when done
            cursor.close()
            conn.close()
    
    if not authorized:
        response = MessagingResponse()
        message = response.message()
        message.body("⚠️ Your phone number is not registered. Please contact support.")
        return str(response)

    # Check if the incoming message is a greeting
    if incoming_msg in ['hi', 'hello', 'hey', 'greetings', 'hola']:  # Add more greetings here
        user_state[sender] = 'main_menu'
        response = MessagingResponse()
        message = response.message()

        # Send only the welcome message with the main menu, avoid duplication
        welcome_text = "👋 **Welcome to Atica Support!**\n🏢 *Atica - Your Trusted Partner in Business Management*\n" + get_main_menu()
        message.body(welcome_text)
        
        response_str = str(response)
        print(f"Sending response: {response_str}")
        return response_str

    # Continue with the rest of your menu handling code...
    state = user_state.get(sender, 'main_menu')
    response = MessagingResponse()
    message = response.message()

    if state == 'main_menu':
        if incoming_msg == '1':
            message.body("*📊 Pricing and Rate Information*\n\n1️⃣ Alter the rates of specific dates\n2️⃣ View pricing for next 30 days\n3️⃣ View pricing for event dates\n4️⃣ View discounts running on the property")
            user_state[sender] = 'pricing'
        elif incoming_msg == '2':
            message.body("*📑 Lead Management & RFPs*\n\n1️⃣ Submit a lead\n2️⃣ Change lead details\n3️⃣ View latest update on any lead")
            user_state[sender] = 'lead_management'
        elif incoming_msg == '3':
            message.body("*📈 Reports*\n\n1️⃣ View/Download STR Report\n2️⃣ View/Download OTA Recon Report\n3️⃣ View/Download Daily Snapshot Report\n4️⃣ View/Download Client Month End Report\n5️⃣ View/Download Reputation Report")
            user_state[sender] = 'reports'
        elif incoming_msg == '4':
            message.body("*📅 Meeting Schedules*\n\n1️⃣ View next meetings and joining info\n2️⃣ Schedule a meeting")
            user_state[sender] = 'meeting_schedule'
        elif incoming_msg == '5':
            message.body("*⚙️ Escalations and Support*\n\n1️⃣ Revenue Management\n2️⃣ Sales Management\n3️⃣ Account Management")
            user_state[sender] = 'escalation_support'
        elif incoming_msg == '6' or incoming_msg == 'others':
            user_state[sender] = 'others'
            message.body(get_others_menu())
        else:
            message.body(f"⚠️ Invalid choice.\n\n👋 **Welcome to Atica Support!**\n🏢 *Atica - Your Trusted Partner in Business Management*\n{get_main_menu()}")

    elif state == 'escalation_support':
        if incoming_msg == '1':
            user_state[sender] = 'revenue_management'
            message.body("*📊 Revenue Management*\n\n1️⃣ Low Booking ADR\n2️⃣ Pricing\n3️⃣ Performance Issue/Production")
        elif incoming_msg == '2':
            user_state[sender] = 'sales_management'
            message.body("*💼 Sales Management*\n\n1️⃣ Regarding Rooming List\n2️⃣ Regarding Credit Card\n3️⃣ Regarding Group Block\n4️⃣ Performance/Production Issue")
        elif incoming_msg == '3':
            user_state[sender] = 'account_management'
            message.body("*📅 Account Management*\n\n1️⃣ Payment Issues\n2️⃣ POC Issues\n3️⃣ Performance/Production Issues")
        else:
            message.body("⚠️ Invalid choice. Please select a valid category.")
        return str(response)

    # Revenue Management flow
    if state == 'revenue_management':
        if incoming_msg == '1':
            user_state[sender] = 'elaboration'
            message.body("⚠️ Please elaborate on the Low Booking ADR escalation. Provide details to help us understand the issue better.")
        elif incoming_msg == '2':
            user_state[sender] = 'elaboration'
            message.body("⚠️ Please elaborate on the Pricing escalation. Provide details to help us understand the issue better.")
        elif incoming_msg == '3':
            user_state[sender] = 'elaboration'
            message.body("⚠️ Please elaborate on the Performance Issue/Production escalation. Provide details to help us understand the issue better.")
        else:
            message.body("⚠️ Invalid choice. Please select a valid issue type.")
        return str(response)

    # Sales Management flow
    if state == 'sales_management':
        if incoming_msg == '1':
            user_state[sender] = 'elaboration'
            message.body("⚠️ Please elaborate on the Rooming List escalation. Provide details to help us understand the issue better.")
        elif incoming_msg == '2':
            user_state[sender] = 'elaboration'
            message.body("⚠️ Please elaborate on the Credit Card escalation. Provide details to help us understand the issue better.")
        elif incoming_msg == '3':
            user_state[sender] = 'elaboration'
            message.body("⚠️ Please elaborate on the Group Block escalation. Provide details to help us understand the issue better.")
        elif incoming_msg == '4':
            user_state[sender] = 'elaboration'
            message.body("⚠️ Please elaborate on the Performance/Production Issue escalation. Provide details to help us understand the issue better.")
        else:
            message.body("⚠️ Invalid choice. Please select a valid issue type.")
        return str(response)

    # Account Management flow
    if state == 'account_management':
        if incoming_msg == '1':
            user_state[sender] = 'elaboration'
            message.body("⚠️ Please elaborate on the Payment Issue escalation. Provide details to help us understand the issue better.")
        elif incoming_msg == '2':
            user_state[sender] = 'elaboration'
            message.body("⚠️ Please elaborate on the POC Issue escalation. Provide details to help us understand the issue better.")
        elif incoming_msg == '3':
            user_state[sender] = 'elaboration'
            message.body("⚠️ Please elaborate on the Performance/Production Issue escalation. Provide details to help us understand the issue better.")
        else:
            message.body("⚠️ Invalid choice. Please select a valid issue type.")
        return str(response)

    # Elaboration flow
    if state == 'elaboration':
        ticket_response = create_trello_ticket(sender, incoming_msg, escalation='true')
        message.body(ticket_response)
        user_state[sender] = 'main_menu'

    elif state == 'others':
        if incoming_msg.strip():  # Check if the message is not empty
            ticket_response = create_trello_ticket(sender, incoming_msg)
            message.body(ticket_response)
        else:
            message.body("⚠️ Please provide more details for your inquiry.")
        user_state[sender] = 'main_menu'

    return str(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

