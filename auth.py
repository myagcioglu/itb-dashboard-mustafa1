import pandas as pd
import bcrypt
import streamlit as st

USERS_FILE = "users.csv"

def load_users() -> pd.DataFrame:
    return pd.read_csv(USERS_FILE, dtype=str).fillna("")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def login_ui():
    st.sidebar.subheader("Giriş")
    username = st.sidebar.text_input("Kullanıcı adı")
    password = st.sidebar.text_input("Şifre", type="password")

    if st.sidebar.button("Giriş yap"):
        users = load_users()
        row = users[users["username"] == username]
        if row.empty:
            st.sidebar.error("Kullanıcı bulunamadı.")
            return None

        user = row.iloc[0].to_dict()
        if not verify_password(password, user.get("password_hash", "")):
            st.sidebar.error("Şifre hatalı.")
            return None

        st.session_state["user"] = user
        st.sidebar.success(f"Hoş geldin, {user.get('display_name', username)}")
        return user

    return st.session_state.get("user")

def logout_ui():
    if st.sidebar.button("Çıkış"):
        st.session_state.pop("user", None)
        st.rerun()
