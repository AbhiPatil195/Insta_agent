from __future__ import annotations
import hashlib
import hmac
import requests
from typing import Tuple

from shared.config import META_APP_SECRET, META_IG_BUSINESS_ID, META_GRAPH_VERSION


def _messages_url() -> str:
    version = META_GRAPH_VERSION or "21.0"
    base = f"https://graph.facebook.com/v{version}"
    if META_IG_BUSINESS_ID:
        return f"{base}/{META_IG_BUSINESS_ID}/messages"
    return f"{base}/me/messages"


def appsecret_proof(token: str, app_secret: str | None) -> str | None:
    if not token or not app_secret:
        return None
    digest = hmac.new(app_secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest


def send_instagram_text(user_psid: str, text: str, page_access_token: str | None) -> Tuple[bool, str | None]:
    if not page_access_token:
        return False, "Missing META_PAGE_ACCESS_TOKEN"

    params = {"access_token": page_access_token}
    proof = appsecret_proof(page_access_token, META_APP_SECRET)
    if proof:
        params["appsecret_proof"] = proof

    payload = {
        "messaging_product": "instagram",
        "recipient": {"id": user_psid},
        "message": {"text": text[:990]},
    }

    try:
        resp = requests.post(_messages_url(), params=params, json=payload, timeout=15)
        if resp.status_code >= 400:
            return False, f"{resp.status_code}: {resp.text}"
        return True, None
    except Exception as e:
        return False, str(e)


def send_mark_seen(user_psid: str, page_access_token: str | None) -> Tuple[bool, str | None]:
    if not page_access_token:
        return False, "Missing META_PAGE_ACCESS_TOKEN"
    params = {"access_token": page_access_token}
    proof = appsecret_proof(page_access_token, META_APP_SECRET)
    if proof:
        params["appsecret_proof"] = proof
    payload = {
        "messaging_product": "instagram",
        "recipient": {"id": user_psid},
        "sender_action": "mark_seen",
    }
    try:
        resp = requests.post(_messages_url(), params=params, json=payload, timeout=10)
        if resp.status_code >= 400:
            return False, f"{resp.status_code}: {resp.text}"
        return True, None
    except Exception as e:
        return False, str(e)


def send_typing_on(user_psid: str, page_access_token: str | None) -> Tuple[bool, str | None]:
    if not page_access_token:
        return False, "Missing META_PAGE_ACCESS_TOKEN"
    params = {"access_token": page_access_token}
    proof = appsecret_proof(page_access_token, META_APP_SECRET)
    if proof:
        params["appsecret_proof"] = proof
    payload = {
        "messaging_product": "instagram",
        "recipient": {"id": user_psid},
        "sender_action": "typing_on",
    }
    try:
        resp = requests.post(_messages_url(), params=params, json=payload, timeout=10)
        if resp.status_code >= 400:
            return False, f"{resp.status_code}: {resp.text}"
        return True, None
    except Exception as e:
        return False, str(e)
