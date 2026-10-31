"""A beginner-friendly Streamlit dashboard for fictional crime records."""

import calendar
import html
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st


st.set_page_config(
    page_title="Crime Data Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path(__file__).parent / "crime_data.csv"
REQUIRED_COLUMNS = [
    "Crime_ID",
    "City",
    "Crime_Type",
    "Date",
    "Area",
    "Time_Period",
    "Record_Status",
]


st.markdown(
    """
    <style>
    .stApp { background-color: #f4f7fb; color: #17243a; }
    [data-testid="stSidebar"] { background-color: #14243a; }
    [data-testid="stSidebar"] * { color: #f3f6fb; }
    [data-testid="stSidebar"] [data-baseweb="select"] * { color: #17243a; }
    .block-container { padding-top: 1.8rem; padding-bottom: 2rem; }
    .page-title { color: #14243a; font-size: 2.15rem; font-weight: 750; margin-bottom: 0.15rem; }
    .page-subtitle { color: #61718a; margin-bottom: 1.4rem; }
    .metric-card {
        background: #ffffff; border: 1px solid #e4eaf2; border-radius: 14px;
        padding: 1rem 1.15rem; min-height: 112px; box-shadow: 0 3px 12px #20334d0b;
    }
    .metric-label { color: #65748b; font-size: 0.88rem; margin-bottom: 0.45rem; }
    .metric-value { color: #17243a; font-size: 1.65rem; font-weight: 700; overflow-wrap: anywhere; }
    div[data-testid="stDataFrame"] { border: 1px solid #e4eaf2; border-radius: 10px; }
    @media (max-width: 700px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        .page-title { font-size: 1.7rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_source(uploaded_file):
    """Read the selected CSV, or use the sample file supplied with the project."""
    try:
        if uploaded_file is not None:
            return pd.read_csv(uploaded_file), uploaded_file.name
        return pd.read_csv(DATA_FILE), DATA_FILE.name
    except (OSError, UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as error:
        st.error(f"Could not read the CSV file: {error}")
        st.stop()


def clean_records(source):
    """Validate columns and clean missing, invalid, and duplicate records."""
    source.columns = [str(column).strip() for column in source.columns]
    normalized_columns = [column.casefold() for column in source.columns]

    if len(normalized_columns) != len(set(normalized_columns)):
        st.error("The CSV contains duplicate column names. Rename them and upload it again.")
        st.stop()

    column_lookup = dict(zip(normalized_columns, source.columns))
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column.casefold() not in column_lookup
    ]
    if missing_columns:
        st.error(
            "The CSV is missing required columns: "
            + ", ".join(missing_columns)
            + ". Please upload a CSV with the required project columns."
        )
        st.stop()

    source = source.rename(
        columns={
            column_lookup[column.casefold()]: column
            for column in REQUIRED_COLUMNS
        }
    )
    records = source[REQUIRED_COLUMNS].copy()
    original_count = len(records)

    for column in REQUIRED_COLUMNS:
        if column != "Date":
            records[column] = records[column].astype("string").str.strip()
            records[column] = records[column].replace("", pd.NA)
    records["Date"] = pd.to_datetime(records["Date"], errors="coerce")
    invalid_date_count = int(records["Date"].isna().sum())
    critical_columns = ["Crime_ID", "City", "Crime_Type", "Date"]
    missing_critical_count = int(records[critical_columns].isna().any(axis=1).sum())
    records = records.dropna(subset=critical_columns)

    optional_columns = ["Area", "Time_Period", "Record_Status"]
    missing_optional_count = int(records[optional_columns].isna().sum().sum())
    records[optional_columns] = records[optional_columns].fillna("Unknown")

    duplicate_count = int(records.duplicated(subset=["Crime_ID"]).sum())
    records = records.drop_duplicates(subset=["Crime_ID"], keep="first").copy()
    records["Year"] = records["Date"].dt.year
    records["Month"] = records["Date"].dt.month
    records["Month_Name"] = records["Date"].dt.month_name()
    records["Month_Start"] = records["Date"].dt.to_period("M").dt.to_timestamp()

    cleaning_summary = {
        "original": original_count,
        "removed": original_count - len(records),
        "invalid_dates": invalid_date_count,
        "missing_critical": missing_critical_count,
        "missing_optional": missing_optional_count,
        "duplicates": duplicate_count,
    }
    if records.empty:
        st.error("No valid records remain after cleaning. Check the required fields and dates.")
        st.stop()
    return records, cleaning_summary


def metric_card(label, value):
    """Display a compact dashboard summary card."""
    st.markdown(
        (
            '<div class="metric-card">'
            f'<div class="metric-label">{html.escape(str(label))}</div>'
            f'<div class="metric-value">{html.escape(str(value))}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def show_page_heading(title, subtitle):
    st.markdown(f'<div class="page-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="page-subtitle">{html.escape(subtitle)}</div>',
        unsafe_allow_html=True,
    )


def show_chart(figure):
    st.pyplot(figure, width="stretch")
    plt.close(figure)


def filtered_records(records):
    """Apply the optional sidebar filters and return the matching rows."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter records")
    cities = st.sidebar.multiselect("City", sorted(records["City"].unique()))
    crime_types = st.sidebar.multiselect(
        "Crime type", sorted(records["Crime_Type"].unique())
    )
    years = st.sidebar.multiselect("Year", sorted(records["Year"].unique()))
    months = st.sidebar.multiselect(
        "Month",
        list(range(1, 13)),
        format_func=lambda month: calendar.month_name[month],
    )
    min_date = records["Date"].min().date()
    max_date = records["Date"].max().date()
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    selected = records.copy()
    if cities:
        selected = selected[selected["City"].isin(cities)]
    if crime_types:
        selected = selected[selected["Crime_Type"].isin(crime_types)]
    if years:
        selected = selected[selected["Year"].isin(years)]
    if months:
        selected = selected[selected["Month"].isin(months)]
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        selected = selected[
            selected["Date"].dt.date.between(start_date, end_date)
        ]
    return selected


def show_dashboard(records):
    show_page_heading(
        "Crime Data Overview",
        "Explore high-level statistics from the fictional sample dataset.",
    )
    most_common = records["Crime_Type"].mode().iloc[0] if not records.empty else "—"
    columns = st.columns(4)
    with columns[0]:
        metric_card("Crime records", f"{len(records):,}")
    with columns[1]:
        metric_card("Cities represented", records["City"].nunique())
    with columns[2]:
        metric_card("Most common category", most_common)
    with columns[3]:
        year_count = records["Year"].nunique()
        metric_card("Years represented", year_count)

    if records.empty:
        st.info("No records match the selected filters. Adjust the filters to see charts.")
        return

    st.markdown("### Year-wise crime statistics")
    yearly = records.groupby("Year").size().rename("Crime records").reset_index()
    figure, axis = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=yearly, x="Year", y="Crime records", marker="o", ax=axis, color="#2878b5")
    axis.set(title="Crime records by year", xlabel="Year", ylabel="Records")
    axis.set_xticks(yearly["Year"].tolist())
    show_chart(figure)

    st.markdown("### Most reported crime categories")
    category_counts = records["Crime_Type"].value_counts().rename_axis("Crime type").reset_index(name="Records")
    figure, axis = plt.subplots(figsize=(10, 4))
    sns.barplot(data=category_counts, x="Crime type", y="Records", hue="Crime type", legend=False, ax=axis, palette="Blues_r")
    axis.set(title="Crime records by category", xlabel="", ylabel="Records")
    axis.tick_params(axis="x", rotation=25)
    show_chart(figure)


