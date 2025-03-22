import requests

# Trello API credentials (Replace these with your actual values)
API_KEY = '3dad77ed287d634221c484a9d8474459'
TOKEN = 'ATTA0222485c5c1433102dbc2dd23f22835727d0da23eb649c9c75a1e82f7c6fe1dfFC1D0FC8'
BOARD_ID = 'rhDqY0vP'
LIST_NAME = 'To Do'

def get_list_id():
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists?key={API_KEY}&token={TOKEN}"
    
    response = requests.get(url)
    if response.status_code == 200:
        lists = response.json()
        for lst in lists:
            if lst['name'].lower() == LIST_NAME.lower():
                return lst['id']
        raise ValueError("List not found")
    else:
        raise Exception(f"Failed to fetch lists: {response.text}")

def create_trello_ticket(name, description):
    try:
        list_id = get_list_id()
        url = f"https://api.trello.com/1/cards"
        
        payload = {
            'key': API_KEY,
            'token': TOKEN,
            'idList': list_id,
            'name': name,
            'desc': description
        }
        
        response = requests.post(url, params=payload)
        
        if response.status_code == 200:
            return response.json(), "Ticket created successfully!"
        else:
            return None, f"Failed to create ticket: {response.text}"
    except Exception as e:
        return None, str(e)
