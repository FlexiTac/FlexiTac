"""The static site's Python side: ``web/py/worker.js`` imports this module in
Pyodide and calls ``handle`` for every API request of the page.

The answer is ``app.answer``'s, so the browser gets the server's replies; an
unexpected failure becomes the server's 500 JSON (``AppHandler._dispatch``),
with the traceback in the browser console instead of the server log.
"""

from __future__ import annotations

import json
import sys
import traceback
from http import HTTPStatus
from typing import Any

import app
from engine import BuildCache
from engine.profile import ProfileError

CACHE = BuildCache(app.BUILD_CACHE_SIZE)


def handle(method: str, target: str, content_type: str, body: Any) -> tuple[int, str, str, bytes]:
    """Status, reason phrase, headers (JSON pairs, Content-Type first) and body of one request.

    ``body`` is bytes, or the page's Uint8Array (a Pyodide JsProxy)."""

    data = bytes(body) if isinstance(body, (bytes, bytearray, memoryview)) else body.to_bytes()
    try:
        reply = app.answer(method, target, content_type, data, cache=CACHE)
    except ProfileError:
        reply = _failed("E_PROFILE_INVALID", "The bundled manufacturing profile is inconsistent; see the browser console.")
    except Exception:
        reply = _failed("E_INTERNAL", "Unexpected error in the in-browser generator; see the browser console.")
    headers = [("Content-Type", reply.content_type), *reply.headers]
    return reply.status, HTTPStatus(reply.status).phrase, json.dumps(headers), reply.body


def _failed(code: str, message: str) -> app.Reply:
    sys.stderr.write(f"[flexitac-gen] {code}\n{traceback.format_exc()}")
    return app.error_reply(HTTPStatus.INTERNAL_SERVER_ERROR, code, message)
