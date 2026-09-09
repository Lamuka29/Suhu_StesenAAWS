import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import calendar
import io
import streamlit as st

# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Temperature Analysis",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ Temperature Data Analysis")
st.caption("Pemprosesan, Quality Control dan Analisis Data Suhu Harian")

# ============================================================
# MONTHS
# ============================================================
months = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

# ============================================================
# GRAPH SETTINGS
# ============================================================
TEMP_MIN = 0
TEMP_MAX = 40
FIG_WIDTH = 14
FIG_HEIGHT = 8

# ============================================================
# FILE UPLOAD
# ============================================================
uploaded_files = st.file_uploader(
    "📁 Upload Excel file data suhu mengikut stesen AAWS",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("Sila upload sekurang-kurangnya satu fail Excel.")
    st.markdown(
        """
        **Format data yang diperlukan:**
        - Sheet dinamakan mengikut tahun, contoh `2016`, `2017`, ..., `2025`
        - Header berada pada baris ke-7 Excel
        - Column A = `hari`
        - Column B:M = `Jan` hingga `Dec`
        - Nilai suhu dalam °C
        """
    )
    st.stop()

# ============================================================
# DETECT AVAILABLE YEARS
# ============================================================
def get_available_years(uploaded_file):
    try:
        file_bytes = uploaded_file.getvalue()
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        engine = "xlrd" if ext == ".xls" else "openpyxl"

        excel_file = pd.ExcelFile(
            io.BytesIO(file_bytes),
            engine=engine
        )

        available_years = []
        for sheet in excel_file.sheet_names:
            try:
                year = int(str(sheet).strip())
                if 1900 <= year <= 2100:
                    available_years.append(year)
            except Exception:
                continue

        return sorted(set(available_years))

    except Exception:
        return []


all_available_years = set()
file_years = {}

for uploaded_file in uploaded_files:
    detected_years = get_available_years(uploaded_file)
    file_years[uploaded_file.name] = detected_years
    all_available_years.update(detected_years)

all_available_years = sorted(all_available_years)

if not all_available_years:
    st.error("❌ Tiada sheet tahun yang sah dijumpai dalam fail Excel.")
    st.stop()

# ============================================================
# CLIMATOLOGY PERIOD
# ============================================================
st.sidebar.subheader("📅 Climatology Period")

START_YEAR = st.sidebar.selectbox(
    "Start Year",
    all_available_years,
    index=0
)

END_YEAR = st.sidebar.selectbox(
    "End Year",
    all_available_years,
    index=len(all_available_years) - 1
)

if START_YEAR > END_YEAR:
    st.sidebar.error("Start Year mesti lebih kecil atau sama dengan End Year.")
    st.stop()

years = range(int(START_YEAR), int(END_YEAR) + 1)
YEAR_RANGE_TEXT = f"{int(START_YEAR)}–{int(END_YEAR)}"

# ============================================================
# SIDEBAR SETTINGS
# ============================================================
st.sidebar.header("⚙️ Analysis Settings")

VALID_MIN = st.sidebar.number_input(
    "Minimum valid temperature (°C)",
    value=0.0,
    step=0.1,
    help="Nilai di bawah had ini dianggap invalid."
)

VALID_MAX = st.sidebar.number_input(
    "Maximum valid temperature (°C)",
    value=40.0,
    step=0.1,
    help="Nilai di atas had ini dianggap invalid."
)

MAX_MISSING_DAYS = st.sidebar.number_input(
    "Maximum missing days",
    min_value=0,
    max_value=31,
    value=10,
    step=1
)

MAX_CONSECUTIVE_MISSING = st.sidebar.number_input(
    "Maximum consecutive missing days",
    min_value=1,
    max_value=31,
    value=4,
    step=1
)

# ============================================================
# PLOT SETTINGS
# ============================================================
st.sidebar.header("🎨 Plot Settings")

# ============================================================
# BACKGROUND
# ============================================================
BG_COLOR = st.sidebar.color_picker(
    "Background Graf",
    "#FFFFFF"
)

# ============================================================
# DEFAULT BAR COLORS — MONTHLY TEMPERATURE
# ============================================================
default_colors = [
    "#4682B4",  # Jan
    "#87CEEB",  # Feb
    "#3CB371",  # Mar
    "#32CD32",  # Apr
    "#FFD700",  # May
    "#FFA500",  # Jun
    "#FF7F50",  # Jul
    "#FF6347",  # Aug
    "#9370DB",  # Sep
    "#DA70D6",  # Oct
    "#6A5ACD",  # Nov
    "#008080"   # Dec
]

# ============================================================
# SESSION STATE
# ============================================================
if "bar_colors" not in st.session_state:
    st.session_state.bar_colors = default_colors.copy()

# ============================================================
# SELECT MONTH BAR COLOUR
# ============================================================
selected_month = st.sidebar.selectbox(
    "📊 Select Month Bar Colour",
    months,
    key="temperature_bar_month"
)

selected_index = months.index(
    selected_month
)

st.session_state.bar_colors[
    selected_index
] = st.sidebar.color_picker(
    f"{selected_month} Bar Colour",
    st.session_state.bar_colors[selected_index],
    key=f"bar_color_{selected_month}"
)

# ============================================================
# MEAN LINE
# ============================================================
LINE_COLOR = st.sidebar.color_picker(
    "Mean Line",
    "#000000"
)

# ============================================================
# MINIMUM
# ============================================================
MIN_COLOR = st.sidebar.color_picker(
    "Minimum",
    "#008000"
)

# ============================================================
# MAXIMUM
# ============================================================
MAX_COLOR = st.sidebar.color_picker(
    "Maximum",
    "#FF0000"
)
# ============================================================
# FUNCTION: MAX CONSECUTIVE MISSING
# ============================================================
def max_consecutive_missing(values):
    is_missing = values.isna()
    max_missing = 0
    current_missing = 0

    for missing in is_missing:
        if missing:
            current_missing += 1
            max_missing = max(max_missing, current_missing)
        else:
            current_missing = 0

    return max_missing


# ============================================================
# FUNCTION: READ YEAR SHEET
# ============================================================
def read_year_sheet(uploaded_file, year):
    try:
        file_bytes = uploaded_file.getvalue()
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        engine = "xlrd" if ext == ".xls" else "openpyxl"

        df = pd.read_excel(
            io.BytesIO(file_bytes),
            sheet_name=str(year),
            header=6,
            engine=engine
        )

    except Exception as e:
        return None, str(e)

    if df is None or df.empty:
        return None, "Sheet kosong."

    if df.shape[1] < 13:
        return None, (
            f"Bilangan column tidak mencukupi "
            f"({df.shape[1]} dikesan). Minimum 13 diperlukan."
        )

    df = df.iloc[:, :13].copy()

    df.columns = [
        "hari",
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    df["hari"] = pd.to_numeric(df["hari"], errors="coerce")
    df = df[df["hari"].between(1, 31)].copy()

    for month in months:
        df[month] = pd.to_numeric(
            df[month],
            errors="coerce"
        )

        invalid = (
            (df[month] < VALID_MIN) |
            (df[month] > VALID_MAX)
        )

        df.loc[invalid, month] = np.nan

    df["Year"] = int(year)

    return df, None


# ============================================================
# FUNCTION: ANALYZE ONE FILE
# ============================================================
def analyze_file(uploaded_file):
    file_name = os.path.splitext(uploaded_file.name)[0]
    original_file_name = uploaded_file.name

    daily_results = []
    read_errors = []

    for year in years:
        df, error = read_year_sheet(uploaded_file, year)

        if df is not None:
            daily_results.append(df)
        else:
            read_errors.append({
                "Year": int(year),
                "Error": error
            })

    if not daily_results:
        return {
            "success": False,
            "file_name": file_name,
            "original_file_name": original_file_name,
            "error": "Tiada sheet tahun berjaya dibaca."
        }

    all_daily = pd.concat(
        daily_results,
        ignore_index=True
    )

    # --------------------------------------------------------
    # MONTHLY MEAN TEMPERATURE
    # --------------------------------------------------------
    available_years = sorted(
        all_daily["Year"].unique()
    )

    yearly_monthly_mean = pd.DataFrame(
        index=available_years,
        columns=months,
        dtype=float
    )

    monthly_missing_count = pd.DataFrame(
        index=available_years,
        columns=months,
        dtype=float
    )

    monthly_valid_count = pd.DataFrame(
        index=available_years,
        columns=months,
        dtype=float
    )

    monthly_max_consecutive_missing = pd.DataFrame(
        index=available_years,
        columns=months,
        dtype=float
    )

    monthly_qc_status = pd.DataFrame(
        index=available_years,
        columns=months,
        dtype=object
    )

    for year in available_years:
        year_data = all_daily[
            all_daily["Year"] == year
        ]

        for month in months:
            month_index = months.index(month) + 1

            days_expected = calendar.monthrange(
                int(year),
                month_index
            )[1]

            values = (
                year_data[month]
                .iloc[:days_expected]
                .copy()
            )

            valid_values = values[
                values.notna() &
                values.between(VALID_MIN, VALID_MAX)
            ]

            valid_count = len(valid_values)
            missing_count = days_expected - valid_count
            max_consecutive = max_consecutive_missing(values)

            monthly_valid_count.loc[
                year, month
            ] = valid_count

            monthly_missing_count.loc[
                year, month
            ] = missing_count

            monthly_max_consecutive_missing.loc[
                year, month
            ] = max_consecutive

            if (
                missing_count <= MAX_MISSING_DAYS
                and
                max_consecutive <= MAX_CONSECUTIVE_MISSING
            ):
                yearly_monthly_mean.loc[
                    year, month
                ] = valid_values.mean()

                monthly_qc_status.loc[
                    year, month
                ] = "ACCEPT"

            else:
                yearly_monthly_mean.loc[
                    year, month
                ] = np.nan

                if missing_count > MAX_MISSING_DAYS:
                    monthly_qc_status.loc[
                        year, month
                    ] = (
                        f"REJECT: >{MAX_MISSING_DAYS} MISSING"
                    )
                elif max_consecutive > MAX_CONSECUTIVE_MISSING:
                    monthly_qc_status.loc[
                        year, month
                    ] = (
                        f"REJECT: >{MAX_CONSECUTIVE_MISSING} "
                        f"CONSECUTIVE MISSING"
                    )
                else:
                    monthly_qc_status.loc[
                        year, month
                    ] = "REJECT"

    # --------------------------------------------------------
    # CLIMATOLOGICAL MONTHLY MEAN
    # --------------------------------------------------------
    climatological_monthly_mean = (
        yearly_monthly_mean
        .mean(axis=0, skipna=True)
        .reindex(months)
    )

    # --------------------------------------------------------
    # YEARLY MEAN
    # --------------------------------------------------------
    yearly_mean = (
        yearly_monthly_mean
        .mean(axis=1, skipna=True)
    )

    # --------------------------------------------------------
    # EXTREME DAILY TEMPERATURES
    # --------------------------------------------------------
    records = []

    for _, row in all_daily.iterrows():
        year = int(row["Year"])
        day = int(row["hari"])

        for month in months:
            value = row[month]

            if pd.isna(value):
                continue

            if VALID_MIN <= value <= VALID_MAX:
                records.append({
                    "Year": year,
                    "Month": month,
                    "Month Number": months.index(month) + 1,
                    "Day": day,
                    "Temperature (°C)": float(value)
                })

    daily_long = pd.DataFrame(records)

    if not daily_long.empty:
        daily_long["Date"] = pd.to_datetime(
            dict(
                year=daily_long["Year"],
                month=daily_long["Month Number"],
                day=daily_long["Day"]
            ),
            errors="coerce"
        )

        max_value = daily_long["Temperature (°C)"].max()
        min_value = daily_long["Temperature (°C)"].min()

        max_records = daily_long[
            daily_long["Temperature (°C)"] == max_value
        ].copy()

        min_records = daily_long[
            daily_long["Temperature (°C)"] == min_value
        ].copy()

        max_records = max_records.sort_values("Date")
        min_records = min_records.sort_values("Date")

    else:
        max_value = np.nan
        min_value = np.nan
        max_records = pd.DataFrame()
        min_records = pd.DataFrame()

    return {
        "success": True,
        "file_name": file_name,
        "original_file_name": original_file_name,
        "all_daily": all_daily,
        "daily_long": daily_long,
        "yearly_monthly_mean": yearly_monthly_mean,
        "climatological_monthly_mean": climatological_monthly_mean,
        "yearly_mean": yearly_mean,
        "monthly_missing_count": monthly_missing_count,
        "monthly_valid_count": monthly_valid_count,
        "monthly_max_consecutive_missing": monthly_max_consecutive_missing,
        "monthly_qc_status": monthly_qc_status,
        "max_value": max_value,
        "min_value": min_value,
        "max_records": max_records,
        "min_records": min_records,
        "read_errors": read_errors
    }


# ============================================================
# PROCESS ALL FILES
# ============================================================
with st.spinner("⏳ Sedang memproses semua fail Excel..."):

    results = []
    progress_bar = st.progress(0)

    for i, uploaded_file in enumerate(uploaded_files):

        result = analyze_file(uploaded_file)
        results.append(result)

        progress_bar.progress(
            int(((i + 1) / len(uploaded_files)) * 100)
        )

    progress_bar.empty()


successful_results = [
    result for result in results
    if result.get("success", False)
]

failed_results = [
    result for result in results
    if not result.get("success", False)
]

if failed_results:
    st.warning(
        f"⚠️ {len(failed_results)} fail tidak berjaya dianalisis."
    )

    for result in failed_results:
        st.error(
            f"{result.get('original_file_name', 'Unknown')}: "
            f"{result.get('error', 'Unknown error')}"
        )

if not successful_results:
    st.stop()

# ============================================================
# TARGET YEAR
# ============================================================
available_years = sorted(
    set(
        year
        for result in successful_results
        for year in result["all_daily"]["Year"].dropna().unique()
    )
)

target_year = st.sidebar.selectbox(
    "📅 Target Year",
    available_years,
    index=len(available_years) - 1,
    key="target_year"
)

target_year = int(target_year)

# ============================================================
# CALCULATE TARGET-YEAR VALUES + ANOMALY
# ============================================================
for result in successful_results:

    yearly_monthly_mean = result["yearly_monthly_mean"]
    climatological_monthly_mean = (
        result["climatological_monthly_mean"]
    )

    if target_year in yearly_monthly_mean.index:
        temperature_target = (
            yearly_monthly_mean
            .loc[target_year]
            .reindex(months)
        )
    else:
        temperature_target = pd.Series(
            np.nan,
            index=months
        )

    # Temperature anomaly is expressed in °C,
    # not percentage.
    anomaly_c = (
        temperature_target
        - climatological_monthly_mean
    )

    result["temperature_target"] = temperature_target
    result["anomaly_c"] = anomaly_c

# ============================================================
# STATION SELECTION
# ============================================================
station_options = [
    result["file_name"]
    for result in successful_results
]

selected_station = st.sidebar.selectbox(
    "📍 Select Station",
    station_options,
    key="main_station"
)

display_results = [
    result
    for result in successful_results
    if result["file_name"] == selected_station
]

# ============================================================
# GLOBAL AUTO Y-AXIS — TEMPERATURE
# ============================================================

global_max_target = 0
global_max_mean = 0

max_target_file = None
max_target_month = None

max_mean_file = None
max_mean_month = None


for result in successful_results:

    # --------------------------------------------------------
    # TARGET YEAR TEMPERATURE
    # --------------------------------------------------------
    temperature_target = result["temperature_target"]

    if temperature_target.notna().any():

        local_max = temperature_target.max()

        if local_max > global_max_target:

            global_max_target = local_max

            max_target_file = result["original_file_name"]

            max_target_month = temperature_target.idxmax()


    # --------------------------------------------------------
    # CLIMATOLOGICAL MONTHLY MEAN
    # --------------------------------------------------------
    climatological_monthly_mean = result["climatological_monthly_mean"]

    if climatological_monthly_mean.notna().any():

        local_max = climatological_monthly_mean.max()

        if local_max > global_max_mean:

            global_max_mean = local_max

            max_mean_file = result["original_file_name"]

            max_mean_month = climatological_monthly_mean.idxmax()


# ------------------------------------------------------------
# DETERMINE GLOBAL MAXIMUM
# ------------------------------------------------------------

selected_max = max(
    global_max_target,
    global_max_mean
)

# ------------------------------------------------------------
# AUTO Y-AXIS MAXIMUM
# ------------------------------------------------------------

if selected_max > 0:

    TEMP_MAX = (int(selected_max / 5) + 1) * 5

else:

    TEMP_MAX = 40

# ============================================================
# GLOBAL AUTO Y-AXIS INFORMATION
# ============================================================

with st.expander(
    "🔎 Auto Y-Axis Information"
):

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Maximum Target-Year Monthly Mean**")
        st.write(f"Value: {global_max_target:.2f} °C")
        st.write(f"File: {max_target_file}")
        st.write(f"Month: {max_target_month}")

    with col2:
        st.write("**Maximum Climatological Monthly Mean**")
        st.write(f"Value: {global_max_mean:.2f} °C")
        st.write(f"File: {max_mean_file}")
        st.write(f"Month: {max_mean_month}")

# ============================================================
# GLOBAL SUMMARY
# ============================================================
st.success(
    f"✅ {len(successful_results)} daripada "
    f"{len(uploaded_files)} fail berjaya dianalisis."
)

st.subheader("📌 Overall Analysis Summary")

summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:
    st.metric(
        "Files Analysed",
        len(successful_results)
    )

with summary_col2:
    st.metric(
        "Target Year",
        target_year
    )

with summary_col3:
    st.metric(
        "Climatology",
        YEAR_RANGE_TEXT
    )

# ============================================================
# MAIN TABS
# ============================================================
main_tabs = st.tabs([
    "📅 Target Year",
    "📊 All Years",
    "🔄 Station Comparison",
    "🔥 Suhu Ekstrem"
])

# ============================================================
# MAIN TAB 1 — TARGET YEAR
# ============================================================
with main_tabs[0]:

    for result in display_results:

        file_name = result["file_name"]
        original_file_name = result["original_file_name"]

        all_daily = result["all_daily"]
        yearly_monthly_mean = result["yearly_monthly_mean"]
        climatological_monthly_mean = (
            result["climatological_monthly_mean"]
        )

        temperature_target = result["temperature_target"]
        anomaly_c = result["anomaly_c"]

        target_data = all_daily[
            all_daily["Year"] == target_year
        ].copy()

        # --------------------------------------------------------
        # TARGET YEAR MIN/MAX MONTHLY
        # --------------------------------------------------------
        valid_target = temperature_target.dropna()

        if len(valid_target) > 0:
            min_target_month = valid_target.idxmin()
            min_target_value = valid_target.min()

            max_target_month = valid_target.idxmax()
            max_target_value = valid_target.max()
        else:
            min_target_month = None
            min_target_value = np.nan
            max_target_month = None
            max_target_value = np.nan

        # --------------------------------------------------------
        # HEADER
        # --------------------------------------------------------
        st.divider()
        st.header(f"📁 {original_file_name}")

        # --------------------------------------------------------
        # BASIC METRICS
        # --------------------------------------------------------
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if pd.notna(min_target_value):
                st.metric(
                    f"Lowest Monthly Mean {target_year}",
                    f"{min_target_value:.2f} °C",
                    min_target_month
                )
            else:
                st.metric(
                    f"Lowest Monthly Mean {target_year}",
                    "N.A."
                )

        with c2:
            if pd.notna(max_target_value):
                st.metric(
                    f"Highest Monthly Mean {target_year}",
                    f"{max_target_value:.2f} °C",
                    max_target_month
                )
            else:
                st.metric(
                    f"Highest Monthly Mean {target_year}",
                    "N.A."
                )

        with c3:
            if not result["daily_long"].empty:
                st.metric(
                    "Absolute Minimum",
                    f"{result['min_value']:.2f} °C"
                )
            else:
                st.metric(
                    "Absolute Minimum",
                    "N.A."
                )

        with c4:
            if not result["daily_long"].empty:
                st.metric(
                    "Absolute Maximum",
                    f"{result['max_value']:.2f} °C"
                )
            else:
                st.metric(
                    "Absolute Maximum",
                    "N.A."
                )

        # --------------------------------------------------------
        # TARGET-YEAR ANALYSIS TABS
        # --------------------------------------------------------
        tabs = st.tabs([
            "📊 Monthly Temperature",
            "🔥 Heatmap",
            "📉 Anomaly",
            "📋 Statistics",
            "📦 Boxplot",
            "⚠️ QC",
            "🌡️ Temperature Extremes"
        ])

        # ========================================================
        # TAB 1 — MONTHLY TEMPERATURE
        # ========================================================
        with tabs[0]:
        
            st.subheader(
                f"Monthly Mean Temperature {target_year} vs "
                f"Climatological Mean {YEAR_RANGE_TEXT}"
            )
        
            x = np.arange(
                len(months)
            )
        
            fig, ax = plt.subplots(
                figsize=(
                    FIG_WIDTH,
                    FIG_HEIGHT
                )
            )
        
            bg_color = BG_COLOR
        
            fig.patch.set_facecolor(
                bg_color
            )
        
            ax.set_facecolor(
                bg_color
            )
        
            # ====================================================
            # BAR — TARGET YEAR
            # ====================================================
        
            ax.bar(
                x,
                temperature_target.values,
                width=0.60,
                color=st.session_state.bar_colors,
                edgecolor="black",
                linewidth=0.8,
                label=(
                    f"Monthly Mean Temperature {target_year}"
                )
            )
        
            # ====================================================
            # LINE — CLIMATOLOGICAL MEAN
            # ====================================================
        
            ax.plot(
                x,
                climatological_monthly_mean.values,
                color=LINE_COLOR,
                marker="o",
                linewidth=2.5,
                markersize=7,
                label=(
                    f"Climatological Mean "
                    f"{YEAR_RANGE_TEXT}"
                )
            )
        
            # ----------------------------------------------------
            # Mean labels
            # ----------------------------------------------------
        
            for i, value in enumerate(
                climatological_monthly_mean.values
            ):
        
                if pd.notna(value):
        
                    ax.annotate(
                        f"{value:.1f}",
                        (
                            i,
                            value
                        ),
                        xytext=(0, 10),
                        textcoords="offset points",
                        ha="center",
                        fontsize=11,
                        fontweight="bold"
                    )
        
            # ----------------------------------------------------
            # Minimum
            # ----------------------------------------------------
        
            if min_target_month is not None:
        
                min_index = months.index(
                    min_target_month
                )
        
                ax.scatter(
                    min_index,
                    min_target_value,
                    s=50,
                    color=MIN_COLOR,
                    edgecolor="black",
                    linewidth=1,
                    zorder=5,
                    label=(
                        f"Minimum {target_year}: "
                        f"{min_target_month} "
                        f"({min_target_value:.1f} °C)"
                    )
                )
        
            # ----------------------------------------------------
            # Maximum
            # ----------------------------------------------------
        
            if max_target_month is not None:
        
                max_index = months.index(
                    max_target_month
                )
        
                ax.scatter(
                    max_index,
                    max_target_value,
                    s=50,
                    color=MAX_COLOR,
                    edgecolor="black",
                    linewidth=1,
                    zorder=5,
                    label=(
                        f"Maximum {target_year}: "
                        f"{max_target_month} "
                        f"({max_target_value:.1f} °C)"
                    )
                )
        
            # ====================================================
            # TITLE
            # ====================================================
        
            ax.set_title(
                f"{file_name}\n"
                f"Monthly Mean Temperature {target_year} vs "
                f"Climatological Mean {YEAR_RANGE_TEXT}",
                fontsize=16,
                fontweight="bold"
            )
        
            ax.set_xlabel(
                "Month",
                fontsize=12
            )
        
            ax.set_ylabel(
                "Temperature (°C)",
                fontsize=12
            )
        
            ax.set_xticks(x)
        
            ax.set_xticklabels(
                months
            )
        
            # ====================================================
            # AUTO Y-AXIS
            # ====================================================
        
            ax.set_ylim(
                TEMP_MIN,
                TEMP_MAX
            )
        
            ax.grid(
                True,
                axis="y",
                linestyle="--",
                alpha=0.4
            )
        
            ax.legend(
                bbox_to_anchor=(1.02, 1),
                loc="upper left",
                fontsize=9
            )
        
            plt.tight_layout()
        
            st.pyplot(
                fig,
                use_container_width=True
            )
        
            # ====================================================
            # DOWNLOAD PLOT
            # ====================================================
        
            img_buffer = io.BytesIO()
        
            fig.savefig(
                img_buffer,
                format="png",
                dpi=300,
                bbox_inches="tight"
            )
        
            img_buffer.seek(0)
        
            st.download_button(
                "📥 Download Plot PNG",
                data=img_buffer.getvalue(),
                file_name=(
                    f"{selected_station}_monthly_temperature_"
                    f"{target_year}.png"
                ),
                mime="image/png",
                key=(
                    f"download_monthly_temperature_"
                    f"{selected_station}_{target_year}"
                )
            )
        
            # ====================================================
            # TABLE DATA
            # ====================================================
        
            plot_table = pd.DataFrame({
        
                "Month":
                    months,
        
                f"Monthly Mean {target_year} (°C)":
                    temperature_target.values,
        
                f"Climatological Mean {YEAR_RANGE_TEXT} (°C)":
                    climatological_monthly_mean.values,
        
                "Anomaly (°C)":
                    anomaly_c.values
        
            })
        
            plot_table = plot_table.round(
                2
            )
        
            st.dataframe(
                plot_table,
                use_container_width=True,
                hide_index=True
            )
        
            csv = (
                plot_table
                .to_csv(index=False)
                .encode("utf-8")
            )
        
            st.download_button(
                "📥 Download Table CSV",
                data=csv,
                file_name=(
                    f"{selected_station}_monthly_temperature_"
                    f"{target_year}.csv"
                ),
                mime="text/csv",
                key=(
                    f"download_monthly_temperature_table_"
                    f"{selected_station}_{target_year}"
                )
            )
        
            plt.close(fig)
        # ========================================================
        # TAB 2 — HEATMAP
        # ========================================================
        with tabs[1]:

            st.subheader(
                f"Monthly Mean Temperature Heatmap "
                f"{YEAR_RANGE_TEXT}"
            )

            heatmap_data = (
                yearly_monthly_mean
                .reindex(columns=months)
            )

            fig, ax = plt.subplots(
                figsize=(14, 8)
            )

            fig.patch.set_facecolor(BG_COLOR)
            ax.set_facecolor(BG_COLOR)

            plot_data = heatmap_data.copy()

            valid_values = plot_data.values[
                ~pd.isna(plot_data.values)
            ]

            if len(valid_values) > 0:
                vmin = valid_values.min()
                vmax = valid_values.max()

                if vmin == vmax:
                    vmax = vmin + 1
            else:
                vmin = 0
                vmax = 1

            im = ax.imshow(
                plot_data.values,
                aspect="auto",
                cmap="RdYlBu_r",
                vmin=vmin,
                vmax=vmax
            )

            ax.set_xticks(range(len(months)))
            ax.set_xticklabels(months)

            ax.set_yticks(
                range(len(plot_data.index))
            )
            ax.set_yticklabels(
                plot_data.index.astype(str)
            )

            # Grid
            ax.set_xticks(
                [
                    i - 0.5
                    for i in range(len(months) + 1)
                ],
                minor=True
            )

            ax.set_yticks(
                [
                    i - 0.5
                    for i in range(len(plot_data.index) + 1)
                ],
                minor=True
            )

            ax.grid(
                which="minor",
                color="white",
                linestyle="-",
                linewidth=1
            )

            ax.tick_params(
                which="minor",
                bottom=False,
                left=False
            )

            # Values
            for i in range(len(plot_data.index)):
                for j in range(len(months)):

                    value = plot_data.iloc[i, j]

                    if pd.notna(value):
                        ax.text(
                            j,
                            i,
                            f"{value:.1f}",
                            ha="center",
                            va="center",
                            fontsize=8
                        )
                    else:
                        ax.add_patch(
                            plt.Rectangle(
                                (
                                    j - 0.5,
                                    i - 0.5
                                ),
                                1,
                                1,
                                facecolor="lightgray",
                                edgecolor="white",
                                linewidth=1
                            )
                        )

                        ax.text(
                            j,
                            i,
                            "N.A.",
                            ha="center",
                            va="center",
                            fontsize=7
                        )

            cbar = fig.colorbar(
                im,
                ax=ax
            )

            cbar.set_label(
                "Mean Temperature (°C)",
                fontsize=11
            )

            ax.set_title(
                f"{file_name}\n"
                f"Monthly Mean Temperature Heatmap "
                f"{YEAR_RANGE_TEXT}",
                fontsize=16,
                fontweight="bold"
            )

            ax.set_xlabel(
                "Month",
                fontsize=12
            )

            ax.set_ylabel(
                "Year",
                fontsize=12
            )

            plt.tight_layout()
            st.pyplot(
                fig,
                use_container_width=True
            )

            img_buffer = io.BytesIO()

            fig.savefig(
                img_buffer,
                format="png",
                dpi=300,
                bbox_inches="tight"
            )

            img_buffer.seek(0)

            st.download_button(
                "📥 Download Heatmap PNG",
                data=img_buffer.getvalue(),
                file_name=(
                    f"{selected_station}_temperature_heatmap_"
                    f"{YEAR_RANGE_TEXT}.png"
                ),
                mime="image/png",
                key=(
                    f"download_temperature_heatmap_"
                    f"{selected_station}_{YEAR_RANGE_TEXT}"
                )
            )

            heatmap_table = (
                heatmap_data
                .reset_index()
                .round(2)
            )

            st.dataframe(
                heatmap_table,
                use_container_width=True,
                hide_index=True
            )

            csv = heatmap_table.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "📥 Download Heatmap Table CSV",
                data=csv,
                file_name=(
                    f"{selected_station}_temperature_heatmap_"
                    f"{YEAR_RANGE_TEXT}.csv"
                ),
                mime="text/csv",
                key=(
                    f"download_temperature_heatmap_table_"
                    f"{selected_station}_{YEAR_RANGE_TEXT}"
                )
            )

            plt.close(fig)

        # ========================================================
        # TAB 3 — ANOMALY
        # ========================================================
        with tabs[2]:

            st.subheader(
                f"Temperature Anomaly {target_year} "
                f"Relative to Climatological Mean {YEAR_RANGE_TEXT}"
            )

            fig, ax = plt.subplots(
                figsize=(14, 8)
            )

            fig.patch.set_facecolor(BG_COLOR)
            ax.set_facecolor(BG_COLOR)

            anomaly_colors = [
                (
                    "darkorange"
                    if pd.notna(value) and value >= 0
                    else "steelblue"
                    if pd.notna(value)
                    else "lightgray"
                )
                for value in anomaly_c.values
            ]

            bars = ax.bar(
                x,
                anomaly_c.values,
                width=0.60,
                color=anomaly_colors,
                edgecolor="black",
                linewidth=0.8
            )

            ax.axhline(
                0,
                color="black",
                linewidth=1
            )

            for bar, value in zip(
                bars,
                anomaly_c.values
            ):

                if pd.notna(value):

                    if value >= 0:
                        offset = 5
                        vertical = "bottom"
                    else:
                        offset = -12
                        vertical = "top"

                    ax.annotate(
                        f"{value:+.2f} °C",
                        (
                            bar.get_x()
                            + bar.get_width() / 2,
                            value
                        ),
                        xytext=(0, offset),
                        textcoords="offset points",
                        ha="center",
                        va=vertical,
                        fontsize=9
                    )

            ax.set_title(
                f"{file_name}\n"
                f"Temperature Anomaly {target_year} "
                f"Relative to {YEAR_RANGE_TEXT}",
                fontsize=16,
                fontweight="bold"
            )

            ax.set_xlabel(
                "Month",
                fontsize=12
            )

            ax.set_ylabel(
                "Temperature Anomaly (°C)",
                fontsize=12
            )

            ax.set_xticks(x)
            ax.set_xticklabels(months)

            ax.grid(
                True,
                axis="y",
                linestyle="--",
                alpha=0.4
            )

            plt.tight_layout()
            st.pyplot(
                fig,
                use_container_width=True
            )

            img_buffer = io.BytesIO()

            fig.savefig(
                img_buffer,
                format="png",
                dpi=300,
                bbox_inches="tight"
            )

            img_buffer.seek(0)

            st.download_button(
                "📥 Download Anomaly PNG",
                data=img_buffer.getvalue(),
                file_name=(
                    f"{selected_station}_temperature_anomaly_"
                    f"{target_year}.png"
                ),
                mime="image/png",
                key=(
                    f"download_temperature_anomaly_"
                    f"{selected_station}_{target_year}"
                )
            )

            anomaly_table = pd.DataFrame({
                "Month": months,
                f"Temperature {target_year} (°C)":
                    temperature_target.values,
                f"Climatological Mean {YEAR_RANGE_TEXT} (°C)":
                    climatological_monthly_mean.values,
                "Anomaly (°C)":
                    anomaly_c.values
            }).round(2)

            st.dataframe(
                anomaly_table,
                use_container_width=True,
                hide_index=True
            )

            csv = anomaly_table.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "📥 Download Anomaly Table CSV",
                data=csv,
                file_name=(
                    f"{selected_station}_temperature_anomaly_"
                    f"{target_year}.csv"
                ),
                mime="text/csv",
                key=(
                    f"download_temperature_anomaly_table_"
                    f"{selected_station}_{target_year}"
                )
            )

            plt.close(fig)

        # ========================================================
        # TAB 4 — STATISTICS
        # ========================================================
        with tabs[3]:

            st.subheader(
                f"📋 Temperature Statistical Analysis - "
                f"{target_year}"
            )

            rows = []

            for month in months:

                month_index = months.index(month) + 1

                days_expected = calendar.monthrange(
                    target_year,
                    month_index
                )[1]

                values = (
                    target_data[month]
                    .iloc[:days_expected]
                    .dropna()
                )

                if len(values) > 0:

                    rows.append({
                        "Month": month,
                        "Mean (°C)": values.mean(),
                        "Median (°C)": values.median(),
                        "Minimum (°C)": values.min(),
                        "Maximum (°C)": values.max(),
                        "Std Dev (°C)": (
                            values.std()
                            if len(values) > 1
                            else np.nan
                        ),
                        "Valid Days": len(values),
                        "Valid Data (%)": (
                            len(values) /
                            days_expected
                        ) * 100
                    })

                else:

                    rows.append({
                        "Month": month,
                        "Mean (°C)": np.nan,
                        "Median (°C)": np.nan,
                        "Minimum (°C)": np.nan,
                        "Maximum (°C)": np.nan,
                        "Std Dev (°C)": np.nan,
                        "Valid Days": 0,
                        "Valid Data (%)": 0
                    })

            statistics_table = (
                pd.DataFrame(rows)
                .round(2)
            )

            st.dataframe(
                statistics_table,
                use_container_width=True,
                hide_index=True
            )

            csv = statistics_table.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "📥 Download Statistics CSV",
                data=csv,
                file_name=(
                    f"{selected_station}_temperature_statistics_"
                    f"{target_year}.csv"
                ),
                mime="text/csv",
                key=(
                    f"download_temperature_statistics_"
                    f"{selected_station}_{target_year}"
                )
            )

        # ========================================================
        # TAB 5 — BOXPLOT
        # ========================================================
        with tabs[4]:

            st.subheader(
                f"Daily Temperature Distribution by Month - "
                f"{target_year}"
            )

            boxplot_data = []

            for month in months:

                month_index = months.index(month) + 1

                days_expected = calendar.monthrange(
                    target_year,
                    month_index
                )[1]

                values = (
                    target_data[month]
                    .iloc[:days_expected]
                    .dropna()
                )

                boxplot_data.append(
                    values.tolist()
                )

            if any(
                len(values) > 0
                for values in boxplot_data
            ):

                fig, ax = plt.subplots(
                    figsize=(14, 8)
                )

                fig.patch.set_facecolor(BG_COLOR)
                ax.set_facecolor(BG_COLOR)

                bp = ax.boxplot(
                    boxplot_data,
                    tick_labels=months,
                    patch_artist=True,
                    showmeans=True,
                    showfliers=False
                )

                for box in bp["boxes"]:
                    box.set(
                        facecolor="#87CEEB",
                        edgecolor="black",
                        linewidth=1
                    )

                for median in bp["medians"]:
                    median.set(
                        color="red",
                        linewidth=2
                    )

                for mean in bp["means"]:
                    mean.set(
                        marker="o",
                        markerfacecolor="black",
                        markeredgecolor="black",
                        markersize=5
                    )

                ax.set_title(
                    f"{file_name}\n"
                    f"Daily Temperature Distribution by Month - "
                    f"{target_year}",
                    fontsize=16,
                    fontweight="bold"
                )

                ax.set_xlabel(
                    "Month",
                    fontsize=12
                )

                ax.set_ylabel(
                    "Temperature (°C)",
                    fontsize=12
                )

                ax.grid(
                    True,
                    axis="y",
                    linestyle="--",
                    alpha=0.4
                )
                
                # ------------------------------------------------
                # INDIVIDUAL DATA POINTS - SIDE OF BOXPLOT
                # ------------------------------------------------
                for i, values in enumerate(boxplot_data, start=1):
                
                    if len(values) > 0:
                
                        # Titik diletakkan di sebelah kanan box
                        x_points = np.random.normal(
                            i + 0.5,
                            0.025,
                            size=len(values)
                        )
                
                        ax.scatter(
                            x_points,
                            values,
                            s=25,
                            color="black",
                            alpha=0.55,
                            edgecolors="white",
                            linewidth=0.5,
                            zorder=3
                        )
                
                plt.tight_layout()
                st.pyplot(
                    fig,
                    use_container_width=True
                )

                img_buffer = io.BytesIO()

                fig.savefig(
                    img_buffer,
                    format="png",
                    dpi=300,
                    bbox_inches="tight"
                )

                img_buffer.seek(0)

                st.download_button(
                    "📥 Download Boxplot PNG",
                    data=img_buffer.getvalue(),
                    file_name=(
                        f"{selected_station}_temperature_boxplot_"
                        f"{target_year}.png"
                    ),
                    mime="image/png",
                    key=(
                        f"download_temperature_boxplot_"
                        f"{selected_station}_{target_year}"
                    )
                )

                plt.close(fig)

            else:
                st.warning(
                    "Tiada data suhu sah untuk menghasilkan boxplot."
                )

        # ========================================================
        # TAB 6 — QUALITY CONTROL
        # ========================================================
        with tabs[5]:

            st.subheader("⚠️ Quality Control")

            st.markdown(
                f"""
                **QC Rules**
                - Suhu antara `{VALID_MIN:.1f} °C` hingga
                  `{VALID_MAX:.1f} °C` = data sah
                - Nilai di luar julat tersebut = invalid / dibuang
                - Missing days `>{MAX_MISSING_DAYS}` = bulan ditolak
                - Missing berturut-turut
                  `>{MAX_CONSECUTIVE_MISSING}` = bulan ditolak
                """
            )

            qc_tabs = st.tabs([
                "📅 Missing Count",
                "🔢 Valid Count",
                "🔁 Consecutive Missing",
                "📋 QC Status"
            ])

            with qc_tabs[0]:
                st.dataframe(
                    result["monthly_missing_count"],
                    use_container_width=True
                )

            with qc_tabs[1]:
                st.dataframe(
                    result["monthly_valid_count"],
                    use_container_width=True
                )

            with qc_tabs[2]:
                st.dataframe(
                    result["monthly_max_consecutive_missing"],
                    use_container_width=True
                )

            with qc_tabs[3]:
                st.dataframe(
                    result["monthly_qc_status"],
                    use_container_width=True
                )

        # ========================================================
        # TAB 7 — TEMPERATURE EXTREMES
        # ========================================================
        with tabs[6]:

            st.subheader(
                f"🌡️ Temperature Extremes "
                f"{YEAR_RANGE_TEXT}"
            )

            max_records = result["max_records"].copy()
            min_records = result["min_records"].copy()

            ec1, ec2 = st.columns(2)

            with ec1:

                st.markdown("### 🔥 Highest Temperature")

                if not max_records.empty:

                    highest = max_records.iloc[0]

                    st.metric(
                        "Highest Recorded Temperature",
                        f"{highest['Temperature (°C)']:.2f} °C",
                        f"{highest['Day']} {highest['Month']} "
                        f"{highest['Year']}"
                    )

                    display_max = max_records[
                        [
                            "Year",
                            "Month",
                            "Day",
                            "Date",
                            "Temperature (°C)"
                        ]
                    ].copy()

                    display_max["Date"] = (
                        display_max["Date"]
                        .dt.strftime("%d-%m-%Y")
                    )

                    st.dataframe(
                        display_max,
                        use_container_width=True,
                        hide_index=True
                    )

                    csv = display_max.to_csv(
                        index=False
                    ).encode("utf-8")

                    st.download_button(
                        "📥 Download Highest Temperature CSV",
                        data=csv,
                        file_name=(
                            f"{selected_station}_highest_temperature_"
                            f"{YEAR_RANGE_TEXT}.csv"
                        ),
                        mime="text/csv",
                        key=(
                            f"download_highest_temperature_"
                            f"{selected_station}_{YEAR_RANGE_TEXT}"
                        )
                    )

                else:
                    st.info(
                        "Tiada data suhu sah."
                    )

            with ec2:

                st.markdown("### ❄️ Lowest Temperature")

                if not min_records.empty:

                    lowest = min_records.iloc[0]

                    st.metric(
                        "Lowest Recorded Temperature",
                        f"{lowest['Temperature (°C)']:.2f} °C",
                        f"{lowest['Day']} {lowest['Month']} "
                        f"{lowest['Year']}"
                    )

                    display_min = min_records[
                        [
                            "Year",
                            "Month",
                            "Day",
                            "Date",
                            "Temperature (°C)"
                        ]
                    ].copy()

                    display_min["Date"] = (
                        display_min["Date"]
                        .dt.strftime("%d-%m-%Y")
                    )

                    st.dataframe(
                        display_min,
                        use_container_width=True,
                        hide_index=True
                    )

                    csv = display_min.to_csv(
                        index=False
                    ).encode("utf-8")

                    st.download_button(
                        "📥 Download Lowest Temperature CSV",
                        data=csv,
                        file_name=(
                            f"{selected_station}_lowest_temperature_"
                            f"{YEAR_RANGE_TEXT}.csv"
                        ),
                        mime="text/csv",
                        key=(
                            f"download_lowest_temperature_"
                            f"{selected_station}_{YEAR_RANGE_TEXT}"
                        )
                    )

                else:
                    st.info(
                        "Tiada data suhu sah."
                    )

            # ----------------------------------------------------
            # MONTHLY EXTREMES BY YEAR
            # ----------------------------------------------------
            st.divider()

            st.markdown(
                "### 📅 Minimum dan Maximum Suhu Mengikut Tahun & Bulan"
            )

            if not result["daily_long"].empty:

                monthly_extremes = (
                    result["daily_long"]
                    .groupby(
                        ["Year", "Month Number", "Month"],
                        as_index=False
                    )
                    .agg(
                        Minimum=("Temperature (°C)", "min"),
                        Maximum=("Temperature (°C)", "max")
                    )
                    .sort_values(
                        ["Year", "Month Number"]
                    )
                )

                monthly_extremes = (
                    monthly_extremes[
                        [
                            "Year",
                            "Month",
                            "Minimum",
                            "Maximum"
                        ]
                    ]
                    .round(2)
                )

                st.dataframe(
                    monthly_extremes,
                    use_container_width=True,
                    hide_index=True
                )

                csv = monthly_extremes.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    "📥 Download Monthly Extremes CSV",
                    data=csv,
                    file_name=(
                        f"{selected_station}_monthly_temperature_extremes_"
                        f"{YEAR_RANGE_TEXT}.csv"
                    ),
                    mime="text/csv",
                    key=(
                        f"download_monthly_temperature_extremes_"
                        f"{selected_station}_{YEAR_RANGE_TEXT}"
                    )
                )

