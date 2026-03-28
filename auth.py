from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hmac

import pandas as pd
import streamlit as st

USERS_FILE = "users.csv"
REQUIRED_COLUMNS = {"username", "password", "role", "societes_autorisees", "enabled"}
OPTIONAL_COLUMNS = {"display_name"}


@dataclass
class AuthenticatedUser:
    username: str
    display_name: str
    role: str
    societes_autorisees: list[str]

    @property
    def is_admin(self) -> bool:
        return self.role.lower() == "admin"


def _normalize_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "oui", "yes"])


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
            missing = REQUIRED_COLUMNS.difference(df.columns)
            if missing:
                missing_text = ", ".join(sorted(missing))
                raise ValueError(
                    "Le fichier users.csv est incomplet. Colonnes obligatoires : "
                    f"username;password;role;societes_autorisees;enabled. Manquantes : {missing_text}"
                )

            df["username"] = df["username"].astype(str).str.strip().str.lower()
            df["password"] = df["password"].fillna("").astype(str)
            df["role"] = df["role"].astype(str).str.strip().str.lower()
            df["enabled"] = _normalize_bool(df["enabled"])
            df["societes_autorisees"] = df["societes_autorisees"].fillna("").astype(str)

            if "display_name" not in df.columns:
                df["display_name"] = df["username"]
            else:
                df["display_name"] = df["display_name"].fillna(df["username"]).astype(str).str.strip()
                df.loc[df["display_name"].eq(""), "display_name"] = df["username"]
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



def verify_password(password_entered: str, password_expected: str) -> bool:
    return hmac.compare_digest(str(password_entered or ""), str(password_expected or ""))



def authenticate_user(username: str, password: str, search_root: Path | None = None) -> AuthenticatedUser | None:
    users = load_users(search_root)
    username_normalized = str(username or "").strip().lower()
    row = users.loc[users["username"] == username_normalized]
    if row.empty:
        return None

    user = row.iloc[0]
    if not bool(user["enabled"]):
        return None
    if not verify_password(password, str(user["password"])):
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

    st.info(
        "Version simple : users.csv contient les mots de passe en clair. À utiliser pour un prototype sur dépôt privé."
    )
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
