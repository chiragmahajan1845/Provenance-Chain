import streamlit as st
import json
from datetime import datetime
from web3 import Web3

st.set_page_config(page_title="ProvenanceChain", layout="centered")

@st.cache_resource
def load_contract():
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
    if not serial_input.strip():
        st.error("Please enter a valid serial number.")
    elif contract is None:
        st.warning("Running in Demo Mode (Local blockchain not connected). Showing sample verified record:")
        st.success("✅ **GENUINE PRODUCT CONFIRMED (Tamper-Free Record)**")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Product Name:** Nike Air Max Precision")
            st.write("**Brand:** Nike")
            st.write(f"**Serial:** `{serial_input}`")
        with col2:
            st.write("**Current Stage:** `Warehoused`")
            st.write("**Custodian:** `0x7099...79C8`")
        
        st.subheader("Custody Chain Timeline")
        st.info("1. Manufactured — Caguas, Puerto Rico")
        st.info("2. InTransit — Regional Sort Center, San Juan")
        st.info("3. Warehoused — National Distribution Hub, Miami")
    else:
        try:
            p_id = contract.functions.generateProductId(serial_input.strip()).call()
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
            st.error(f"Could not find this serial on-chain or network error: {e}")
