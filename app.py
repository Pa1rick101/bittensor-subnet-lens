import streamlit as st
import bittensor as bt
import plotly.express as px
import pandas as pd

# --- Config ---
st.set_page_config(
    page_title="Subnet Lens",
    page_icon="🔭",
    layout="wide"
)

st.title("🔭 Subnet Lens")
st.caption("Bittensor subnet health & analytics dashboard")

# --- Sidebar ---
netuid = st.sidebar.number_input("Subnet (netuid)", min_value=1, max_value=100, value=1)
st.sidebar.info("Start with netuid=1 (SN1 — text prompting)")

def gini(values):
    arr = sorted(values)
    n = len(arr)
    cumsum = 0
    for i, v in enumerate(arr):
        cumsum += (2 * (i + 1) - n - 1) * v
    return cumsum / (n * sum(arr)) if sum(arr) > 0 else 0


# --- Load data ---
@st.cache_resource(ttl=60)
def load_metagraph(netuid: int):
    sub = bt.subtensor()
    meta = sub.metagraph(netuid=netuid)
    return meta

with st.spinner("Fetching metagraph from mainnet..."):
    meta = load_metagraph(netuid)

st.success(f"Block: {meta.block.item()} | Miners: {len(meta.uids)}")

# --- Build dataframe ---
df = pd.DataFrame({
    "uid": meta.uids.tolist(),
    "stake": meta.S.tolist(),
    "trust": meta.T.tolist(),
    "rank": meta.R.tolist(),
    "emission": meta.emission.tolist(),
    "incentive": meta.I.tolist(),
})

# --- Gini Health Score ---
gini_score = gini(df["emission"].tolist())

st.subheader("Subnet Health Score")
col1, col2, col3 = st.columns(3)

col1.metric("Gini Coefficient", f"{gini_score:.3f}")
col2.metric("Miners", len(df))
col3.metric("Total Emission", f"{df['emission'].sum():.4f}")

if gini_score < 0.4:
    st.success("✅ Healthy — emissions are well distributed")
elif gini_score < 0.7:
    st.warning("⚠️ Moderate — some concentration detected")
else:
    st.error("🚨 Unhealthy — emissions are highly concentrated")

# --- Panel 1: Emission distribution ---
st.subheader("Emission Distribution")
fig1 = px.bar(
    df.sort_values("emission", ascending=False),
    x="uid", y="emission",
    labels={"uid": "Miner UID", "emission": "Emission"},
    color="emission",
    color_continuous_scale="Teal"
)
st.plotly_chart(fig1, use_container_width=True)

# --- Panel 2: Trust vs Stake ---
st.subheader("Trust vs Stake")
fig2 = px.scatter(
    df, x="stake", y="trust",
    hover_data=["uid", "emission"],
    labels={"stake": "Stake", "trust": "Trust"},
    color="emission",
    color_continuous_scale="Bluered"
)
st.plotly_chart(fig2, use_container_width=True)

# --- Panel 3: Raw table ---
st.subheader("Raw Metagraph Data")
st.dataframe(df.sort_values("emission", ascending=False), use_container_width=True)