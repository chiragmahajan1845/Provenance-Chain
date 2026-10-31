
import streamlit as st
import json
import numpy as np
from datetime import datetime

try:
    from web3 import Web3
    HAS_WEB3 = True
except ImportError:
    HAS_WEB3 = False

try:
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# -------------------------------
# STREAMLIT CONFIG
# -------------------------------

st.set_page_config(
    page_title="ProvenanceChain AI",
    page_icon="📦",
    layout="wide"
)

st.title("📦 ProvenanceChain AI")
st.caption(
    "Blockchain-Based Product Authenticity "
    "& AI Risk Detection System"
)


# -------------------------------
# BLOCKCHAIN CONNECTION
# -------------------------------

@st.cache_resource
def load_contract():

    if not HAS_WEB3:
        return None, None

    try:

        with open("contract_data.json", "r") as f:
            config = json.load(f)

        w3 = Web3(
            Web3.HTTPProvider(
                "http://127.0.0.1:8545"
            )
        )

        if not w3.is_connected():
            return None, None

        contract = w3.eth.contract(
            address=Web3.to_checksum_address(
                config["address"]
            ),
            abi=config["abi"]
        )

        return w3, contract

    except Exception:
        return None, None


w3, contract = load_contract()


# -------------------------------
# PRODUCT STAGES
# -------------------------------

stages = [
    "Manufactured",
    "InTransit",
    "Warehoused",
    "DeliveredToRetail",
    "Sold"
]


# -------------------------------
# AI FEATURE EXTRACTION
# -------------------------------

def extract_features(history):

    if not history:
        return None

    try:

        stage_values = []
        timestamps = []
        custodians = []

        for record in history:

            stage_values.append(int(record[0]))

            custodians.append(
                str(record[3]).lower()
            )

            timestamps.append(
                int(record[4])
            )

        stage_count = len(stage_values)

        unique_custodians = len(
            set(custodians)
        )

        stage_changes = sum(
            1 for i in range(1, stage_count)
            if stage_values[i] != stage_values[i - 1]
        )

        time_gaps = []

        for i in range(1, len(timestamps)):

            gap = (
                timestamps[i] - timestamps[i - 1]
            )

            time_gaps.append(
                max(gap, 0)
            )

        total_time = sum(time_gaps)

        average_gap = (
            np.mean(time_gaps)
            if time_gaps else 0
        )

        minimum_gap = (
            min(time_gaps)
            if time_gaps else 0
        )

        return np.array([
            stage_count,
            unique_custodians,
            stage_changes,
            total_time,
            average_gap,
            minimum_gap
        ], dtype=float)

    except Exception:

        return None


# -------------------------------
# AI RISK ANALYSIS
# -------------------------------

def ai_risk_analysis(history):

    features = extract_features(history)

    if features is None:

        return {
            "risk": 0,
            "status": "Insufficient Data",
            "details": [
                "Product history unavailable."
            ]
        }

    risk = 0

    details = []

    # Number of recorded custody events

    if len(history) < 2:

        risk += 20

        details.append(
            "Very limited custody history."
        )

    # Analyze stage sequence

    stages_found = []

    for record in history:

        try:

            stages_found.append(
                int(record[0])
            )

        except Exception:
            continue

    if stages_found:

        if any(
            stage < 0 or stage >= len(stages)
            for stage in stages_found
        ):

            risk += 40

            details.append(
                "Invalid product stage detected."
            )

        # Check for unexpected stage movement

        for i in range(1, len(stages_found)):

            previous = stages_found[i - 1]

            current = stages_found[i]

            if current < previous:

                risk += 25

                details.append(
                    "Product stage moved backwards."
                )

            elif current > previous + 1:

                risk += 15

                details.append(
                    "Product skipped a custody stage."
            )

    # Analyze timestamps

    timestamps = []

    for record in history:

        try:

            timestamps.append(
                int(record[4])
            )

        except Exception:
            continue

    for i in range(1, len(timestamps)):

        gap = (
            timestamps[i] - timestamps[i - 1]
        )

        if gap < 0:

            risk += 35

            details.append(
                "Suspicious timestamp sequence."
            )

        elif gap < 60:

            risk += 10

            details.append(
                "Very rapid custody movement."
            )

    # Analyze custodians

    custodians = []

    for record in history:

        try:

            custodians.append(
                str(record[3]).lower()
            )

        except Exception:
            continue

    if len(custodians) >= 3:

        if len(set(custodians)) == 1:

            risk += 10

            details.append(
                "All records have the same custodian."
            )

    # -------------------------------
    # ISOLATION FOREST AI
    # -------------------------------

    if HAS_SKLEARN and len(history) >= 3:

        try:

            training_data = []

            for count in range(3, len(history) + 1):

                sample = extract_features(
                    history[:count]
                )

                if sample is not None:

                    training_data.append(
                        sample
                    )

            if len(training_data) >= 3:

                model = IsolationForest(
                    contamination=0.15,
                    random_state=42
                )

                model.fit(
                    training_data
                )

                prediction = model.predict(
                    features.reshape(1, -1)
                )

                if prediction[0] == -1:

                    risk += 20

                    details.append(
                        "AI detected an unusual "
                        "custody pattern."
                    )

        except Exception:

            details.append(
                "AI model could not analyze "
                "the available history."
            )

    # -------------------------------
    # FINAL RISK
    # -------------------------------

    risk = min(
        max(risk, 0),
        100
    )

    if risk >= 60:

        status = "HIGH RISK"

    elif risk >= 30:

        status = "MEDIUM RISK"

    else:

        status = "LOW RISK"

    if not details:

        details.append(
            "No suspicious patterns "
            "were detected in the available history."
        )

    return {
        "risk": risk,
        "status": status,
        "details": details
    }


