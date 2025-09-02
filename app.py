import logging
import os
import threading

from dotenv import load_dotenv
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from langchain_handler import LangChainHandler

# Configuración de logging
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Inicializar LangChainHandler con variables de entorno
langchain_handler = LangChainHandler(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
    twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
    twilio_whatsapp_number=os.getenv("TWILIO_WHATSAPP_NUMBER"),
)


@app.route("/whatsapp", methods=["POST"])
def handle_whatsapp():
    """Endpoint para recibir mensajes de WhatsApp vía Twilio."""
    incoming_msg = request.form.get("Body", "").strip()
    user_number = request.form.get("From", "").strip()
    session_id = user_number

    response_event = threading.Event()
    response_msg = ""

    def callback(response):
        nonlocal response_msg
        response_msg = response
        response_event.set()

    try:
        langchain_handler.async_get_response(
            incoming_msg,
            session_id,
            user_number,
            callback,
        )
        # Esperar la respuesta con timeout
        response_event.wait(timeout=15)

        if not response_event.is_set():
            response_msg = (
                "Lo siento, el servidor está tardando en responder. "
                "Por favor, intenta de nuevo más tarde."
            )

        resp = MessagingResponse()
        resp.message(response_msg)
        return str(resp)
    except Exception as exc:
        _logger.error("Error in handle_whatsapp: %s", str(exc), exc_info=True)
        resp = MessagingResponse()
        resp.message("Lo siento, no pude procesar tu solicitud.")
        return str(resp)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=True,
    )

