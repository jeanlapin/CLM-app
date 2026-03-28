from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import base64
import hashlib
import hmac
import os

import pandas as pd
import streamlit as st

USERS_FILE = "users.csv"


@dataclass
class AuthenticatedUser:
    username: str
    display_name: str
    role: str
    societes_autorisees: list[str]

    @property
    def is_admin(self) -> bool:
        return self.role.lower() == "admin"


def hash_password(password: str, iterations: int = 260_000) -> str:
    salt = base64.urlsafe_b64encode(os.urandom(16)).decode("ascii").rstrip("=")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    token = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${iterations}${salt}${token}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt, expected = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations_text),
        )
        candidate = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return hmac.compare_digest(candidate, expected)
    except Exception:
        return False


@st.cache_data(show_spinner=False)
def load_users(search_root: Path | None = None) -> pd.DataFrame:
    here = search_root or Path(__file__).resolve().parent
    candidates = [
        here / USERS_FILE,
        here / "data" / USERS_FILE,
        here.parent / USERS_FILE,
        here.parent / "data" / USERS_FILE,
        Path.cwd() / USERS_FILE,
        Path.cwd() / "data" / USERS_FILE,
    ]
    for path in candidates:
        if path.exists():
            df = pd.read_csv(path, sep=";", encoding="utf-8-sig").dropna(how="all")
            expected_cols = {"username", "display_name", "password_hash", "role", "enabled", "societes_autorisees"}
            missing = expected_cols.difference(df.columns)
            if missing:
                missing_text = ", ".join(sorted(missing))
                raise ValueError(f"Le fichier users.csv est incomplet. Colonnes manquantes : {missing_text}")
            df["username"] = df["username"].astype(str).str.strip().str.lower()
            df["display_name"] = df["display_name"].astype(str).str.strip()
            df["role"] = df["role"].astype(str).str.strip().str.lower()
            df["enabled"] = df["enabled"].astype(str).str.strip().str.lower().isin(["true", "1", "oui", "yes"])
            df["societes_autorisees"] = df["societes_autorisees"].fillna("").astype(str)
            return df
    searched = "\n - ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        "Impossible de trouver users.csv. Créez ce fichier à la racine du dépôt."
        f"\nEmplacements testés :\n - {searched}"
    )


def parse_allowed_societies(raw_value: str) -> list[str]:
    raw = str(raw_value or "").strip()
    if not raw:
        return []
    if raw.upper() == "ALL":
        return ["ALL"]
    return sorted({item.strip().upper() for item in raw.split(",") if item.strip()})


def authenticate_user(username: str, password: str, search_root: Path | None = None) -> AuthenticatedUser | None:
    users = load_users(search_root)
    username_normalized = username.strip().lower()
    row = users.loc[users["username"] == username_normalized]
    if row.empty:
        return None
    user = row.iloc[0]
    if not bool(user["enabled"]):
        return None
    if not verify_password(password, str(user["password_hash"])):
        return None
    return AuthenticatedUser(
        username=str(user["username"]),
        display_name=str(user["display_name"]),
        role=str(user["role"]),
        societes_autorisees=parse_allowed_societies(str(user["societes_autorisees"])),
    )


def login_form() -> AuthenticatedUser | None:
    if st.session_state.get("authenticated_user"):
        payload = st.session_state["authenticated_user"]
        return AuthenticatedUser(**payload)

    st.subheader("Connexion")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter", type="primary")

    if submitted:
        user = authenticate_user(username, password)
        if user is None:
            st.error("Identifiants invalides ou compte désactivé.")
            return None
        st.session_state["authenticated_user"] = {
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "societes_autorisees": user.societes_autorisees,
        }
        st.rerun()

    st.info("Ajoutez un fichier users.csv à la racine du projet pour activer les comptes utilisateurs.")
    return None


def get_current_user() -> AuthenticatedUser | None:
    payload = st.session_state.get("authenticated_user")
    if not payload:
        return None
    return AuthenticatedUser(**payload)


def logout_button() -> None:
    if st.button("Se déconnecter"):
        st.session_state.pop("authenticated_user", None)
        st.rerun()