def show_analysis(records):
    show_page_heading(
        "Crime Analysis",
        "Compare crime categories, cities, years, and monthly reporting trends.",
    )
    if records.empty:
        st.info("No records match the selected filters. Adjust the filters to see analysis.")
        return

    category_counts = records["Crime_Type"].value_counts().rename_axis("Crime type").reset_index(name="Records")
    city_counts = records["City"].value_counts().rename_axis("City").reset_index(name="Records")
    yearly = records.groupby("Year").size().rename("Crime records").reset_index()
    monthly = records.groupby("Month_Start").size().rename("Crime records").reset_index()

    first, second = st.columns(2)
    with first:
        st.markdown("### Crime category comparison")
        figure, axis = plt.subplots(figsize=(8, 4.5))
        sns.barplot(data=category_counts, x="Records", y="Crime type", hue="Crime type", legend=False, ax=axis, palette="Blues_r")
        axis.set(xlabel="Records", ylabel="", title="Records by crime category")
        show_chart(figure)
    with second:
        st.markdown("### Category distribution")
        pie_data = category_counts.head(5).copy()
        if len(category_counts) > 5:
            pie_data.loc[len(pie_data)] = ["Other categories", category_counts.iloc[5:]["Records"].sum()]
        figure, axis = plt.subplots(figsize=(8, 4.5))
        axis.pie(
            pie_data["Records"],
            labels=pie_data["Crime type"],
            autopct="%1.1f%%",
            startangle=90,
            colors=sns.color_palette("Set2", len(pie_data)),
            wedgeprops={"linewidth": 1, "edgecolor": "white"},
        )
        axis.set_title("Share of reported categories")
        show_chart(figure)

    third, fourth = st.columns(2)
    with third:
        st.markdown("### City-wise crime statistics")
        top_cities = city_counts.head(10)
        figure, axis = plt.subplots(figsize=(8, 4.5))
        sns.barplot(data=top_cities, x="Records", y="City", hue="City", legend=False, ax=axis, palette="crest")
        axis.set(xlabel="Records", ylabel="", title="Top 10 cities by record count")
        show_chart(figure)
    with fourth:
        st.markdown("### Year-to-year comparison")
        figure, axis = plt.subplots(figsize=(8, 4.5))
        sns.barplot(data=yearly, x="Year", y="Crime records", hue="Year", legend=False, ax=axis, palette="Blues")
        axis.set(title="Records by year", xlabel="Year", ylabel="Records")
        show_chart(figure)

    st.markdown("### Monthly crime trends")
    figure, axis = plt.subplots(figsize=(11, 4))
    sns.lineplot(data=monthly, x="Month_Start", y="Crime records", marker="o", ax=axis, color="#2878b5")
    axis.set(title="Reported records per month", xlabel="Month", ylabel="Records")
    figure.autofmt_xdate()
    show_chart(figure)