# ============================================================
# MAIN TAB 2 — ALL YEARS
# ============================================================

with main_tabs[1]:

    result = display_results[0]

    st.subheader(
        f"📊 All Years Temperature Analysis "
        f"{YEAR_RANGE_TEXT}"
    )

    # ========================================================
    # DATA ASAS — SEMUA TAHUN
    # ========================================================

    yearly_mean_table = (
        result["yearly_monthly_mean"]
        .copy()
        .round(2)
    )

    yearly_mean_table.index.name = "Year"

    climatological_mean = (
        result["climatological_monthly_mean"]
        .copy()
    )

    # Pastikan ikut susunan bulan
    yearly_mean_table = yearly_mean_table[
        months
    ]

    climatological_mean = (
        climatological_mean.reindex(months)
    )

    # ========================================================
    # SUB TABS
    # ========================================================

    all_year_tabs = st.tabs([
        "📈 Monthly Temperature",
        "🔥 Heatmap",
        "📊 Anomaly",
        "📋 Statistics",
        "📦 Boxplot"
    ])


    # ========================================================
    # TAB 1 — MONTHLY TEMPERATURE
    # ========================================================

    with all_year_tabs[0]:

        st.subheader(
            "📈 Monthly Mean Temperature — All Years"
        )

        st.dataframe(
            yearly_mean_table,
            use_container_width=True
        )

        # ----------------------------------------------------
        # LINE GRAPH
        # ----------------------------------------------------

        fig, ax = plt.subplots(
            figsize=(FIG_WIDTH, FIG_HEIGHT)
        )

        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)

        for year in yearly_mean_table.index:

            values = yearly_mean_table.loc[
                year,
                months
            ]

            ax.plot(
                months,
                values,
                marker="o",
                linewidth=1.5,
                alpha=0.60,
                label=str(int(year))
            )

        # Mean keseluruhan
        ax.plot(
            months,
            climatological_mean.values,
            color=LINE_COLOR,
            marker="o",
            linewidth=3,
            label=f"Mean {YEAR_RANGE_TEXT}"
        )

        ax.set_title(
            f"{result['file_name']}\n"
            f"Monthly Mean Temperature by Year",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Month",
            fontsize=12
        )

        ax.set_ylabel(
            "Temperature (°C)",
            fontsize=12
        )

        ax.set_ylim(
            TEMP_MIN,
            TEMP_MAX
        )

        ax.grid(
            True,
            axis="y",
            linestyle="--",
            alpha=0.4
        )

        ax.legend(
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize=8
        )

        plt.xticks(
            rotation=45
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)


    # ========================================================
    # TAB 2 — HEATMAP
    # ========================================================

    with all_year_tabs[1]:

        st.subheader(
            "🔥 Heatmap Suhu Bulanan Mengikut Tahun"
        )

        heatmap_data = (
            yearly_mean_table
            .copy()
        )

        fig, ax = plt.subplots(
            figsize=(FIG_WIDTH, FIG_HEIGHT)
        )

        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)

        im = ax.imshow(
            heatmap_data.values,
            aspect="auto"
        )

        # ----------------------------------------------------
        # AXIS
        # ----------------------------------------------------

        ax.set_xticks(
            np.arange(len(months))
        )

        ax.set_xticklabels(
            months
        )

        ax.set_yticks(
            np.arange(len(heatmap_data.index))
        )

        ax.set_yticklabels(
            heatmap_data.index.astype(int)
        )

        ax.set_xlabel(
            "Month",
            fontsize=12
        )

        ax.set_ylabel(
            "Year",
            fontsize=12
        )

        ax.set_title(
            f"{result['file_name']}\n"
            f"Monthly Mean Temperature Heatmap "
            f"{YEAR_RANGE_TEXT}",
            fontsize=16,
            fontweight="bold"
        )

        # ----------------------------------------------------
        # NILAI DALAM HEATMAP
        # ----------------------------------------------------

        for i in range(
            len(heatmap_data.index)
        ):

            for j in range(
                len(months)
            ):

                value = heatmap_data.iloc[
                    i,
                    j
                ]

                if pd.notna(value):

                    ax.text(
                        j,
                        i,
                        f"{value:.1f}",
                        ha="center",
                        va="center",
                        fontsize=8
                    )

        cbar = fig.colorbar(
            im,
            ax=ax
        )

        cbar.set_label(
            "Temperature (°C)"
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)


    # ========================================================
    # TAB 3 — ANOMALY
    # ========================================================

    with all_year_tabs[2]:

        st.subheader(
            "📊 Temperature Anomaly — All Years"
        )

        # ----------------------------------------------------
        # KIRA ANOMALY
        # ----------------------------------------------------

        anomaly_data = (
            yearly_mean_table
            .subtract(
                climatological_mean,
                axis="columns"
            )
        )

        anomaly_data = (
            anomaly_data
            .round(2)
        )

        anomaly_data.index.name = "Year"

        st.dataframe(
            anomaly_data,
            use_container_width=True
        )

        # ----------------------------------------------------
        # HEATMAP ANOMALY
        # ----------------------------------------------------

        fig, ax = plt.subplots(
            figsize=(FIG_WIDTH, FIG_HEIGHT)
        )

        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)

        im = ax.imshow(
            anomaly_data.values,
            aspect="auto"
        )

        ax.set_xticks(
            np.arange(len(months))
        )

        ax.set_xticklabels(
            months
        )

        ax.set_yticks(
            np.arange(len(anomaly_data.index))
        )

        ax.set_yticklabels(
            anomaly_data.index.astype(int)
        )

        ax.set_xlabel(
            "Month",
            fontsize=12
        )

        ax.set_ylabel(
            "Year",
            fontsize=12
        )

        ax.set_title(
            f"{result['file_name']}\n"
            f"Temperature Anomaly "
            f"{YEAR_RANGE_TEXT}",
            fontsize=16,
            fontweight="bold"
        )

        # ----------------------------------------------------
        # NILAI ANOMALY
        # ----------------------------------------------------

        for i in range(
            len(anomaly_data.index)
        ):

            for j in range(
                len(months)
            ):

                value = anomaly_data.iloc[
                    i,
                    j
                ]

                if pd.notna(value):

                    ax.text(
                        j,
                        i,
                        f"{value:+.1f}",
                        ha="center",
                        va="center",
                        fontsize=8
                    )

        cbar = fig.colorbar(
            im,
            ax=ax
        )

        cbar.set_label(
            "Temperature Anomaly (°C)"
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)

        # ----------------------------------------------------
        # SUMMARY ANOMALY
        # ----------------------------------------------------

        anomaly_values = (
            anomaly_data
            .stack()
            .dropna()
        )

        if not anomaly_values.empty:

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "📈 Maximum Positive Anomaly",
                f"{anomaly_values.max():.2f} °C"
            )

            col2.metric(
                "📉 Maximum Negative Anomaly",
                f"{anomaly_values.min():.2f} °C"
            )

            col3.metric(
                "📊 Mean Anomaly",
                f"{anomaly_values.mean():.2f} °C"
            )


    # ========================================================
    # TAB 4 — STATISTICS
    # ========================================================

    with all_year_tabs[3]:

        st.subheader(
            "📋 Temperature Statistics — All Years"
        )

        # ----------------------------------------------------
        # DATA LONG
        # ----------------------------------------------------

        stats_long = (
            yearly_mean_table
            .reset_index()
            .melt(
                id_vars=["Year"],
                value_vars=months,
                var_name="Month",
                value_name="Temperature"
            )
        )

        stats_long["Temperature"] = pd.to_numeric(
            stats_long["Temperature"],
            errors="coerce"
        )

        stats_long = stats_long.dropna(
            subset=["Temperature"]
        )

        # ----------------------------------------------------
        # OVERALL STATISTICS
        # ----------------------------------------------------

        overall_stats = pd.DataFrame({
            "Statistic": [
                "Count",
                "Mean",
                "Median",
                "Minimum",
                "Maximum",
                "Standard Deviation",
                "Q1 (25%)",
                "Q3 (75%)",
                "Range"
            ],
            "Value": [
                stats_long["Temperature"].count(),
                stats_long["Temperature"].mean(),
                stats_long["Temperature"].median(),
                stats_long["Temperature"].min(),
                stats_long["Temperature"].max(),
                stats_long["Temperature"].std(),
                stats_long["Temperature"].quantile(0.25),
                stats_long["Temperature"].quantile(0.75),
                (
                    stats_long["Temperature"].max()
                    -
                    stats_long["Temperature"].min()
                )
            ]
        })

        overall_stats["Value"] = (
            overall_stats["Value"]
            .round(2)
        )

        st.markdown(
            "### 📊 Statistik Keseluruhan"
        )

        st.dataframe(
            overall_stats,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # MONTHLY STATISTICS
        # ----------------------------------------------------

        st.markdown(
            "### 📅 Statistik Mengikut Bulan"
        )

        monthly_stats = (
            stats_long
            .groupby("Month")["Temperature"]
            .agg([
                "count",
                "mean",
                "median",
                "min",
                "max",
                "std"
            ])
            .reindex(months)
            .reset_index()
        )

        monthly_stats.columns = [
            "Month",
            "Count",
            "Mean (°C)",
            "Median (°C)",
            "Minimum (°C)",
            "Maximum (°C)",
            "Std Dev (°C)"
        ]

        monthly_stats = (
            monthly_stats
            .round(2)
        )

        st.dataframe(
            monthly_stats,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # DOWNLOAD STATISTICS
        # ----------------------------------------------------

        csv_stats = (
            monthly_stats
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "⬇️ Download Monthly Statistics",
            data=csv_stats,
            file_name=(
                f"monthly_temperature_statistics_"
                f"{result['file_name']}.csv"
            ),
            mime="text/csv",
            key="download_all_year_monthly_statistics"
        )


    # ========================================================
    # TAB 5 — BOXPLOT
    # ========================================================

    with all_year_tabs[4]:

        st.subheader(
            "📦 Boxplot Temperature Mengikut Bulan"
        )

        box_data = []

        for month in months:

            values = (
                stats_long.loc[
                    stats_long["Month"] == month,
                    "Temperature"
                ]
                .dropna()
                .values
            )

            box_data.append(
                values
            )

        fig, ax = plt.subplots(
            figsize=(FIG_WIDTH, FIG_HEIGHT)
        )

        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)

        ax.boxplot(
            box_data,
            tick_labels=months,
            patch_artist=False
        )

        ax.set_title(
            f"{result['file_name']}\n"
            f"Monthly Temperature Distribution "
            f"{YEAR_RANGE_TEXT}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Month",
            fontsize=12
        )

        ax.set_ylabel(
            "Temperature (°C)",
            fontsize=12
        )

        ax.set_ylim(
            TEMP_MIN,
            TEMP_MAX
        )

        ax.grid(
            True,
            axis="y",
            linestyle="--",
            alpha=0.4
        )

        plt.xticks(
            rotation=45
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)

        # ----------------------------------------------------
        # SUMMARY BOXPLOT
        # ----------------------------------------------------

        box_summary = (
            stats_long
            .groupby("Month")["Temperature"]
            .describe()
            .reindex(months)
            .round(2)
        )

        st.markdown(
            "### 📋 Ringkasan Boxplot"
        )

        st.dataframe(
            box_summary,
            use_container_width=True
        )

        # ----------------------------------------------------
        # DOWNLOAD BOXPLOT DATA
        # ----------------------------------------------------

        csv_boxplot = (
            box_summary
            .to_csv()
            .encode("utf-8")
        )

        st.download_button(
            "⬇️ Download Boxplot Statistics",
            data=csv_boxplot,
            file_name=(
                f"boxplot_temperature_statistics_"
                f"{result['file_name']}.csv"
            ),
            mime="text/csv",
            key="download_all_year_boxplot"
        )

# ============================================================
# MAIN TAB 3 — STATION COMPARISON
# ============================================================
with main_tabs[2]:

    st.subheader(
        f"🔄 Station Comparison - "
        f"Monthly Mean Temperature {target_year}"
    )

    comparison_rows = []

    for result in successful_results:

        values = result["temperature_target"]

        row = {
            "Station": result["file_name"]
        }

        for month in months:
            row[month] = values.get(
                month,
                np.nan
            )

        comparison_rows.append(row)

    comparison_table = (
        pd.DataFrame(comparison_rows)
        .set_index("Station")
        .round(2)
    )

    st.dataframe(
        comparison_table,
        use_container_width=True
    )

    # --------------------------------------------------------
    # STATION COMPARISON GRAPH
    # --------------------------------------------------------
    fig, ax = plt.subplots(
        figsize=(14, 8)
    )

    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    for station in comparison_table.index:

        ax.plot(
            months,
            comparison_table.loc[
                station,
                months
            ],
            marker="o",
            linewidth=2,
            label=station
        )

    ax.set_title(
        f"Monthly Mean Temperature Comparison "
        f"Between Stations - {target_year}",
        fontsize=16,
        fontweight="bold"
    )

    ax.set_xlabel(
        "Month",
        fontsize=12
    )

    ax.set_ylabel(
        "Temperature (°C)",
        fontsize=12
    )

    ax.grid(
        True,
        axis="y",
        linestyle="--",
        alpha=0.4
    )

    ax.legend(
        bbox_to_anchor=(1.02, 1),
        loc="upper left"
    )

    plt.tight_layout()

    st.pyplot(
        fig,
        use_container_width=True
    )

    plt.close(fig)

# ============================================================
# MAIN TAB 4 — SUHU TERTINGGI / EKSTREM
# ============================================================

with main_tabs[3]:

    st.header("🔥 Analisis Suhu Ekstrem")

    # ========================================================
    # PILIH STESEN
    # ========================================================

    available_stations_extreme = [
        result["file_name"]
        for result in successful_results
    ]

    if not available_stations_extreme:

        st.warning(
            "⚠️ Tiada stesen dengan data yang berjaya diproses."
        )

        st.stop()

    selected_station_extreme = st.selectbox(
        "🏢 Pilih Stesen",
        available_stations_extreme,
        key="extreme_station"
    )

    # ========================================================
    # CARI RESULT STESEN
    # ========================================================

    selected_extreme_result = None

    for result in successful_results:

        if result["file_name"] == selected_station_extreme:

            selected_extreme_result = result
            break

    if selected_extreme_result is None:

        st.error(
            "❌ Data stesen tidak dijumpai."
        )

        st.stop()

    # ========================================================
    # AMBIL DATA
    # ========================================================

    all_daily_extreme = (
        selected_extreme_result["all_daily"].copy()
    )

    original_file_name_extreme = (
        selected_extreme_result["original_file_name"]
    )

    read_errors_extreme = (
        selected_extreme_result["read_errors"]
    )

    # ========================================================
    # FILTER TEMPOH ANALISIS
    # ========================================================

    period_data_extreme = all_daily_extreme[
        all_daily_extreme["Year"].between(
            int(START_YEAR),
            int(END_YEAR)
        )
    ].copy()

    if period_data_extreme.empty:

        st.warning(
            f"⚠️ Tiada data antara "
            f"{START_YEAR} hingga {END_YEAR}."
        )

        st.stop()

    # ========================================================
    # WIDE → LONG FORMAT
    # ========================================================

    extreme_long = period_data_extreme.melt(
        id_vars=[
            "Year",
            "hari"
        ],
        value_vars=months,
        var_name="Month",
        value_name="Temperature"
    )

    # ========================================================
    # CONVERT NUMERIC
    # ========================================================

    extreme_long["Year"] = pd.to_numeric(
        extreme_long["Year"],
        errors="coerce"
    )

    extreme_long["hari"] = pd.to_numeric(
        extreme_long["hari"],
        errors="coerce"
    )

    extreme_long["Temperature"] = pd.to_numeric(
        extreme_long["Temperature"],
        errors="coerce"
    )

    # ========================================================
    # MONTH NUMBER
    # ========================================================

    month_number = {
        month: i + 1
        for i, month in enumerate(months)
    }

    extreme_long["Month_Number"] = (
        extreme_long["Month"].map(month_number)
    )

    # ========================================================
    # BUANG DATA TIDAK SAH
    # ========================================================

    extreme_long = extreme_long.dropna(
        subset=[
            "Year",
            "hari",
            "Month_Number",
            "Temperature"
        ]
    ).copy()

    # ========================================================
    # BILANGAN HARI DALAM BULAN
    # ========================================================

    extreme_long["Days_In_Month"] = extreme_long.apply(
        lambda row: calendar.monthrange(
            int(row["Year"]),
            int(row["Month_Number"])
        )[1],
        axis=1
    )

    # ========================================================
    # VALID DAY
    # ========================================================

    extreme_long = extreme_long[
        (extreme_long["hari"] >= 1) &
        (
            extreme_long["hari"]
            <= extreme_long["Days_In_Month"]
        )
    ].copy()

    # ========================================================
    # CREATE DATE
    # ========================================================

    extreme_long["Date"] = pd.to_datetime(
        dict(
            year=extreme_long["Year"].astype(int),
            month=extreme_long["Month_Number"].astype(int),
            day=extreme_long["hari"].astype(int)
        ),
        errors="coerce"
    )

    extreme_long = extreme_long.dropna(
        subset=["Date"]
    ).copy()

    # ========================================================
    # CHECK DATA
    # ========================================================

    if extreme_long.empty:

        st.warning(
            "⚠️ Tiada data suhu yang sah untuk dianalisis."
        )

        st.stop()

    # ========================================================
    # SUSUN IKUT TARIKH
    # ========================================================

    extreme_long = (
        extreme_long
        .sort_values("Date")
        .reset_index(drop=True)
    )

    # ========================================================
    # REKOD SUHU TERTINGGI
    # ========================================================

    highest_index = (
        extreme_long["Temperature"].idxmax()
    )

    highest_row = (
        extreme_long.loc[highest_index]
    )

    highest_temperature = (
        highest_row["Temperature"]
    )

    highest_date = (
        highest_row["Date"]
    )

    # ========================================================
    # REKOD SUHU TERENDAH
    # ========================================================

    lowest_index = (
        extreme_long["Temperature"].idxmin()
    )

    lowest_row = (
        extreme_long.loc[lowest_index]
    )

    lowest_temperature = (
        lowest_row["Temperature"]
    )

    lowest_date = (
        lowest_row["Date"]
    )

    # ========================================================
    # RANGE SUHU
    # ========================================================

    temperature_range = (
        highest_temperature
        - lowest_temperature
    )

    # ========================================================
    # SUB TABS
    # ========================================================

    extreme_tabs = st.tabs([
        "🌡️ Rekod Ekstrem",
        "🏆 Top 10 Tertinggi",
        "❄️ Top 10 Terendah",
        "📅 Maximum Mengikut Tahun",
        "🔥 Cuaca Panas"
    ])

    # ========================================================
    # TAB 1 — REKOD EKSTREM
    # ========================================================

    with extreme_tabs[0]:

        st.subheader(
            "🌡️ Rekod Suhu Ekstrem"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "🔥 Suhu Tertinggi",
                f"{highest_temperature:.1f} °C"
            )

            st.caption(
                highest_date.strftime(
                    "%d/%m/%Y"
                )
            )

        with col2:

            st.metric(
                "❄️ Suhu Terendah",
                f"{lowest_temperature:.1f} °C"
            )

            st.caption(
                lowest_date.strftime(
                    "%d/%m/%Y"
                )
            )

        with col3:

            st.metric(
                "📏 Julat Suhu",
                f"{temperature_range:.1f} °C"
            )

        st.markdown("---")

        col1, col2 = st.columns(2)

        # ----------------------------------------------------
        # TERTINGGI
        # ----------------------------------------------------

        with col1:

            st.markdown(
                "### 🔥 Rekod Tertinggi"
            )

            highest_info = pd.DataFrame({
                "Perkara": [
                    "Suhu",
                    "Tarikh",
                    "Tahun",
                    "Bulan",
                    "Hari"
                ],
                "Nilai": [
                    f"{highest_temperature:.1f} °C",
                    highest_date.strftime(
                        "%d/%m/%Y"
                    ),
                    highest_date.year,
                    highest_date.strftime("%B"),
                    highest_date.day
                ]
            })

            st.dataframe(
                highest_info,
                use_container_width=True,
                hide_index=True
            )

        # ----------------------------------------------------
        # TERENDAH
        # ----------------------------------------------------

        with col2:

            st.markdown(
                "### ❄️ Rekod Terendah"
            )

            lowest_info = pd.DataFrame({
                "Perkara": [
                    "Suhu",
                    "Tarikh",
                    "Tahun",
                    "Bulan",
                    "Hari"
                ],
                "Nilai": [
                    f"{lowest_temperature:.1f} °C",
                    lowest_date.strftime(
                        "%d/%m/%Y"
                    ),
                    lowest_date.year,
                    lowest_date.strftime("%B"),
                    lowest_date.day
                ]
            })

            st.dataframe(
                lowest_info,
                use_container_width=True,
                hide_index=True
            )

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        extreme_record_download = pd.DataFrame({
            "Stesen": [
                selected_station_extreme
            ],
            "Suhu Tertinggi (°C)": [
                highest_temperature
            ],
            "Tarikh Tertinggi": [
                highest_date.strftime(
                    "%d/%m/%Y"
                )
            ],
            "Suhu Terendah (°C)": [
                lowest_temperature
            ],
            "Tarikh Terendah": [
                lowest_date.strftime(
                    "%d/%m/%Y"
                )
            ],
            "Julat Suhu (°C)": [
                temperature_range
            ]
        })

        csv_extreme_record = (
            extreme_record_download
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "⬇️ Download Rekod Ekstrem",
            data=csv_extreme_record,
            file_name=(
                f"rekod_suhu_ekstrem_"
                f"{selected_station_extreme}.csv"
            ),
            mime="text/csv",
            key="download_extreme_record"
        )

    # ========================================================
    # TAB 2 — TOP 10 TERTINGGI
    # ========================================================

    with extreme_tabs[1]:

        st.subheader(
            "🏆 Top 10 Suhu Tertinggi"
        )

        top10_highest = (
            extreme_long
            .nlargest(
                10,
                "Temperature"
            )
            .copy()
        )

        top10_highest["Tarikh"] = (
            top10_highest["Date"]
            .dt.strftime("%d/%m/%Y")
        )

        top10_highest_display = (
            top10_highest[
                [
                    "Tarikh",
                    "Temperature"
                ]
            ]
            .rename(
                columns={
                    "Tarikh": "Tarikh",
                    "Temperature": "Suhu (°C)"
                }
            )
            .reset_index(drop=True)
        )

        top10_highest_display.index += 1

        st.dataframe(
            top10_highest_display,
            use_container_width=True
        )

        # ----------------------------------------------------
        # BAR CHART
        # ----------------------------------------------------

        fig, ax = plt.subplots(
            figsize=(FIG_WIDTH, FIG_HEIGHT)
        )

        x_labels = (
            top10_highest["Date"]
            .dt.strftime("%d/%m/%Y")
        )

        bars = ax.bar(
            x_labels,
            top10_highest["Temperature"],
            edgecolor="black",
            linewidth=0.8
        )
        
        # NILAI DI ATAS BAR
        for bar, value in zip(
            bars,
            top10_highest["Temperature"]
        ):
        
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3,
                f"{value:.1f} °C",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )

        ax.set_title(
            f"Top 10 Suhu Tertinggi\n"
            f"{selected_station_extreme}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Tarikh"
        )

        ax.set_ylabel(
            "Temperature (°C)"
        )

        ax.set_ylim(
            TEMP_MIN,
            TEMP_MAX + 5
        )

        ax.tick_params(
            axis="x",
            rotation=45
        )

        ax.grid(
            True,
            axis="y",
            linestyle="--",
            alpha=0.4
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        csv_top10_highest = (
            top10_highest_display
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "⬇️ Download Top 10 Tertinggi",
            data=csv_top10_highest,
            file_name=(
                f"top10_suhu_tertinggi_"
                f"{selected_station_extreme}.csv"
            ),
            mime="text/csv",
            key="download_top10_highest"
        )

    # ========================================================
    # TAB 3 — TOP 10 TERENDAH
    # ========================================================

    with extreme_tabs[2]:

        st.subheader(
            "❄️ Top 10 Suhu Terendah"
        )

        top10_lowest = (
            extreme_long
            .nsmallest(
                10,
                "Temperature"
            )
            .copy()
        )

        top10_lowest["Tarikh"] = (
            top10_lowest["Date"]
            .dt.strftime("%d/%m/%Y")
        )

        top10_lowest_display = (
            top10_lowest[
                [
                    "Tarikh",
                    "Temperature"
                ]
            ]
            .rename(
                columns={
                    "Tarikh": "Tarikh",
                    "Temperature": "Suhu (°C)"
                }
            )
            .reset_index(drop=True)
        )

        top10_lowest_display.index += 1

        st.dataframe(
            top10_lowest_display,
            use_container_width=True
        )

        # ----------------------------------------------------
        # BAR CHART
        # ----------------------------------------------------

        fig, ax = plt.subplots(
            figsize=(FIG_WIDTH, FIG_HEIGHT)
        )

        x_labels = (
            top10_lowest["Date"]
            .dt.strftime("%d/%m/%Y")
        )

        bars = ax.bar(
            x_labels,
            top10_lowest["Temperature"],
            edgecolor="black",
            linewidth=0.8
        )
        
        # NILAI DI ATAS BAR
        for bar, value in zip(
            bars,
            top10_lowest["Temperature"]
        ):
        
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3,
                f"{value:.1f} °C",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )

        ax.set_title(
            f"Top 10 Suhu Terendah\n"
            f"{selected_station_extreme}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Tarikh"
        )

        ax.set_ylabel(
            "Temperature (°C)"
        )

        ax.set_ylim(
            TEMP_MIN,
            TEMP_MAX + 5
        )

        ax.tick_params(
            axis="x",
            rotation=45
        )

        ax.grid(
            True,
            axis="y",
            linestyle="--",
            alpha=0.4
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        csv_top10_lowest = (
            top10_lowest_display
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "⬇️ Download Top 10 Terendah",
            data=csv_top10_lowest,
            file_name=(
                f"top10_suhu_terendah_"
                f"{selected_station_extreme}.csv"
            ),
            mime="text/csv",
            key="download_top10_lowest"
        )

    # ========================================================
    # TAB 4 — MAXIMUM MENGIKUT TAHUN
    # ========================================================
    
    with extreme_tabs[3]:
    
        st.subheader(
            "📅 Suhu Maximum Mengikut Tahun"
        )
    
        # ----------------------------------------------------
        # CARI BARIS SUHU MAKSIMUM SETIAP TAHUN
        # ----------------------------------------------------
    
        annual_max_idx = (
            extreme_long
            .groupby("Year")["Temperature"]
            .idxmax()
        )
    
        annual_max = (
            extreme_long
            .loc[
                annual_max_idx,
                ["Year", "Date", "Temperature"]
            ]
            .copy()
        )
    
        annual_max = annual_max.sort_values(
            "Year"
        )
    
        annual_max["Year"] = (
            annual_max["Year"]
            .astype(int)
        )
    
        # ----------------------------------------------------
        # FORMAT TARIKH
        # ----------------------------------------------------
    
        annual_max["Date"] = (
            pd.to_datetime(
                annual_max["Date"]
            ).dt.strftime("%d/%m/%Y")
        )
    
        # ----------------------------------------------------
        # TABLE DISPLAY
        # ----------------------------------------------------
    
        annual_max_display = (
            annual_max
            .rename(
                columns={
                    "Year": "Tahun",
                    "Date": "Tarikh",
                    "Temperature": "Maximum (°C)"
                }
            )
            .reset_index(drop=True)
        )
    
        st.dataframe(
            annual_max_display,
            use_container_width=True,
            hide_index=True
        )
        # ----------------------------------------------------
        # BAR CHART
        # ----------------------------------------------------

        fig, ax = plt.subplots(
            figsize=(FIG_WIDTH, FIG_HEIGHT)
        )

        bars = ax.bar(
            annual_max["Year"].astype(str),
            annual_max["Temperature"],
            edgecolor="black",
            linewidth=0.8
        )
        
        # NILAI DI ATAS BAR
        for bar, value in zip(
            bars,
            annual_max["Temperature"]
        ):
        
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3,
                f"{value:.1f} °C",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )

        ax.set_title(
            f"Maximum Temperature Mengikut Tahun\n"
            f"{selected_station_extreme}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Tahun"
        )

        ax.set_ylabel(
            "Maximum Temperature (°C)"
        )

        ax.set_ylim(
            TEMP_MIN,
            TEMP_MAX + 5
        )

        ax.grid(
            True,
            axis="y",
            linestyle="--",
            alpha=0.4
        )

        plt.xticks(
            rotation=45
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        csv_annual_max = (
            annual_max_display
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "⬇️ Download Maximum Mengikut Tahun",
            data=csv_annual_max,
            file_name=(
                f"maximum_suhu_tahunan_"
                f"{selected_station_extreme}.csv"
            ),
            mime="text/csv",
            key="download_annual_max"
        )
        
        # ========================================================
        # TAB 5 — CUACA PANAS MENGIKUT TAHUN
        # ========================================================
        
        with extreme_tabs[4]:
        
            st.subheader(
                f"🔥 Analisis Cuaca Panas Mengikut Tahun "
                f"({START_YEAR}–{END_YEAR})"
            )
        
            st.caption(
                f"Stesen: {selected_station_extreme}"
            )
        
            st.info(
                "Kejadian cuaca panas dikira apabila suhu "
                "mencapai sekurang-kurangnya 35 °C selama "
                "3 hari berturut-turut."
            )
        
            # ====================================================
            # KRITERIA
            # ====================================================
        
            st.markdown(
                """
                ### 🌡️ Kriteria Tahap Cuaca Panas
        
                | Tahap | Kategori | Suhu | Tempoh |
                |---|---|---|---|
                | 🟡 Tahap 1 | Berjaga-jaga | 35 hingga <37 °C | ≥ 3 hari berturut-turut |
                | 🟠 Tahap 2 | Gelombang Haba | 37 hingga 40 °C | ≥ 3 hari berturut-turut |
                | 🔴 Tahap 3 | Bahaya / Gelombang Haba Ekstrem | >40 °C | ≥ 3 hari berturut-turut |
                """
            )
        
            # ====================================================
            # DATA HARIAN
            # ====================================================
        
            heatwave_data = extreme_long[
                [
                    "Date",
                    "Year",
                    "Temperature"
                ]
            ].copy()
        
            heatwave_data["Temperature"] = pd.to_numeric(
                heatwave_data["Temperature"],
                errors="coerce"
            )
        
            heatwave_data["Year"] = pd.to_numeric(
                heatwave_data["Year"],
                errors="coerce"
            )
        
            heatwave_data = (
                heatwave_data
                .dropna(
                    subset=[
                        "Date",
                        "Year",
                        "Temperature"
                    ]
                )
                .sort_values("Date")
                .drop_duplicates(
                    subset=["Date"],
                    keep="first"
                )
                .reset_index(drop=True)
            )
        
            # ====================================================
            # CLASSIFY TEMPERATURE LEVEL
            # ====================================================
        
            def get_heat_level(temp):
        
                if pd.isna(temp):
                    return "Missing"
        
                if temp > 40:
                    return "Tahap 3"
        
                elif temp >= 37:
                    return "Tahap 2"
        
                elif temp >= 35:
                    return "Tahap 1"
        
                return "Normal"
        
            heatwave_data["Tahap"] = (
                heatwave_data["Temperature"]
                .apply(get_heat_level)
            )
        
            # ====================================================
            # DETECT CONSECUTIVE HOT EVENTS
            # ====================================================
        
            detected_events = []
        
            current_event = []
            previous_date = None
        
            for _, row in heatwave_data.iterrows():
        
                current_date = row["Date"]
                temperature = row["Temperature"]
        
                # ------------------------------------------------
                # SUHU >= 35°C
                # ------------------------------------------------
        
                if temperature >= 35:
        
                    # Event baru
                    if not current_event:
        
                        current_event = [row]
        
                    # Hari berturut-turut
                    elif (
                        previous_date is not None
                        and (current_date - previous_date).days == 1
                    ):
        
                        current_event.append(row)
        
                    # Ada gap tarikh
                    else:
        
                        if len(current_event) >= 3:
        
                            event_df = pd.DataFrame(
                                current_event
                            )
        
                            max_temp = event_df[
                                "Temperature"
                            ].max()
        
                            # Tentukan tahap berdasarkan
                            # suhu maksimum sepanjang event
                            if max_temp > 40:
        
                                event_level = "Tahap 3"
        
                            elif max_temp >= 37:
        
                                event_level = "Tahap 2"
        
                            else:
        
                                event_level = "Tahap 1"
        
                            detected_events.append({
                                "Tahun": int(
                                    event_df["Year"].iloc[0]
                                ),
                                "Tahap": event_level,
                                "Tarikh Mula": event_df["Date"].min(),
                                "Tarikh Tamat": event_df["Date"].max(),
                                "Bilangan Hari": len(event_df),
                                "Suhu Maksimum (°C)": max_temp
                            })
        
                        current_event = [row]
        
                # ------------------------------------------------
                # SUHU < 35°C
                # ------------------------------------------------
        
                else:
        
                    if len(current_event) >= 3:
        
                        event_df = pd.DataFrame(
                            current_event
                        )
        
                        max_temp = event_df[
                            "Temperature"
                        ].max()
        
                        if max_temp > 40:
        
                            event_level = "Tahap 3"
        
                        elif max_temp >= 37:
        
                            event_level = "Tahap 2"
        
                        else:
        
                            event_level = "Tahap 1"
        
                        detected_events.append({
                            "Tahun": int(
                                event_df["Year"].iloc[0]
                            ),
                            "Tahap": event_level,
                            "Tarikh Mula": event_df["Date"].min(),
                            "Tarikh Tamat": event_df["Date"].max(),
                            "Bilangan Hari": len(event_df),
                            "Suhu Maksimum (°C)": max_temp
                        })
        
                    current_event = []
        
                previous_date = current_date
        
            # ====================================================
            # CHECK LAST EVENT
            # ====================================================
        
            if len(current_event) >= 3:
        
                event_df = pd.DataFrame(
                    current_event
                )
        
                max_temp = event_df[
                    "Temperature"
                ].max()
        
                if max_temp > 40:
        
                    event_level = "Tahap 3"
        
                elif max_temp >= 37:
        
                    event_level = "Tahap 2"
        
                else:
        
                    event_level = "Tahap 1"
        
                detected_events.append({
                    "Tahun": int(
                        event_df["Year"].iloc[0]
                    ),
                    "Tahap": event_level,
                    "Tarikh Mula": event_df["Date"].min(),
                    "Tarikh Tamat": event_df["Date"].max(),
                    "Bilangan Hari": len(event_df),
                    "Suhu Maksimum (°C)": max_temp
                })
        
            # ====================================================
            # RESULT
            # ====================================================
        
            if not detected_events:
        
                st.success(
                    "✅ Tiada kejadian cuaca panas "
                    "selama sekurang-kurangnya 3 hari "
                    "berturut-turut dikesan."
                )
        
            else:
        
                heatwave_df = pd.DataFrame(
                    detected_events
                )
        
                heatwave_df = (
                    heatwave_df
                    .sort_values(
                        [
                            "Tahun",
                            "Tarikh Mula"
                        ]
                    )
                    .reset_index(drop=True)
                )
        
                # =================================================
                # RINGKASAN MENGIKUT TAHUN
                # =================================================
        
                st.subheader(
                    "📊 Ringkasan Cuaca Panas Mengikut Tahun"
                )
        
                yearly_summary = (
                    heatwave_df
                    .pivot_table(
                        index="Tahun",
                        columns="Tahap",
                        values="Tarikh Mula",
                        aggfunc="count",
                        fill_value=0
                    )
                    .reset_index()
                )
        
                # Pastikan semua kolum tahap wujud
                for stage in [
                    "Tahap 1",
                    "Tahap 2",
                    "Tahap 3"
                ]:
        
                    if stage not in yearly_summary.columns:
        
                        yearly_summary[stage] = 0
        
                yearly_summary = yearly_summary[
                    [
                        "Tahun",
                        "Tahap 1",
                        "Tahap 2",
                        "Tahap 3"
                    ]
                ]
        
                yearly_summary["Jumlah Kejadian"] = (
                    yearly_summary[
                        [
                            "Tahap 1",
                            "Tahap 2",
                            "Tahap 3"
                        ]
                    ]
                    .sum(axis=1)
                )
        
                yearly_summary = yearly_summary.sort_values(
                    "Tahun"
                )
        
                st.dataframe(
                    yearly_summary,
                    use_container_width=True,
                    hide_index=True
                )
        
                # =================================================
                # METRICS KESELURUHAN
                # =================================================
        
                st.markdown("---")
        
                total_events = len(
                    heatwave_df
                )
        
                stage1_count = (
                    heatwave_df["Tahap"]
                    .eq("Tahap 1")
                    .sum()
                )
        
                stage2_count = (
                    heatwave_df["Tahap"]
                    .eq("Tahap 2")
                    .sum()
                )
        
                stage3_count = (
                    heatwave_df["Tahap"]
                    .eq("Tahap 3")
                    .sum()
                )
        
                col1, col2, col3, col4 = (
                    st.columns(4)
                )
        
                with col1:
        
                    st.metric(
                        "🔥 Jumlah Kejadian",
                        total_events
                    )
        
                with col2:
        
                    st.metric(
                        "🟡 Tahap 1",
                        stage1_count
                    )
        
                with col3:
        
                    st.metric(
                        "🟠 Tahap 2",
                        stage2_count
                    )
        
                with col4:
        
                    st.metric(
                        "🔴 Tahap 3",
                        stage3_count
                    )
        
                # =================================================
                # GRAF — TAHAP MENGIKUT TAHUN
                # =================================================
        
                st.subheader(
                    "📊 Tahap Cuaca Panas Mengikut Tahun"
                )
        
                fig, ax = plt.subplots(
                    figsize=(FIG_WIDTH, FIG_HEIGHT)
                )
        
                x = np.arange(
                    len(yearly_summary)
                )
        
                width = 0.25
        
                bars1 = ax.bar(
                    x - width,
                    yearly_summary["Tahap 1"],
                    width,
                    label="Tahap 1",
                    edgecolor="black",
                    linewidth=0.8
                )
        
                bars2 = ax.bar(
                    x,
                    yearly_summary["Tahap 2"],
                    width,
                    label="Tahap 2",
                    edgecolor="black",
                    linewidth=0.8
                )
        
                bars3 = ax.bar(
                    x + width,
                    yearly_summary["Tahap 3"],
                    width,
                    label="Tahap 3",
                    edgecolor="black",
                    linewidth=0.8
                )
        
                # Label nilai
                for bars in [
                    bars1,
                    bars2,
                    bars3
                ]:
        
                    for bar in bars:
        
                        height = bar.get_height()
        
                        if height > 0:
        
                            ax.text(
                                bar.get_x()
                                + bar.get_width() / 2,
                                height + 0.05,
                                f"{int(height)}",
                                ha="center",
                                va="bottom",
                                fontsize=9,
                                fontweight="bold"
                            )
        
                ax.set_title(
                    f"Bilangan Kejadian Mengikut Tahap dan Tahun\n"
                    f"{selected_station_extreme}",
                    fontsize=16,
                    fontweight="bold"
                )
        
                ax.set_xlabel(
                    "Tahun"
                )
        
                ax.set_ylabel(
                    "Bilangan Kejadian"
                )
        
                ax.set_xticks(
                    x
                )
        
                ax.set_xticklabels(
                    yearly_summary["Tahun"]
                    .astype(int)
                )
        
                ax.legend()
        
                ax.grid(
                    True,
                    axis="y",
                    linestyle="--",
                    alpha=0.4
                )
        
                plt.xticks(
                    rotation=45
                )
        
                plt.tight_layout()
        
                st.pyplot(
                    fig,
                    use_container_width=True
                )

                # ============================================================
                # DOWNLOAD GRAF TAHAP CUACA PANAS
                # ============================================================
                
                img_stage = io.BytesIO()
                
                fig.savefig(
                    img_stage,
                    format="png",
                    dpi=300,
                    bbox_inches="tight",
                    facecolor=fig.get_facecolor()
                )
                
                img_stage.seek(0)
                
                st.download_button(
                    label="📥 Download Graf Tahap Cuaca Panas",
                    data=img_stage,
                    file_name=f"Tahap_Cuaca_Panas_{selected_station_extreme}.png",
                    mime="image/png",
                    key="download_stage_heatwave_graph"
                )
                                
                plt.close(fig)
        
                # =================================================
                # REKOD KEJADIAN MENGIKUT TAHUN
                # =================================================
        
                st.markdown("---")
        
                st.subheader(
                    "📋 Rekod Kejadian Cuaca Panas Mengikut Tahun"
                )
        
                display_heatwave = (
                    heatwave_df.copy()
                )
        
                display_heatwave[
                    "Tarikh Mula"
                ] = (
                    display_heatwave[
                        "Tarikh Mula"
                    ]
                    .dt.strftime("%d/%m/%Y")
                )
        
                display_heatwave[
                    "Tarikh Tamat"
                ] = (
                    display_heatwave[
                        "Tarikh Tamat"
                    ]
                    .dt.strftime("%d/%m/%Y")
                )
        
                st.dataframe(
                    display_heatwave,
                    use_container_width=True,
                    hide_index=True
                )
        
                # =================================================
                # DOWNLOAD REKOD
                # =================================================
        
                csv_heatwave = (
                    display_heatwave
                    .to_csv(index=False)
                    .encode("utf-8")
                )
        
                st.download_button(
                    "⬇️ Download Rekod Cuaca Panas",
                    data=csv_heatwave,
                    file_name=(
                        f"rekod_cuaca_panas_mengikut_tahun_"
                        f"{selected_station_extreme}.csv"
                    ),
                    mime="text/csv",
                    key="download_heatwave"
                )
        
                # =================================================
                # DOWNLOAD RINGKASAN TAHUN
                # =================================================
        
                csv_yearly_heatwave = (
                    yearly_summary
                    .to_csv(index=False)
                    .encode("utf-8")
                )
        
                st.download_button(
                    "⬇️ Download Ringkasan Mengikut Tahun",
                    data=csv_yearly_heatwave,
                    file_name=(
                        f"ringkasan_cuaca_panas_tahunan_"
                        f"{selected_station_extreme}.csv"
                    ),
                    mime="text/csv",
                    key="download_yearly_heatwave"
                )
                
# ============================================================
# FOOTER
# ============================================================
st.divider()

st.caption(
    "🌡️ Temperature Data Analysis | "
    "Monthly Mean, Anomaly, Heatmap, Statistical Analysis, "
    "Temperature Extremes, Quality Control and Station Comparison"
)
