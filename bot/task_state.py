import os
import json
from datetime import datetime
from pytz import timezone

STATE_FILE = "task_state.json"
MSK = timezone("Europe/Moscow")


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def update_last_run(task_name):
    state = load_state()
    now_str = datetime.now(MSK).isoformat()
    state[task_name] = now_str
    save_state(state)


def was_task_already_run(task_name, after_dt):
    state = load_state()
    last_run = state.get(task_name)
    if not last_run:
        return False
    try:
        last_run_dt = datetime.fromisoformat(last_run)
        return last_run_dt >= after_dt
    except Exception:
        return False


def clear_state():
    """Safely deletes the state file."""
    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            print("Файл состояния планировщика очищен.")
    except Exception as e:
        print(f"Ошибка при очистке файла состояния: {e}")