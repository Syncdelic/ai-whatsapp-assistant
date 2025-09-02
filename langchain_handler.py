import logging
from datetime import datetime
from threading import Thread

import pytz
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from twilio.rest import Client

_logger = logging.getLogger(__name__)


class LangChainHandler:
    def __init__(
        self,
        openai_api_key,
        twilio_account_sid,
        twilio_auth_token,
        twilio_whatsapp_number,
        model_name="gpt-4o-mini",
        temperature=0.8,
        max_tokens=350,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    ):
        # NOTE: In some recent LangChain versions the parameter is 'model' instead of
        # 'model_name'. Keep as-is if your current env works; otherwise swap to model=...
        # Ref: ChatPromptTemplate / ChatOpenAI docs. 
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )

        # === PURPOSE: Order Tracking & Returns Assistant (WhatsApp-friendly) ===
        # Highlights: intent detection + minimal data capture + concise confirmations.
        # Uses ChatPromptTemplate.from_messages per LangChain docs. 
        # See: ChatPromptTemplate / RunnableWithMessageHistory how-to.
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are an Order Support Assistant for a small e-commerce shop. "
                        "Your job is to detect the user's intent and complete ONE task:\n"
                        "1) Track an order, 2) Start a return, or 3) Answer basic product questions.\n\n"
                        "— If tracking: ask for order number and email/phone to verify. "
                        "— If return: ask for order number, item, reason (brief), and email/phone. "
                        "— If product: answer briefly; if specs/policies are missing, say you will "
                        "forward the question to a human.\n\n"
                        "Rules:\n"
                        "- Be concise and friendly.\n"
                        "- Ask only for the next required field; do not dump long lists.\n"
                        "- Confirm the captured fields back to the user.\n"
                        "- If the user switches intent mid-chat, confirm the new intent.\n"
                        "- Always include a short next step.\n"
                    ),
                ),
                (
                    "system",
                    (
                        "Current date/time: {datetime}. "
                        "Output language must match the user's input language."
                    ),
                ),
                # Conversation memory gets injected here by RunnableWithMessageHistory
                ("placeholder", "{chat_history}"),
                # User message
                ("human", "{input}"),
            ]
        )

        self.chain = self.prompt | self.llm | StrOutputParser()
        self.conversations = {}

        self.twilio_client = Client(twilio_account_sid, twilio_auth_token)
        self.twilio_whatsapp_number = twilio_whatsapp_number

    def get_response(self, user_input, session_id, user_number):
        if session_id not in self.conversations:
            history = InMemoryChatMessageHistory()
            self.conversations[session_id] = {
                "chain": RunnableWithMessageHistory(
                    self.chain,
                    # A simple per-session history provider.
                    # For multi-user apps, see LangChain message history guide.
                    # This keeps the WhatsApp number's state isolated.
                    lambda: history,
                    input_messages_key="input",
                    history_messages_key="chat_history",
                ),
                "history": history,
            }

        conversation = self.conversations[session_id]["chain"]
        guadalajara_tz = pytz.timezone("America/Mexico_City")
        current_datetime = datetime.now(guadalajara_tz).strftime("%Y-%m-%d %H:%M:%S")

        response = conversation.invoke(
            {
                "input": user_input,
                "datetime": current_datetime,
                "user_number": user_number,
            }
        )

        _logger.info(
            "LangChain response for %s: %s...",
            session_id,
            str(response)[:50],
        )
        return response

    def get_memory(self, session_id):
        if session_id in self.conversations:
            history = self.conversations[session_id]["history"]
            return history.messages
        return None

    def async_get_response(self, user_input, session_id, user_number, callback):
        def run():
            try:
                response = self.get_response(user_input, session_id, user_number)
                callback(response)
            except Exception as exc:
                _logger.error(
                    "Error in async_get_response: %s",
                    str(exc),
                    exc_info=True,
                )
                callback("Lo siento, no pude procesar tu solicitud.")

        t = Thread(target=run)
        t.start()

