import requests
from db import get_unread_messages_count


def send_count(localhost, port):
    unread_messages_count = get_unread_messages_count()

    if unread_messages_count == 0:
        requests.get(f"http://{localhost}:{port}/control/all_off")
        requests.get(f"http://{localhost}:{port}/control/led_notify")
        requests.get(f"http://{localhost}:{port}/control/ringhton")
    elif unread_messages_count > 0 and unread_messages_count < 6:
        requests.get(f"http://{localhost}:{port}/control/all_off")
        requests.get(f"http://{localhost}:{port}/control/green_on")
    elif unread_messages_count >= 6 and unread_messages_count < 10:
        requests.get(f"http://{localhost}:{port}/control/all_off")
        requests.get(f"http://{localhost}:{port}/control/yellow_on")
    elif unread_messages_count >= 10:
        requests.get(f"http://{localhost}:{port}/control/all_off")
        requests.get(f"http://{localhost}:{port}/control/red_on")
    # print(response.json())

def send_notification(localhost, port):
    requests.get(f"http://{localhost}:{port}/control/sound_notify")