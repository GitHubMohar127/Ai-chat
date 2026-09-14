import os
import json

from google import genai
from google.genai import types


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_ai_client():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    return genai.Client(
        api_key=api_key
    )


# ============================================================
# GEMINI MESSAGE ANALYSIS
# ============================================================

def analyze_user_message(message):

    if not isinstance(message, str):
        message = ""

    message = message.strip()

    if not message:

        return {
            "intent": "invalid",
            "search_query": "",
            "confidence": 1.0,
            "reason": "Empty message."
        }


    # ========================================================
    # CREATE GEMINI CLIENT
    # ========================================================

    client = get_ai_client()


    if client is None:

        return {
            "intent": "error",
            "search_query": "",
            "confidence": 0.0,
            "reason": (
                "GEMINI_API_KEY was not found."
            )
        }


    # ========================================================
    # SYSTEM INSTRUCTION
    # ========================================================

    prompt = f"""
You are the AI message understanding system for a
Hindcon Product Assistant.

The application is used ONLY for finding Hindcon products
and their TDS/MSDS document links.

Your job is to UNDERSTAND and CLASSIFY the user's message.

You must NOT answer the user's question.

You must NOT provide technical TDS information.

You must NOT invent any product information.

Choose exactly ONE of these intents:

------------------------------------------------------------
INTENT 1: greeting
------------------------------------------------------------

Use "greeting" when the user is greeting the assistant.

Examples:

hi
hello
hey
hii
hiii
helo
good morning
good afternoon
good evening
good night


------------------------------------------------------------
INTENT 2: product_search
------------------------------------------------------------

Use "product_search" when the user wants to find a Hindcon
product or wants its TDS/MSDS document.

Examples:

Hind
hind plast
Hind Sol SR
Hind Fix TA
Hind Crystel Seal
show Hind
show Hind products
show me Hind Sol SR
find Hind Fix TA
I want Hind Crystel Seal
Give me the TDS of Hind Crystel Seal
Give me the MSDS of Hind Fix TA
I need the TDS of Hind Sol SR
hind crystel sel


IMPORTANT:

For product_search, extract ONLY the product name or
product search phrase.

Example:

User:
Give me the TDS of Hind Crystel Seal

search_query:
Hind Crystel Seal


User:
I need the MSDS of Hind Fix TA

search_query:
Hind Fix TA


User:
show me Hind Sol SR

search_query:
Hind Sol SR


User:
hind plast

search_query:
hind plast


User:
hind

search_query:
hind


User:
hind crystel sel

search_query:
hind crystel sel


------------------------------------------------------------
INTENT 3: casual
------------------------------------------------------------

Use "casual" for normal conversation that is not a
product search.

Examples:

how are you
how are ypu
how are u
how r you
thanks
thank you
bye
goodbye
who are you
what are you
what are you doing
nice


------------------------------------------------------------
INTENT 4: invalid
------------------------------------------------------------

Use "invalid" when the user asks something unrelated to
Hindcon products or TDS/MSDS.

Examples:

what is the date of today?
what is today's date?
what is the weather today?
what is the weather?
what time is it?
tell me a joke
solve 2 + 2
solve this math problem
who won the cricket match?
who won the football match?
what is the capital of India?
write python code
write a program
who is the prime minister?


IMPORTANT RULES:

- Date questions = invalid
- Weather questions = invalid
- Time questions = invalid
- Cricket questions = invalid
- Football questions = invalid
- Mathematics questions = invalid
- Programming questions = invalid
- General knowledge questions = invalid
- Jokes = invalid

Only Hindcon product/TDS/MSDS requests are
product_search.


------------------------------------------------------------
VERY IMPORTANT
------------------------------------------------------------

If the user writes only a word or short phrase that looks
like a Hindcon product search, classify it as product_search.

Examples:

Hind
Hind plast
Hind sol
Hind fix
Hind seal
Hind plug


------------------------------------------------------------
OUTPUT
------------------------------------------------------------

Return ONLY JSON.

The JSON must have exactly these fields:

intent
search_query
confidence
reason

Example:

{{
    "intent": "product_search",
    "search_query": "Hind Crystel Seal",
    "confidence": 0.98,
    "reason": "The user wants to find a Hindcon product."
}}

User message:

{message}
"""


    # ========================================================
    # CALL GEMINI
    # ========================================================

    try:

        response = client.models.generate_content(

            model="gemini-3.1-flash-lite",

            contents=prompt,

            config=types.GenerateContentConfig(

                temperature=0,

                response_mime_type="application/json",

                response_schema={
                    "type": "OBJECT",
                    "properties": {

                        "intent": {
                            "type": "STRING",
                            "enum": [
                                "greeting",
                                "product_search",
                                "casual",
                                "invalid"
                            ]
                        },

                        "search_query": {
                            "type": "STRING"
                        },

                        "confidence": {
                            "type": "NUMBER"
                        },

                        "reason": {
                            "type": "STRING"
                        }

                    },

                    "required": [
                        "intent",
                        "search_query",
                        "confidence",
                        "reason"
                    ]
                }
            )
        )


        # ====================================================
        # READ GEMINI RESPONSE
        # ====================================================

        response_text = response.text.strip()


        if not response_text:

            return {
                "intent": "error",
                "search_query": "",
                "confidence": 0.0,
                "reason": (
                    "Gemini returned an empty response."
                )
            }


        # ====================================================
        # CONVERT JSON
        # ====================================================

        result = json.loads(
            response_text
        )


        # ====================================================
        # GET VALUES
        # ====================================================

        intent = result.get(
            "intent",
            "invalid"
        )

        search_query = result.get(
            "search_query",
            ""
        )

        confidence = result.get(
            "confidence",
            0.0
        )

        reason = result.get(
            "reason",
            "Gemini analyzed the message."
        )


        # ====================================================
        # VALIDATE INTENT
        # ====================================================

        valid_intents = {
            "greeting",
            "product_search",
            "casual",
            "invalid"
        }


        if intent not in valid_intents:

            intent = "invalid"


        # ====================================================
        # CLEAN SEARCH QUERY
        # ====================================================

        if not isinstance(
            search_query,
            str
        ):

            search_query = ""


        search_query = search_query.strip()


        # ====================================================
        # PRODUCT SEARCH FALLBACK
        # ========================================================

        if (
            intent == "product_search"
            and not search_query
        ):

            search_query = message


        # ====================================================
        # CONFIDENCE
        # ========================================================

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            confidence = 0.0


        confidence = max(
            0.0,
            min(
                1.0,
                confidence
            )
        )


        # ====================================================
        # RETURN RESULT
        # ========================================================

        return {
            "intent": intent,
            "search_query": search_query,
            "confidence": confidence,
            "reason": reason
        }


    # ========================================================
    # GEMINI ERROR
    # ========================================================

    except Exception as error:

        print(
            "Gemini error:",
            error
        )


        return {
            "intent": "error",
            "search_query": "",
            "confidence": 0.0,
            "reason": (
                "Gemini could not analyze the message."
            )
        }


