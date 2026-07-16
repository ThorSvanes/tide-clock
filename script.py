import requests
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=scopes
)

client = gspread.authorize(creds)
sheet = client.open("Tide Data").sheet1

def getHiloData():
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    daysAhead = 7
    today = datetime.now().strftime("%Y%m%d")
    weekAhead = (datetime.now() + timedelta(days=daysAhead)).strftime("%Y%m%d")
    params = {
        "product": "predictions",
        "application": "test_app",
        "begin_date": today,
        "end_date": weekAhead,
        "datum": "MLLW",
        "station": "TEC2801",
        "time_zone": "lst_ldt",
        "units": "english",
        "interval": "hilo",
        "format": "json"
    }
    data = requests.get(url, params=params).json()

    hiloData = []

    startTime = datetime.strptime(data["predictions"][0]["t"], "%Y-%m-%d %H:%M")

    for prediction in data["predictions"]:
        dt = datetime.strptime(prediction["t"], "%Y-%m-%d %H:%M")
        hours = (dt - startTime).total_seconds() / 3600
        height = float(prediction["v"])

        hiloData.append({
            "time": dt,
            "hours": hours,
            "height": height,
            "type": prediction["type"],
            "king": height >= 2.3
        })

    with open("tides.csv", "w") as file:
        file.write("time,high low,height,king tide\n")
        rows = [["Time", "High/Low", "Height", "King Tide"]]

        for prediction in data["predictions"]:
            tide_type = "High Tide" if prediction["type"] == "H" else "Low Tide"
            height = float(prediction['v'])
            kingTide = ""

            if height >= 2.3:
                kingTide = "King Tide"
            file.write(
                f"{prediction['t']},"
                f"{tide_type},"
                f"{prediction['v']},"
                f"{kingTide}\n"
            )
            rows.append([
                prediction["t"],
                tide_type,
                height,
                kingTide
            ])

            startTime = hiloData[0]["time"]
            dt = datetime.strptime(prediction["t"], "%Y-%m-%d %H:%M")

            for tide in hiloData:
                tide["hours"] = (tide["time"] - startTime).total_seconds() / 3600

        sheet.batch_clear(["A1:D15000"])
        sheet.update(rows, value_input_option="USER_ENTERED")
    return hiloData
