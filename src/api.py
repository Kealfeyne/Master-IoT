import requests
from db import get_unread_messages_count


def send_count(localhost, port):
    unread_messages_count = get_unread_messages_count()

    if unread_messages_count == 0:
        requests.get(f"http://{localhost}:{port}/all_off")
        requests.get(f"http://{localhost}:{port}/led_notify")
        requests.get(f"http://{localhost}:{port}/ringhton")
    elif unread_messages_count > 0 and unread_messages_count < 6:
        requests.get(f"http://{localhost}:{port}/all_off")
        requests.get(f"http://{localhost}:{port}/green_on")
    elif unread_messages_count >= 6:
        requests.get(f"http://{localhost}:{port}/all_off")
        requests.get(f"http://{localhost}:{port}/yellow_on")
    elif unread_messages_count >= 10:
        requests.get(f"http://{localhost}:{port}/all_off")
        requests.get(f"http://{localhost}:{port}/red_on")
    # print(response.json())

def send_notification(localhost, port):
    requests.get(f"http://{localhost}:{port}/sound_notification")
