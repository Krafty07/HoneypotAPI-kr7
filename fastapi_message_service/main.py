from typing import Dict, List
import os
import re
import random
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
import google.generativeai as genai

# =========================
# Load ENV
# =========================
load_dotenv()

API_KEY = os.getenv("API_KEY", "kr7-secret")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# =========================
# Gemini Setup
# =========================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# =========================
# App
# =========================
app = FastAPI()

# =========================
# Memory
# =========================
conversations: Dict[str, List[dict]] = {}

# =========================
# Models
# =========================
class MessageRequest(BaseModel):
    conversation_id: str
    message: str


class MessageResponse(BaseModel):
    is_scam: bool
    reply: str
    turns: int
    intelligence: dict


# =========================
# Security
# =========================
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


# =========================
# Scam Detection
# =========================
def detect_scam(text: str) -> bool:
    keywords = [
        "otp", "bank", "upi", "kyc", "account blocked",
        "urgent", "refund", "link", "verify", "payment failed"
    ]

    text = text.lower()
    return any(word in text for word in keywords)


# =========================
# Personas
# =========================
PERSONAS = [
    "You are a 55-year-old uncle who is bad with technology and asks many basic questions.",
    "You are a confused college student who doesn’t understand banking terms.",
    "You run a small grocery shop and are worried about refund issues.",
    "You are not tech-savvy and keep saying things like 'link not opening'.",
    "You are impatient and ask the scammer to repeat details again and again."
]


# =========================
# Gemini Agent
# =========================
def generate_agent_reply(history: List[dict]) -> str:
    try:
        persona = random.choice(PERSONAS)

        system_prompt = (
            f"{persona} "
            "Act confused and cooperative. Never reveal you suspect a scam. "
            "Try to naturally ask for bank account numbers, UPI IDs or links. "
            "Keep replies short and realistic.\n\n"
        )

        # Convert history to plain text for Gemini
        convo_text = ""
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            convo_text += f"{role}: {msg['content']}\n"

        prompt = system_prompt + convo_text + "Assistant:"

        model.generate_content(prompt, request_options={"timeout": 5})

        return response.text.strip()

    except Exception as e:
        print("Gemini error:", e)
        return "Okay, can you send details again?"


# =========================
# Intelligence Extraction
# =========================
def extract_intelligence(text: str) -> dict:
    upi_pattern = r"\b[\w.-]+@[\w]+\b"
    url_pattern = r"https?://\S+"
    account_pattern = r"\b\d{9,18}\b"

    return {
        "upi_ids": list(set(re.findall(upi_pattern, text))),
        "urls": list(set(re.findall(url_pattern, text))),
        "bank_accounts": list(set(re.findall(account_pattern, text)))
    }


# =========================
# Endpoint
# =========================
@app.post("/message", response_model=MessageResponse)
async def process_message(
    request: MessageRequest,
    api_key: str = Depends(verify_api_key)
):

    cid = request.conversation_id
    message = request.message

    if cid not in conversations:
        conversations[cid] = []

    # store user message
    conversations[cid].append({"role": "user", "content": message})

    # detect scam
    is_scam = detect_scam(message)

    reply = "received"

    if is_scam:
        reply = generate_agent_reply(conversations[cid])
        conversations[cid].append({"role": "assistant", "content": reply})

    turns = len(conversations[cid])

    # extraction
    intelligence = extract_intelligence(message + " " + reply)

    return MessageResponse(
        is_scam=is_scam,
        reply=reply,
        turns=turns,
        intelligence=intelligence
    )