# ============================================================
# MAIN RESPONSE HANDLER
# ============================================================

def get_ai_response(message):

    result = analyze_user_message(
        message
    )


    intent = result["intent"]


    # ========================================================
    # GEMINI ERROR
    # ========================================================

    if intent == "error":

        return {
            "type": "text",
            "message": (
                "Sorry, I am temporarily unable to "
                "understand your request. Please try again."
            ),
            "analysis": result
        }


    # ========================================================
    # GREETING
    # ========================================================

    if intent == "greeting":

        return {
            "type": "text",
            "message": (
                "Hello! How can I help you today?"
            ),
            "analysis": result
        }


    # ========================================================
    # CASUAL
    # ========================================================

    if intent == "casual":

        normalized = message.lower().strip()


        if normalized in {
            "thanks",
            "thank you",
            "thankyou"
        }:

            response = (
                "You're welcome! "
                "How can I help you find a Hindcon product?"
            )


        elif normalized in {
            "bye",
            "goodbye"
        }:

            response = (
                "Goodbye! Have a great day."
            )


        elif normalized in {
            "how are you",
            "how are ypu",
            "how are u",
            "how r you",
            "how r u"
        }:

            response = (
                "I'm doing well! "
                "How can I help you find a Hindcon product?"
            )


        elif normalized in {
            "who are you",
            "what are you"
        }:

            response = (
                "I'm a Hindcon Product Assistant. "
                "I can help you find Hindcon products "
                "and their TDS/MSDS documents."
            )


        else:

            response = (
                "I'm here to help you find Hindcon products "
                "and their TDS/MSDS documents."
            )


        return {
            "type": "text",
            "message": response,
            "analysis": result
        }


    # ========================================================
    # INVALID
    # ========================================================

    if intent == "invalid":

        return {
            "type": "text",
            "message": (
                "Sorry, I can only help you search for "
                "Hindcon products and their TDS/MSDS documents."
            ),
            "analysis": result
        }


    # ========================================================
    # PRODUCT SEARCH
    # ========================================================

    if intent == "product_search":

        return {
            "type": "product_search",
            "search_query": result[
                "search_query"
            ],
            "analysis": result
        }


    # ========================================================
    # FINAL FALLBACK
    # ========================================================

    return {
        "type": "text",
        "message": (
            "Sorry, I could not understand your request."
        ),
        "analysis": result
    }