def show_records(records):
    show_page_heading(
        "Crime Records",
        "Review the records that match your sidebar filters and download them as a CSV.",
    )
    st.caption(f"{len(records):,} record(s) match the current filters.")
    display_columns = REQUIRED_COLUMNS
    display_data = records[display_columns].copy()
    display_data["Date"] = display_data["Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display_data, width="stretch", hide_index=True)

    csv_bytes = display_data.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered report",
        data=csv_bytes,
        file_name="filtered_crime_report.csv",
        mime="text/csv",
        width="stretch",
    )


def show_data_management(cleaning_summary, source_name):
    show_page_heading(
        "Data Management",
        "Upload a CSV to explore your own records, or return to the supplied fictional sample.",
    )
    st.info(
        "This dashboard contains fictional sample data for educational use only. "
        "It does not make predictions or identify people."
    )
    st.markdown(f"**Current data source:** {html.escape(source_name)}")
    st.markdown("### Data cleaning summary")
    st.write(f"Rows read: **{cleaning_summary['original']:,}**")
    st.write(f"Rows removed as invalid or duplicate: **{cleaning_summary['removed']:,}**")
    st.write(f"Rows with missing required fields: **{cleaning_summary['missing_critical']:,}**")
    st.write(f"Rows with missing or invalid dates: **{cleaning_summary['invalid_dates']:,}**")
    st.write(f"Missing optional field values filled as “Unknown”: **{cleaning_summary['missing_optional']:,}**")
    st.write(f"Duplicate crime IDs removed: **{cleaning_summary['duplicates']:,}**")
    st.markdown("### Required CSV columns")
    st.code(", ".join(REQUIRED_COLUMNS), language=None)
    st.caption("Upload a CSV using the control in the sidebar. The supplied sample is restored by clearing the upload.")


st.sidebar.title("Crime Data Analysis")
st.sidebar.caption("Fictional educational sample")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Crime Analysis", "Crime Records", "Data Management"],
)
uploaded_file = st.sidebar.file_uploader(
    "Upload a CSV file",
    type=["csv"],
    help="The uploaded CSV must include all seven required project columns.",
)

source_data, source_name = read_source(uploaded_file)
all_records, cleaning_summary = clean_records(source_data)
selected_records = filtered_records(all_records)

if page == "Dashboard":
    show_dashboard(selected_records)
elif page == "Crime Analysis":
    show_analysis(selected_records)
elif page == "Crime Records":
    show_records(selected_records)
else:
    show_data_management(cleaning_summary, source_name)
