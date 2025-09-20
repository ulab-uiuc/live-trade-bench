import json
import os
import threading

visit_count = 0
counter_lock = threading.Lock()

COUNTER_DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "counter_data.json"
)


def load_counter_data():
    global visit_count

    if os.path.exists(COUNTER_DATA_FILE):
        try:
            with open(COUNTER_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                visit_count = data.get("visit_count", 0)
        except Exception as e:
            print(f"Error loading counter data: {e}")
            visit_count = 0
    else:
        visit_count = 0


def save_counter_data():
    try:
        data = {"visit_count": visit_count}
        with open(COUNTER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving counter data: {e}")
        pass


def increment_visit_count():
    global visit_count

    with counter_lock:
        visit_count += 1
        save_counter_data()
        return visit_count


def get_visit_count():
    return visit_count


load_counter_data()
