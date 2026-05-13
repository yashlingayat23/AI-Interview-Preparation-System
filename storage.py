import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "interview_sessions.json"



def initialize_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        write_data({"sessions": []})



def read_data() -> dict:
    initialize_storage()
    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    data.setdefault("sessions", [])
    return data



def write_data(data: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)



def load_sessions() -> list[dict]:
    return read_data()["sessions"]



def save_session(session: dict) -> None:
    data = read_data()
    data["sessions"].append(session)
    write_data(data)
