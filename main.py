from flask import Flask, request
import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}/"

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")
        if text == "/start":
            send_message(chat_id, "Привет! Я твой ассистент 🚀")
        elif text == "/challenge":
            send_message(chat_id, "Сегодня челлендж: пройти 15000 шагов! 🏃‍♂️")
    return "ok"

def send_message(chat_id, text):
    requests.post(URL + "sendMessage", json={"chat_id": chat_id, "text": text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
