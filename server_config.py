from __future__ import annotations

import os


def get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value.strip()

    try:
        import streamlit as st

        secret_value = st.secrets.get(name, default)
    except Exception:
        return default

    if secret_value is None:
        return default
    return str(secret_value).strip()
