````markdown
# WhatsApp AI Assistant

This project is a **Flask application** that integrates:
- **LangChain + OpenAI** for conversational AI.
- **Twilio WhatsApp API** for messaging.
- A simple session-based memory per user.

It is designed as a virtual assistant for a medical office, but can be adapted to other use cases.

---

## 1. Requirements

- Python **3.10+**
- An [OpenAI API key](https://platform.openai.com/)
- A [Twilio account](https://www.twilio.com/) with WhatsApp Sandbox enabled
- (Optional) [ngrok](https://ngrok.com/) for local testing with Twilio webhooks

---

## 2. Setup

Clone this repository and create a virtual environment:

```bash
git clone https://github.com/<your-username>/whatsapp-ai-assistant.git
cd whatsapp-ai-assistant

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
````

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Configuration

Copy the example environment file and add your keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_MODEL=gpt-4o-mini
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
PORT=5000
```

---

## 4. Running the Application

Start the Flask app:

```bash
python app.py
```

By default it runs on:
👉 [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 5. Testing with Twilio

If running locally, expose your app with **ngrok**:

```bash
ngrok http 5000
```

Copy the generated `https://xxxx.ngrok.io/whatsapp` URL and paste it in your Twilio Console under:
**Messaging → WhatsApp Sandbox → "WHEN A MESSAGE COMES IN".**

Now you can send a WhatsApp message to your Twilio sandbox number and get AI-powered responses.

---

## 6. Notes

* The app maintains a per-user chat history (session-based).
* Default response timeout is 15 seconds (Twilio limit).
* Do **not** commit `.env` or API keys to your repository.

---
