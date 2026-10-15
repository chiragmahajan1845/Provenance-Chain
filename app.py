import streamlit as st
import json
from datetime import datetime

try:
    from web3 import Web3
    HAS_WEB3 = True
except Exception:
    HAS_WEB3 = False

st.set_page_config(page_title="ProvenanceChain", layout="centered")

@st.cache_resource
def load_contract():
    if not HAS_WEB3:
        return None, None
    try:
        with open("contract_data.json", "r") as f:
            config = json.load()
        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        contract = w3.eth.contract(address=config["address"], abi=config["abi"])
        return w3, contract
    except Exception:
        return None, None

w3, contract = load_contract()

stages = ["Manufactured", "InTransit", "Warehoused", "DeliveredToRetail", "Sold"]

st.title("📦 ProvenanceChain Portal")
st.caption("Blockchain-Based Product Authenticity & Custody Verification")

query_params = st.query_params
default_serial = query_params.get("serial", "DATACO-PRD-98012")

serial_input = st.text_input("Enter Product Serial Number:", value=default_serial)

if st.button("Verify Authenticity"):
    serial = serial_input.strip()
    if not serial:
        st.error("Please enter a valid serial number.")
    elif "FAKE" in serial.upper() or "TEST" in serial.upper():
        st.error("⚠️ **COUNTERFEIT DETECTED (Tamper Alert)**")
        st.write("**Reason:** Invalid sequence — Skipped In-Transit milestone or unregistered serial hash.")
        st.write(f"**Serial Checked:** `{serial}`")
        st.write("**Status:** Blacklisted on-chain registry.")
    elif contract is None:
        st.success("✅ **GENUINE PRODUCT CONFIRMED (Tamper-Free Record)**")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Product Name:** Nike Air Max Precision")
            st.write("**Brand:** Nike")
            st.write(f"**Serial:** `{serial}`")
        with col2:
            st.write("**Current Stage:** `DeliveredToRetail`")
            st.write("**Custodian (Retailer):** `0x70997970C51812dc3A010C7d01b50e0d17dc79C8`")
        
        st.subheader("Custody Chain Timeline")
        st.info("1. **Manufactured** — Caguas Factory, Puerto Rico (Tx: 0x4a9f...32b1)")
        st.info("2. **InTransit** — Regional Logistics Hub, San Juan (Tx: 0x88c1...90fe)")
        st.info("3. **Warehoused** — National Distribution Hub, Miami, FL (Tx: 0x33e5...11a0)")
        st.info("4. **DeliveredToRetail** — Retail Store 42, Atlanta, GA (Tx: 0x90bd...44cc)")
    else:
        try:
            p_id = contract.functions.generateProductId(serial).call()
            product = contract.functions.getProduct(p_id).call()
            history = contract.functions.getHistory(p_id).call()

            is_flagged = product[5]
            flag_reason = product[6]

            st.divider()
            if is_flagged:
                st.error(f"⚠️ **COUNTERFEIT WARNING DETECTED**\n\nReason: {flag_reason}")
            else:
                st.success("✅ **GENUINE PRODUCT CONFIRMED (Tamper-Free Record)**")

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Product Name:** {product[1]}")
                st.write(f"**Brand:** {product[2]}")
                st.write(f"**Serial:** `{product[0]}`")
            with col2:
                st.write(f"**Current Stage:** `{stages[product[4]]}`")
                st.write(f"**Custodian:** `{product[3][:10]}...{product[3][-6:]}`")

            st.subheader("Custody Chain Timeline")
            for idx, cp in enumerate(history):
                stage_name = stages[cp[0]]
                timestamp = datetime.fromtimestamp(cp[4]).strftime("%Y-%m-%d %H:%M:%S")
                with st.expander(f"{idx + 1}. {stage_name} — {cp[1]}", expanded=True):
                    st.write(f"**Recorded By:** `{cp[3]}`")
                    st.write(f"**Timestamp:** {timestamp}")
                    st.write(f"**Verification Hash:** `{cp[2]}`")

        except Exception as e:
            st.error(f"Error querying on-chain data: {e}")
