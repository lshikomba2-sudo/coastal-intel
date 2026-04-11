import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

DB_PATH = "database/properties.db"

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
