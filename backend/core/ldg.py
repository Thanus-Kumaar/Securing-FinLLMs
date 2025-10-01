import json
import os
import re
import spacy

CONFIG_PATH = "blocked_keywords.json"

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None  


def load_ldg_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {
        "input_patterns": [],             
        "prompt_injection_patterns": [],  
        "output_patterns": []
    }

LDG_CONFIG = load_ldg_config()

# -------------------------------
SENSITIVE_PATTERNS = {
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}": "*****@*****",       # Email
    r"\b\d{10,16}\b": "************",                                        # Phone / Account numbers
    r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b": "**** ****",                             # Full name
    r"\b\d{4}-?\d{4}-?\d{4}-?\d{4}\b": "****-****-****-****",               # Credit Card
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b": "xxx.xxx.xxx.xxx",                        # IPv4 Address
}


# -------------------------------
# Input Validation
# -------------------------------
def ldg_input_check(user_input: str) -> dict:
    masked_input = user_input
    detected_entities = []

    
    for pattern in LDG_CONFIG.get("input_patterns", []):
        if re.search(pattern, user_input, flags=re.IGNORECASE):
            return {"status": "blocked", "reason": f"Blocked pattern '{pattern}' detected"}

    for pattern, mask in SENSITIVE_PATTERNS.items():
        masked_input = re.sub(pattern, mask, masked_input)

    if nlp:
        doc = nlp(user_input)
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "EMAIL", "GPE", "ORG", "PHONE", "CARDINAL"]:
                detected_entities.append(ent.label_)
                masked_input = masked_input.replace(ent.text, "*" * len(ent.text))

    return {
        "status": "ok",
        "masked_input": masked_input,
        "detected_entities": detected_entities
    }


# -------------------------------
# -------------------------------
def detect_prompt_injection(prompt: str) -> dict:
    lp = prompt.lower()
    for pattern in LDG_CONFIG.get("prompt_injection_patterns", []):
        if re.search(pattern.lower(), lp):
            return {"status": "blocked", "reason": "Potential prompt injection detected"}
    return {"status": "ok"}


# -------------------------------

# -------------------------------
def ldg_output_check(agent_output: str) -> dict:
    for pattern in LDG_CONFIG.get("output_patterns", []):
        if re.search(pattern, agent_output, flags=re.IGNORECASE):
            return {"status": "blocked", "reason": f"Output contains blocked pattern '{pattern}'"}
    return {"status": "ok"}
