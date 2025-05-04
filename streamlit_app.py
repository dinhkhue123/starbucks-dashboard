import streamlit as st
import pandas as pd

# Load the dataset (replace with actual path if needed)
df = pd.read_csv("Starbucks_Performance_Monthly_2020_2025_AdjustedByCity.csv", parse_dates=['Date'])

# Sidebar Filters
st.sidebar.title("Filter Options")

# Year filter comes first
st.sidebar.markdown("### Year Filter for Seasonal Chart")
df['Year'] = df['Date'].dt.year
year_options = sorted(df['Year'].unique())
selected_years = st.sidebar.multiselect("Select Year(s) to Compare", options=year_options, default=year_options)

# Then filter by drink category
drink_categories = st.sidebar.multiselect(
    "Select Drink Category(ies)",
    options=df['Drink_Category'].unique(),
    default=df['Drink_Category'].unique()
)

# Then by region
regions = st.sidebar.multiselect(
    "Select Region(s)",
    options=df['Region'].unique(),
    default=df['Region'].unique()
)

# Date range (optional for advanced filtering)
date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])

# Apply filters to original df (not yet narrowed)
filtered_df = df[
    (df['Year'].isin(selected_years)) &
    (df['Region'].isin(regions)) &
    (df['Drink_Category'].isin(drink_categories)) &
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1]))
]

# Extract month info for seasonal line chart
filtered_df['Month'] = filtered_df['Date'].dt.month_name()
filtered_df['Month_Num'] = filtered_df['Date'].dt.month

# Prepare data for seasonal line chart
monthly_revenue = (
    filtered_df.groupby(['Year', 'Month_Num', 'Month'])['Revenue']
    .sum()
    .reset_index()
    .sort_values(['Month_Num'])
)


# Scorecards
st.title("Starbucks Performance Dashboard")
st.subheader("Key Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    total_revenue = filtered_df['Revenue'].sum()
    st.metric("Total Revenue", f"${total_revenue:,.2f}")

with col2:
    total_units = filtered_df['Units_Sold'].sum()
    st.metric("Total Units Sold", f"{total_units:,}")

with col3:
    avg_spend = (filtered_df['Revenue'].sum() / filtered_df['Customer_Count'].sum()) if filtered_df['Customer_Count'].sum() else 0
    st.metric("Avg Spend per Customer", f"${avg_spend:.2f}")

# Visualizations
import altair as alt

st.subheader("Monthly Revenue by Year (Seasonality View)")

season_chart = alt.Chart(monthly_revenue).mark_line(point=True).encode(
    x=alt.X('Month:N', sort=[
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]),
    y='Revenue:Q',
    color='Year:N',
    tooltip=['Year', 'Month', 'Revenue']
).properties(
    width=700,
    height=400
).interactive()

st.altair_chart(season_chart)

st.subheader("Sales by Drink Category")
revenue_by_category = filtered_df.groupby("Drink_Category")["Revenue"].sum().sort_values(ascending=False)
st.bar_chart(revenue_by_category)

st.subheader("Customer Count by Region")
customer_by_region = filtered_df.groupby("Region")["Customer_Count"].sum().sort_values(ascending=False)
st.bar_chart(customer_by_region)

#st.caption("Dashboard created by your AI Python Developer ✨")

import pydeck as pdk

st.subheader("Enhanced Store Revenue Map")

# Group by store to aggregate revenue and customer count
store_map_data = (
    filtered_df.groupby(['Store_ID', 'City', 'Region', 'Latitude', 'Longitude'])
    .agg({'Revenue': 'sum', 'Customer_Count': 'sum'})
    .reset_index()
    .rename(columns={'Latitude': 'lat', 'Longitude': 'lon'})
)

# Pydeck layer with interactive bubbles
layer = pdk.Layer(
    'ScatterplotLayer',
    data=store_map_data,
    get_position='[lon, lat]',
    get_radius='Revenue / 10',  # scale radius by revenue
    get_fill_color='[30, 144, 255, 160]',
    pickable=True,
)

# Set the initial view state for the map
view_state = pdk.ViewState(
    latitude=store_map_data['lat'].mean(),
    longitude=store_map_data['lon'].mean(),
    zoom=3.5,
    pitch=0,
)

# Tooltip for hover interaction
tooltip = {
    "html": "<b>Store:</b> {Store_ID}<br/>"
            "<b>City:</b> {City}<br/>"
            "<b>Revenue:</b> ${Revenue}<br/>"
            "<b>Customers:</b> {Customer_Count}",
    "style": {"backgroundColor": "rgba(0, 0, 0, 0.7)", "color": "white"}
}

# Render the interactive map
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip=tooltip
))
