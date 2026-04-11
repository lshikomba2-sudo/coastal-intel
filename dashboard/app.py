import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = "database/properties.db"

try:
    from database.seed_on_startup import ensure_data
    ensure_data()
except:
    pass

st.set_page_config(page_title="Coastal Intel", layout="wide")
st.title("Coastal Property Intelligence - Namibia")

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM listings", conn)
    conn.close()
    return df

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

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Average Rental Price by Area")
    rentals = df[df["listing_type"] == "to-rent"].groupby("location")["price"].mean().reset_index()
    rentals.columns = ["Area", "Avg Rental (N$)"]
    rentals = rentals.sort_values("Avg Rental (N$)", ascending=False)
    fig1 = px.bar(rentals, x="Area", y="Avg Rental (N$)", color="Area",
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    st.subheader("Average Sale Price by Area")
    sales = df[df["listing_type"] == "for-sale"].groupby("location")["price"].mean().reset_index()
    sales.columns = ["Area", "Avg Sale Price (N$)"]
    sales = sales.sort_values("Avg Sale Price (N$)", ascending=False)
    fig2 = px.bar(sales, x="Area", y="Avg Sale Price (N$)", color="Area",
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.subheader("Price Distribution - Rentals vs Sales")
fig3 = px.box(df[df["price"] > 0], x="listing_type", y="price", color="listing_type",
              labels={"listing_type": "Type", "price": "Price (N$)"},
              color_discrete_sequence=["#2ecc71", "#3498db"])
st.plotly_chart(fig3, use_container_width=True)

st.divider()

st.subheader("Airbnb Yield Intelligence - Coastal Namibia")
try:
    airbnb_df = pd.read_sql_query("SELECT * FROM airbnb_listings", 
                                   sqlite3.connect(DB_PATH))
    if not airbnb_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        lang = airbnb_df[airbnb_df["area"] == "Langstrand"]
        col1.metric("Langstrand Avg/Night", f"N${lang['price_per_night'].mean():,.0f}")
        col2.metric("Langstrand Min/Night", f"N${lang['price_per_night'].min():,.0f}")
        col3.metric("Langstrand Max/Night", f"N${lang['price_per_night'].max():,.0f}")
        col4.metric("Listings Tracked", len(airbnb_df))

        airbnb_summary = airbnb_df.groupby("area").agg(
            avg_price=("price_per_night", "mean"),
            min_price=("price_per_night", "min"),
            max_price=("price_per_night", "max"),
            listings=("price_per_night", "count"),
            avg_rating=("rating", "mean")
        ).reset_index().round(0)

        fig_airbnb = px.bar(airbnb_summary, x="area", y="avg_price", 
                            color="area",
                            title="Average Airbnb Nightly Rate by Area (N$)",
                            color_discrete_sequence=px.colors.qualitative.Set2)
        fig_airbnb.update_layout(showlegend=False)
        st.plotly_chart(fig_airbnb, use_container_width=True)

        st.subheader("Monthly Revenue Projections")
        proj_col1, proj_col2, proj_col3 = st.columns(3)
        for area, col in zip(["Langstrand", "Swakopmund", "Walvis Bay"], 
                             [proj_col1, proj_col2, proj_col3]):
            area_df = airbnb_df[airbnb_df["area"] == area]
            if not area_df.empty:
                avg = area_df["price_per_night"].mean()
                col.markdown(f"**{area}**")
                col.metric("65% occupancy", f"N${avg * 0.65 * 30:,.0f}/mo")
                col.metric("75% occupancy", f"N${avg * 0.75 * 30:,.0f}/mo")
                col.metric("85% occupancy", f"N${avg * 0.85 * 30:,.0f}/mo")
except Exception as e:
    st.info("Airbnb data loading...")

st.divider()

st.subheader("NHIS Settlement Intelligence - National")
try:
    nhis_df = pd.read_sql_query(
        "SELECT * FROM nhis_informal_settlements", 
        sqlite3.connect(DB_PATH))
    if not nhis_df.empty:
        nhis_col1, nhis_col2, nhis_col3, nhis_col4 = st.columns(4)
        nhis_col1.metric("Total Settlements", len(nhis_df))
        nhis_col2.metric("Regions Covered", nhis_df["region"].nunique())
        nhis_col3.metric("Congested", len(nhis_df[nhis_df["congestion_status"]=="Congested"]))
        nhis_col4.metric("Avg Upgrade Level", f"{nhis_df['upgrade_level'].mean():.1f}/5")

        nhis_summary = nhis_df.groupby("region").agg(
            settlements=("settlement_name", "count"),
            avg_upgrade=("upgrade_level", "mean"),
            congested=("congestion_status", lambda x: (x=="Congested").sum())
        ).reset_index().round(1)

        fig_nhis = px.bar(nhis_summary.sort_values("settlements", ascending=False),
                          x="region", y="settlements", color="avg_upgrade",
                          title="Informal Settlements by Region (colour = avg upgrade level)",
                          color_continuous_scale="RdYlGn")
        st.plotly_chart(fig_nhis, use_container_width=True)

        st.subheader("Erongo Coast Detail")
        erongo = nhis_df[nhis_df["region"] == "Erongo"][
            ["local_authority", "settlement_name", "congestion_status", 
             "bulk_services", "upgrade_level", "tenure_security"]
        ]
        st.dataframe(erongo, use_container_width=True)
except Exception as e:
    st.info("NHIS data loading...")

st.divider()

st.subheader("Price per m² by Area (Sales only)")
sales_m2 = df[(df["listing_type"] == "for-sale") & (df["price_per_m2"] > 0)]
if not sales_m2.empty:
    fig4 = px.scatter(sales_m2, x="size_m2", y="price", color="location",
                      size="price_per_m2", hover_data=["title", "bedrooms", "price_per_m2"],
                      labels={"size_m2": "Size (m²)", "price": "Price (N$)"},
                      color_discrete_sequence=px.colors.qualitative.Bold)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

st.subheader("Raw Listings")
area_filter = st.multiselect("Filter by area", options=df["location"].unique(), default=df["location"].unique())
type_filter = st.radio("Listing type", ["All", "to-rent", "for-sale"], horizontal=True)

filtered = df[df["location"].isin(area_filter)]
if type_filter != "All":
    filtered = filtered[filtered["listing_type"] == type_filter]

st.dataframe(
    filtered[["title", "price", "location", "bedrooms", "bathrooms", "size_m2", "price_per_m2", "listing_type", "date_scraped"]],
    use_container_width=True
)
