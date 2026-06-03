import os
import sqlite3
import sys
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from ai_tools import render_ai_tools

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = "database/properties.db"
ACCENT = "#1D9E75"

try:
    from database.seed_on_startup import ensure_data
    ensure_data()
except:
    pass

st.set_page_config(page_title="Coastal Intel", layout="wide")

st.markdown(
    f"""
    <style>
    .stApp {{
        background: #ffffff;
    }}
    h1, h2, h3 {{
        color: #12231E;
    }}
    [data-testid="stMetric"] {{
        background: #ffffff;
        border: 1px solid #E6EEE9;
        border-radius: 8px;
        padding: 0.9rem;
    }}
    [data-testid="stMetricLabel"] {{
        color: #49645B;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.4rem;
        border-bottom: 1px solid #E6EEE9;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0;
        color: #34544A;
    }}
    .stTabs [aria-selected="true"] {{
        color: {ACCENT};
        border-bottom: 3px solid {ACCENT};
    }}
    section[data-testid="stSidebar"] {{
        background: #F8FBF9;
        border-right: 1px solid #E6EEE9;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM listings", conn)
    conn.close()
    return df


@st.cache_data
def load_airbnb_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM airbnb_listings", conn)
    conn.close()
    return df


@st.cache_data
def load_nhis_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM nhis_informal_settlements", conn)
    conn.close()
    return df


def style_chart(fig):
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_color="#12231E",
        margin=dict(l=20, r=20, t=55, b=20),
    )
    return fig


with st.sidebar:
    st.markdown(
        f"<h2 style='color:{ACCENT}; margin-bottom:0;'>Exokino</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Coastal Property Intelligence")
    st.divider()
    st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.link_button("NHIS Namibia", "https://www.nhis.org.na")
    st.link_button("Property24 Namibia", "https://www.property24.co.na")
    if st.button("Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()


st.title("Coastal Property Intelligence - Namibia")

df = load_data()

if df.empty:
    st.warning("No data yet. Run the scraper first.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Listings", len(df))
col2.metric("Areas Covered", df["location"].nunique())
col3.metric("Avg Rental", f"N${df[df['listing_type']=='to-rent']['price'].mean():,.0f}")
col4.metric("Avg Sale Price", f"N${df[df['listing_type']=='for-sale']['price'].mean():,.0f}")

st.divider()

market_tab, airbnb_tab, nhis_tab, ai_tab = st.tabs([
    "Market Intelligence",
    "Airbnb Yields",
    "NHIS Intelligence",
    "AI Deal Engine",
])

with market_tab:
    st.subheader("Property24 Market Intelligence")

    col_left, col_right = st.columns(2)
    with col_left:
        rentals = df[df["listing_type"] == "to-rent"].groupby("location")["price"].mean().reset_index()
        rentals.columns = ["Area", "Avg Rental (N$)"]
        rentals = rentals.sort_values("Avg Rental (N$)", ascending=False)
        fig_rentals = px.bar(
            rentals,
            x="Area",
            y="Avg Rental (N$)",
            color_discrete_sequence=[ACCENT],
            title="Average Rental Price by Area",
        )
        st.plotly_chart(style_chart(fig_rentals), use_container_width=True)

    with col_right:
        sales = df[df["listing_type"] == "for-sale"].groupby("location")["price"].mean().reset_index()
        sales.columns = ["Area", "Avg Sale Price (N$)"]
        sales = sales.sort_values("Avg Sale Price (N$)", ascending=False)
        fig_sales = px.bar(
            sales,
            x="Area",
            y="Avg Sale Price (N$)",
            color_discrete_sequence=["#34544A"],
            title="Average Sale Price by Area",
        )
        st.plotly_chart(style_chart(fig_sales), use_container_width=True)

    fig_distribution = px.box(
        df[df["price"] > 0],
        x="listing_type",
        y="price",
        color="listing_type",
        labels={"listing_type": "Type", "price": "Price (N$)"},
        color_discrete_sequence=[ACCENT, "#34544A"],
        title="Price Distribution - Rentals vs Sales",
    )
    st.plotly_chart(style_chart(fig_distribution), use_container_width=True)

    sales_m2 = df[(df["listing_type"] == "for-sale") & (df["price_per_m2"] > 0)]
    if not sales_m2.empty:
        fig_m2 = px.scatter(
            sales_m2,
            x="size_m2",
            y="price",
            color="location",
            size="price_per_m2",
            hover_data=["title", "bedrooms", "price_per_m2"],
            labels={"size_m2": "Size (m2)", "price": "Price (N$)"},
            title="Price per m2 by Area - Sales Only",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(style_chart(fig_m2), use_container_width=True)

    st.subheader("Raw Listings")
    area_filter = st.multiselect(
        "Filter by area",
        options=df["location"].unique(),
        default=df["location"].unique(),
    )
    type_filter = st.radio("Listing type", ["All", "to-rent", "for-sale"], horizontal=True)

    filtered = df[df["location"].isin(area_filter)]
    if type_filter != "All":
        filtered = filtered[filtered["listing_type"] == type_filter]

    st.dataframe(
        filtered[[
            "title",
            "price",
            "location",
            "bedrooms",
            "bathrooms",
            "size_m2",
            "price_per_m2",
            "listing_type",
            "date_scraped",
        ]],
        use_container_width=True,
    )

with airbnb_tab:
    st.subheader("Airbnb Yield Intelligence")
    try:
        airbnb_df = load_airbnb_data()
        if airbnb_df.empty:
            st.info("Airbnb data loading...")
        else:
            airbnb_summary = airbnb_df.groupby("area").agg(
                avg_price=("price_per_night", "mean"),
                min_price=("price_per_night", "min"),
                max_price=("price_per_night", "max"),
                listings=("price_per_night", "count"),
                avg_rating=("rating", "mean"),
            ).reset_index().round(0)

            fig_airbnb = px.bar(
                airbnb_summary,
                x="area",
                y="avg_price",
                color_discrete_sequence=[ACCENT],
                title="Average Airbnb Nightly Rate by Area (N$)",
            )
            st.plotly_chart(style_chart(fig_airbnb), use_container_width=True)

            st.subheader("Monthly Revenue Projections")
            projection_areas = ["Langstrand", "Swakopmund", "Walvis Bay"]
            proj_cols = st.columns(len(projection_areas))
            for area, col in zip(projection_areas, proj_cols):
                area_df = airbnb_df[airbnb_df["area"] == area]
                if not area_df.empty:
                    avg = area_df["price_per_night"].mean()
                    col.markdown(f"**{area}**")
                    col.metric("65% occupancy", f"N${avg * 0.65 * 30:,.0f}/mo")
                    col.metric("75% occupancy", f"N${avg * 0.75 * 30:,.0f}/mo")
                    col.metric("85% occupancy", f"N${avg * 0.85 * 30:,.0f}/mo")

            st.subheader("Langstrand Breakdown")
            lang = airbnb_df[airbnb_df["area"] == "Langstrand"]
            if lang.empty:
                st.info("No Langstrand Airbnb records yet.")
            else:
                lang_col1, lang_col2, lang_col3, lang_col4 = st.columns(4)
                lang_col1.metric("Avg/Night", f"N${lang['price_per_night'].mean():,.0f}")
                lang_col2.metric("Min/Night", f"N${lang['price_per_night'].min():,.0f}")
                lang_col3.metric("Max/Night", f"N${lang['price_per_night'].max():,.0f}")
                lang_col4.metric("Listings Tracked", len(lang))
                st.dataframe(lang, use_container_width=True)
    except Exception:
        st.info("Airbnb data loading...")

with nhis_tab:
    st.subheader("NHIS Settlement Intelligence")
    try:
        nhis_df = load_nhis_data()
        if nhis_df.empty:
            st.info("NHIS data loading...")
        else:
            nhis_col1, nhis_col2, nhis_col3, nhis_col4 = st.columns(4)
            nhis_col1.metric("Total Settlements", len(nhis_df))
            nhis_col2.metric("Regions Covered", nhis_df["region"].nunique())
            nhis_col3.metric("Congested", len(nhis_df[nhis_df["congestion_status"] == "Congested"]))
            nhis_col4.metric("Avg Upgrade Level", f"{nhis_df['upgrade_level'].mean():.1f}/5")

            nhis_summary = nhis_df.groupby("region").agg(
                settlements=("settlement_name", "count"),
                avg_upgrade=("upgrade_level", "mean"),
                congested=("congestion_status", lambda x: (x == "Congested").sum()),
            ).reset_index().round(1)

            fig_nhis = px.bar(
                nhis_summary.sort_values("settlements", ascending=False),
                x="region",
                y="settlements",
                color="avg_upgrade",
                title="Informal Settlements by Region",
                color_continuous_scale=["#E6F5EF", ACCENT],
            )
            st.plotly_chart(style_chart(fig_nhis), use_container_width=True)

            st.subheader("Erongo Coast Detail")
            erongo = nhis_df[nhis_df["region"] == "Erongo"][[
                "local_authority",
                "settlement_name",
                "congestion_status",
                "bulk_services",
                "upgrade_level",
                "tenure_security",
            ]]
            st.dataframe(erongo, use_container_width=True)
    except Exception:
        st.info("NHIS data loading...")

with ai_tab:
    render_ai_tools()