# -------------------------------
# PRODUCT SERIAL INPUT
# -------------------------------

query_params = st.query_params

default_serial = query_params.get(
    "serial",
    "DATACO-PRD-98012"
)

serial_input = st.text_input(
    "Enter Product Serial Number",
    value=default_serial
)


# -------------------------------
# VERIFY PRODUCT
# -------------------------------

if st.button(
    "🔍 Verify Product",
    use_container_width=True
):

    serial = serial_input.strip()

    if not serial:

        st.error(
            "Please enter a valid serial number."
        )

    elif contract is None:

        st.error(
            "Blockchain connection unavailable."
        )

        st.warning(
            "Product authenticity could not "
            "be verified."
        )

        st.info(
            "Start your blockchain node "
            "and check contract_data.json."
        )

    else:

        try:

            # Generate product ID

            product_id = (
                contract.functions
                .generateProductId(serial)
                .call()
            )

            # Get product information

            product = (
                contract.functions
                .getProduct(product_id)
                .call()
            )

            # Get custody history

            history = (
                contract.functions
                .getHistory(product_id)
                .call()
            )

            # Product details

            product_name = product[1]

            brand = product[2]

            custodian = product[3]

            current_stage = int(product[4])

            is_flagged = product[5]

            flag_reason = product[6]

            # -------------------------------
            # PRODUCT INFORMATION
            # -------------------------------

            st.divider()

            st.subheader(
                "📋 Product Information"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    "**Product:**",
                    product_name
                )

                st.write(
                    "**Brand:**",
                    brand
                )

                st.write(
                    "**Serial:**",
                    serial
                )

            with col2:

                if 0 <= current_stage < len(stages):

                    st.write(
                        "**Current Stage:**",
                        stages[current_stage]
                    )

                else:

                    st.warning(
                        "Invalid product stage."
                    )

                st.write(
                    "**Custodian:**",
                    str(custodian)
                )

            # -------------------------------
            # BLOCKCHAIN STATUS
            # -------------------------------

            st.subheader(
                "🔗 Blockchain Verification"
            )

            if is_flagged:

                st.error(
                    "⚠️ PRODUCT FLAGGED"
                )

                st.write(
                    "Reason:",
                    flag_reason
                )

            else:

                st.success(
                    "Product is not flagged "
                    "in the blockchain record."
            )

            # -------------------------------
            # AI ANALYSIS
            # -------------------------------

            st.divider()

            st.subheader(
                "🤖 AI Risk Analysis"
            )

            analysis = ai_risk_analysis(
                history
            )

            risk = analysis["risk"]

            status = analysis["status"]

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "AI Risk Score",
                    f"{risk}/100"
                )

                st.progress(
                    risk / 100
                )

            with col2:

                st.metric(
                    "AI Risk Status",
                    status
                )

            for detail in analysis["details"]:

                st.write(
                    "•",
                    detail
                )

            # -------------------------------
            # FINAL PRODUCT RESULT
            # -------------------------------

            st.divider()

            if is_flagged:

                st.error(
                    "⚠️ Product has a "
                    "blockchain counterfeit flag."
                )

            elif risk >= 60:

                st.warning(
                    "⚠️ AI detected high-risk "
                    "custody patterns."
                )

            else:

                st.info(
                    "No high-risk pattern "
                    "detected by AI."
                )

            # -------------------------------
            # CUSTODY TIMELINE
            # -------------------------------

            st.divider()

            st.subheader(
                "📍 Custody Chain Timeline"
            )

            for idx, record in enumerate(history):

                try:

                    stage_id = int(record[0])

                    location = str(record[1])

                    verification_hash = str(
                        record[2]
                    )

                    recorded_by = str(
                        record[3]
                    )

                    timestamp = int(
                        record[4]
                    )

                    if (
                        stage_id < 0
                        or stage_id >= len(stages)
                    ):

                        stage_name = (
                            "Unknown Stage"
                        )

                    else:

                        stage_name = stages[
                            stage_id
                        ]

                    formatted_time = (
                        datetime.fromtimestamp(
                            timestamp
                        ).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )

                    with st.expander(
                        f"{idx + 1}. {stage_name}",
                        expanded=True
                    ):

                        st.write(
                            "**Location:**",
                            location
                        )

                        st.write(
                            "**Recorded By:**",
                            recorded_by
                        )

                        st.write(
                            "**Timestamp:**",
                            formatted_time
                        )

                        st.write(
                            "**Verification Hash:**"
                        )

                        st.code(
                            verification_hash
                        )

                except Exception as error:

                    st.warning(
                        f"Could not display "
                        f"history record: {error}"
                    )

        except Exception as error:

            st.error(
                "Blockchain query failed."
            )

            st.exception(
                error
            )


# -------------------------------
# FOOTER
# -------------------------------

st.divider()

st.caption(
    "ProvenanceChain AI | "
    "Blockchain + Machine Learning"
)
