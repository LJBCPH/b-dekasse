import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import urllib.parse

# CONFIG
ADMIN_TOKEN = "bødekassemand"
MOBILEPAY_PHONE = "12345678"  # Replace with your actual number

# --- Load Data ---
def load_members():
    try:
        return pd.read_csv("./members.csv").sort_values(by="name", ascending=True)
    except FileNotFoundError:
        return pd.DataFrame(columns=["name"])

def load_fines():
    try:
        return pd.read_csv("./fines.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["id", "member", "fine", "amount", "date"])

def save_members(df):
    df.to_csv("./members.csv", index=False)

def save_fines(df):
    df.to_csv("./fines.csv", index=False)

# --- Fine Catalog ---
FINE_CATALOG = {
    "Afbud": 20,
    "No-show": 1000,
    #"For sent afbud": 50
}

# --- Load state ---
members_df = load_members()
fines_df = load_fines()
member_names = members_df["name"].tolist()

# --- Admin Access ---
query_params = st.query_params
is_admin = query_params.get("admin_token", [None]) == ADMIN_TOKEN
# --- Title ---
st.title("⚽ SKJOLDSVINDERHOLD BØDEKASSE")

# --- Public View ---
st.subheader("📋 Bødeoversigt")
st.dataframe(pd.DataFrame(FINE_CATALOG.items(), columns=["Bøde", "Pris"]).sort_values(by="Pris", ascending=False), use_container_width=True, hide_index=True)

st.subheader(f"💰 Bødeliste - {fines_df["amount"].sum()} DKK")
if not fines_df.empty:
    total_owed = fines_df.groupby("member")["amount"].sum().reset_index()
    total_owed.columns = ["Spiller", "Total"]
    total_owed = total_owed.sort_values(by="Total", ascending=False)
    st.dataframe(total_owed, use_container_width=True, hide_index=True)
else:
    st.info("Ingen bøder!")

# --- Member History ---
if member_names:
    selected_member = st.selectbox("Select a member", member_names)

    member_fines = fines_df[fines_df["member"] == selected_member]

    if not member_fines.empty:
        st.dataframe(member_fines[["fine", "amount", "date"]], use_container_width=True, hide_index=True)

        if is_admin and st.button(f"❌ Clear all fines for {selected_member}"):
            fines_df = fines_df[fines_df["member"] != selected_member]
            save_fines(fines_df)
            st.success(f"All fines for {selected_member} have been cleared.")
            st.rerun()
    else:
        st.info(f"{selected_member} er gældsfri.")

# --- MobilePay Links ---
if not fines_df.empty:
    st.subheader("📲 Send pengene over MobilePay")
    for _, row in total_owed.iterrows():
        name = row["Spiller"]
        amount = int(row["Total"])
        msg = urllib.parse.quote(f"Fine payment for {name}")
        pay_url = f"https://mobilepay.dk/erhverv/betalingslink?phone={MOBILEPAY_PHONE}&amount={amount}&comment={msg}"
        st.markdown(f"**{name}**: Skylder {amount} til XXXXXXXXX")


# --- Admin Panel ---
if is_admin:
    st.markdown("---")
    st.subheader("🔐 Admin Panel")

    st.markdown("### ➕ Tilføj bøde")
    if not member_names:
        st.warning("Ingen medlemmer i klubben!!.")
    else:
        member = st.selectbox("Vælg spiller", member_names, key="fine_member")
        fine_type = st.selectbox("Vælg bøde", list(FINE_CATALOG.keys()))
        if st.button("Tilføj bøde"):
            fines_df = load_fines()
            st.markdown(fines_df)
            new_fine = {
                "id": str(uuid.uuid4()),
                "member": member,
                "fine": fine_type,
                "amount": FINE_CATALOG[fine_type],
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            fines_df = pd.concat([fines_df, pd.DataFrame([new_fine])], ignore_index=True)
            save_fines(fines_df)
            st.success(f"Bøde '{fine_type}' tilføjet til {member}.")
            st.rerun()

    st.markdown("### 👥 Rediger spillere")
    with st.form("member_form"):
        new_member = st.text_input("Tilføj ny spiller")
        if st.form_submit_button("Tilføj spiller"):
            if new_member and new_member not in member_names:
                members_df = pd.concat([members_df, pd.DataFrame([{"name": new_member}])], ignore_index=True)
                save_members(members_df)
                st.success(f"TIlføjede: {new_member}")
            else:
                st.warning("Spiller er allerede i klubben.")

        if st.checkbox("Fjern medlemmer"):
            member_to_remove = st.selectbox("Vælg medlem du vil fjerne", member_names)
            if st.form_submit_button("Fjern medlem"):
                members_df = members_df[members_df["name"] != member_to_remove]
                save_members(members_df)
                st.success(f"Fjernede: {member_to_remove}")

# --- Admin Access Hint ---
if not is_admin:
    st.markdown("---")
    st.markdown("🔐 Are you an admin? Go to:")
    admin_link = f"?admin_token={ADMIN_TOKEN}"
    st.code(admin_link)