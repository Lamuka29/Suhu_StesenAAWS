import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import calendar
import io
import streamlit as st
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Temperature Analysis",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ Temperature Data Analysis")
st.caption(
    "Pemprosesan dan Analisis Data Suhu Harian"
)

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
TEMPERATURE_MIN = 0
TEMPERATURE_MAX = 40

# ============================================================
# FIGURE SIZE
# ============================================================
FIG_WIDTH = 14
FIG_HEIGHT = 9

# ============================================================
# FILE UPLOAD
# ============================================================
uploaded_files = st.file_uploader(
    "📁 Upload Excel file data suhu mengikut stesen",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

if not uploaded_files:

    st.info(
        "Sila upload sekurang-kurangnya satu fail Excel."
    )

    st.markdown(
        """
        **Format data yang diperlukan:**

        - Sheet dinamakan mengikut tahun, contoh `2017`, `2018`, ..., `2025`
        - Data disusun dalam format harian
        - Column pertama = `DATE`
        - Column kedua hingga ke-13 = `Jan` hingga `Dec`

        Contoh:

        | DATE | Jan | Feb | Mar | Apr | May | ... | Dec |
        |------|-----|-----|-----|-----|-----|-----|-----|
        | 1    | ... | ... | ... | ... | ... | ... | ... |
        | 2    | ... | ... | ... | ... | ... | ... | ... |
        | 3    | ... | ... | ... | ... | ... | ... | ... |
        """
    )

    st.stop()


# ============================================================
# DETECT AVAILABLE YEARS
# ============================================================
def get_available_years(uploaded_file):

    try:

        file_bytes = uploaded_file.getvalue()

        file_ext = os.path.splitext(
            uploaded_file.name
        )[1].lower()

        if file_ext == ".xls":
            engine = "xlrd"

        else:
            engine = "openpyxl"

        excel_file = pd.ExcelFile(
            io.BytesIO(file_bytes),
            engine=engine
        )

        available_years = []

        for sheet in excel_file.sheet_names:

            try:

                year = int(
                    str(sheet).strip()
                )

                if 1900 <= year <= 2100:
                    available_years.append(year)

            except:

                continue

        return sorted(
            set(available_years)
        )

    except Exception:

        return []


# ============================================================
# DETECT YEARS FROM ALL UPLOADED FILES
# ============================================================
all_available_years = set()

file_years = {}

for uploaded_file in uploaded_files:

    detected_years = get_available_years(
        uploaded_file
    )

    file_years[
        uploaded_file.name
    ] = detected_years

    all_available_years.update(
        detected_years
    )

all_available_years = sorted(
    all_available_years
)


# ============================================================
# CHECK AVAILABLE YEARS
# ============================================================
if not all_available_years:

    st.error(
        "❌ Tiada sheet tahun yang sah dijumpai "
        "dalam fail Excel."
    )

    st.stop()


# ============================================================
# TAHUN ANALISIS
# ============================================================
st.sidebar.subheader(
    "📅 Analysis Period"
)

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

    st.sidebar.error(
        "Start Year mesti lebih kecil "
        "atau sama dengan End Year."
    )

    st.stop()


years = range(
    int(START_YEAR),
    int(END_YEAR) + 1
)

YEAR_RANGE_TEXT = (
    f"{int(START_YEAR)}–{int(END_YEAR)}"
)

# ============================================================
# SIDEBAR SETTINGS
# ============================================================
st.sidebar.header(
    "⚙️ Analysis Settings"
)


# ============================================================
# TEMPERATURE DATA SETTINGS
# ============================================================
st.sidebar.subheader(
    "🌡️ Temperature Settings"
)

st.sidebar.info(
    "Nilai suhu negatif dibenarkan kerana suhu "
    "boleh berada di bawah 0 °C."
)


# ============================================================
# PLOT SETTINGS
# ============================================================
st.sidebar.header(
    "🎨 Plot Settings"
)


# ============================================================
# BACKGROUND
# ============================================================
BG_COLOR = st.sidebar.color_picker(
    "Background Graf",
    "#FFFFFF"
)


# ============================================================
# DEFAULT MONTH COLORS
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

    st.session_state.bar_colors = (
        default_colors.copy()
    )


if "max_daily_color" not in st.session_state:

    st.session_state.max_daily_color = (
        "#FF6347"
    )


if "min_daily_color" not in st.session_state:

    st.session_state.min_daily_color = (
        "#3CB371"
    )


if "mean_color" not in st.session_state:

    st.session_state.mean_color = (
        "#000000"
    )


if "hist_color" not in st.session_state:

    st.session_state.hist_color = (
        "#4682B4"
    )


# ============================================================
# SELECT CHART TYPE
# ============================================================
chart_options = [
    "Bar + Line",
]

selected_chart = st.sidebar.selectbox(
    "Select Chart",
    chart_options
)

# ============================================================
# MONTHLY TEMPERATURE
# ============================================================

if selected_chart == "Bar + Line":

    selected_month = st.sidebar.selectbox(
        "Select Month",
        months
    )

    selected_index = months.index(
        selected_month
    )

    st.session_state.bar_colors[
        selected_index
    ] = st.sidebar.color_picker(
        f"{selected_month} Bar Colour",
        st.session_state.bar_colors[
            selected_index
        ]
    )
# ============================================================
# MEAN LINE
# ============================================================
LINE_COLOR = st.sidebar.color_picker(
    "Mean",
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
# FUNCTION
# MAXIMUM CONSECUTIVE MISSING
# ============================================================
def max_consecutive_missing(values):

    is_missing = values.isna()

    max_missing = 0
    current_missing = 0

    for missing in is_missing:

        if missing:

            current_missing += 1

            if current_missing > max_missing:

                max_missing = current_missing

        else:

            current_missing = 0

    return max_missing


# ============================================================
# FUNCTION
# READ YEAR SHEET
# ============================================================
def read_year_sheet(
    uploaded_file,
    year
):

    try:

        file_bytes = (
            uploaded_file.getvalue()
        )

        file_ext = os.path.splitext(
            uploaded_file.name
        )[1].lower()

        if file_ext == ".xls":

            engine = "xlrd"

        elif file_ext == ".xlsx":

            engine = "openpyxl"

        else:

            return None, (
                "Format fail tidak disokong."
            )


        df = pd.read_excel(
            io.BytesIO(file_bytes),
            sheet_name=str(year),

            # Kalau header sebenar berada
            # pada baris pertama data:
            header=6,

            engine=engine
        )


    except Exception as e:

        return None, str(e)


    if df is None or df.empty:

        return None, "Sheet kosong."


    # --------------------------------------------------------
    # CHECK COLUMN
    # --------------------------------------------------------
    if df.shape[1] < 13:

        return None, (
            f"Bilangan column tidak mencukupi "
            f"({df.shape[1]} column dikesan). "
            f"Minimum 13 column diperlukan."
        )


    # --------------------------------------------------------
    # AMBIL 13 COLUMN PERTAMA
    # --------------------------------------------------------
    df = df.iloc[:, :13].copy()


    # --------------------------------------------------------
    # RENAME COLUMN
    # --------------------------------------------------------
    df.columns = [

        "hari",

        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec"

    ]


    # --------------------------------------------------------
    # CONVERT DAY
    # --------------------------------------------------------
    df["hari"] = pd.to_numeric(
        df["hari"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # VALID DAY
    # --------------------------------------------------------
    df = df[
        df["hari"].between(
            1,
            31
        )
    ].copy()


    # --------------------------------------------------------
    # CONVERT TEMPERATURE
    # --------------------------------------------------------
    for month in months:

        df[month] = pd.to_numeric(
            df[month],
            errors="coerce"
        )

        # ----------------------------------------------------
        # PENTING:
        # Suhu negatif TIDAK dibuang.
        # Hanya data bukan nombor / kosong
        # akan menjadi NaN.
        # ----------------------------------------------------


    # --------------------------------------------------------
    # ADD YEAR
    # --------------------------------------------------------
    df["Year"] = int(year)


    return df, None


# ============================================================
# FUNCTION
# ANALYZE ONE FILE
# ============================================================
def analyze_file(uploaded_file):

    file_name = os.path.splitext(
        uploaded_file.name
    )[0]

    original_file_name = (
        uploaded_file.name
    )

    daily_results = []

    read_errors = []


    # ========================================================
    # READ ALL YEARS
    # ========================================================
    for year in years:

        df, error = read_year_sheet(
            uploaded_file,
            year
        )

        if df is not None:

            daily_results.append(
                df
            )

        else:

            read_errors.append({

                "Year": int(year),
                "Error": error

            })


    # ========================================================
    # CHECK DATA
    # ========================================================
    if len(daily_results) == 0:

        return {

            "success": False,

            "file_name": file_name,

            "original_file_name":
                original_file_name,

            "error":
                "Tiada sheet tahun berjaya dibaca."

        }


    # ========================================================
    # COMBINE DATA
    # ========================================================
    all_daily = pd.concat(
        daily_results,
        ignore_index=True
    )


    # ========================================================
    # RETURN BASIC RESULTS
    # ========================================================
    return {

        "success": True,

        "file_name":
            file_name,

        "original_file_name":
            original_file_name,

        "all_daily":
            all_daily,

        "read_errors":
            read_errors

    }

# ============================================================
# PROCESS ALL UPLOADED FILES
# ============================================================

with st.spinner(
    "⏳ Sedang memproses semua fail Excel..."
):

    results = []

    progress_bar = st.progress(0)

    for i, uploaded_file in enumerate(uploaded_files):

        result = analyze_file(
            uploaded_file
        )

        results.append(
            result
        )

        progress_bar.progress(
            int(
                (
                    (i + 1)
                    /
                    len(uploaded_files)
                ) * 100
            )
        )

    progress_bar.empty()


# ============================================================
# CHECK RESULTS
# ============================================================

successful_results = [

    result

    for result in results

    if result.get(
        "success",
        False
    )

]


failed_results = [

    result

    for result in results

    if not result.get(
        "success",
        False
    )

]


# ============================================================
# FILE SUMMARY
# ============================================================

st.success(

    f"✅ {len(successful_results)} daripada "
    f"{len(uploaded_files)} fail berjaya dianalisis."

)


if failed_results:

    st.warning(

        f"⚠️ {len(failed_results)} fail "
        f"tidak berjaya dianalisis."

    )

    for result in failed_results:

        st.error(

            f"{result.get('original_file_name', 'Unknown')}: "
            f"{result.get('error', 'Unknown error')}"

        )


# ============================================================
# STOP IF NO SUCCESSFUL DATA
# ============================================================

if not successful_results:

    st.error(
        "❌ Tiada data suhu yang berjaya dianalisis."
    )

    st.stop()


# ============================================================
# STATION NAMES
# ============================================================

station_names = [

    result["file_name"]

    for result in successful_results

]


# ============================================================
# AVAILABLE YEARS
# ============================================================

available_years = sorted(

    set(

        int(year)

        for result in successful_results

        for year
        in result["all_daily"]["Year"]
        .dropna()
        .unique()

    )

)


if not available_years:

    st.error(
        "❌ Tiada tahun yang sah dalam data suhu."
    )

    st.stop()


# ============================================================
# TARGET YEAR
# ============================================================

target_year = st.sidebar.selectbox(

    "📅 Target Year",

    available_years,

    index=len(
        available_years
    ) - 1,

    key="target_year"

)

target_year = int(
    target_year
)


# ============================================================
# STATION SELECTION
# ============================================================

selected_station = st.sidebar.selectbox(

    "📍 Select Station",

    station_names,

    key="main_station"

)


# ============================================================
# GET SELECTED STATION DATA
# ============================================================

selected_result = next(

    (
        result

        for result
        in successful_results

        if result["file_name"]
        == selected_station

    ),

    None

)


if selected_result is None:

    st.error(
        "❌ Data stesen yang dipilih tidak dijumpai."
    )

    st.stop()


# ============================================================
# SELECTED STATION DAILY DATA
# ============================================================

all_daily = selected_result[
    "all_daily"
].copy()


# ============================================================
# FILTER SELECTED ANALYSIS PERIOD
# ============================================================

period_data = all_daily[
    all_daily["Year"].between(
        int(START_YEAR),
        int(END_YEAR)
    )
].copy()


if period_data.empty:

    st.warning(
        "⚠️ Tiada data dalam tempoh analisis "
        f"{YEAR_RANGE_TEXT}."
    )

    st.stop()

# ============================================================
# MAIN TABS
# ============================================================
main_tabs = st.tabs([
    "🌡️ Target Year",
    "📊 Purata Sepanjang Tempoh",
    "🏢 Perbandingan Data Stesen",
    "🔥 Suhu Tertinggi"
])
# ============================================================
# MAIN TAB 1 — TARGET YEAR
# ============================================================
with main_tabs[0]:

    # ========================================================
    # SUB TABS
    # ========================================================
    tabs = st.tabs([
        "📊 Monthly Temperature",
        "🔥 Heatmap",
        "📉 Anomaly",
        "📋 Statistics",
        "📈 Daily Temperature"
    ])

    # ========================================================
    # SELECTED STATION DATA
    # ========================================================
    file_name = selected_result["file_name"]

    original_file_name = (
        selected_result["original_file_name"]
    )

    all_daily = (
        selected_result["all_daily"]
        .copy()
    )

    read_errors = (
        selected_result["read_errors"]
    )

    # ========================================================
    # TARGET YEAR DATA
    # ========================================================
    target_data = all_daily[
        all_daily["Year"] == target_year
    ].copy()

    if target_data.empty:

        st.warning(
            f"⚠️ Tiada data suhu bagi tahun "
            f"{target_year} untuk stesen "
            f"{file_name}."
        )

        st.stop()

    # ========================================================
    # CONVERT TARGET YEAR TO LONG FORMAT
    # ========================================================
    target_long = target_data.melt(
        id_vars=[
            "Year",
            "hari"
        ],

        value_vars=months,

        var_name="Month",

        value_name="Temperature"
    )

    # ========================================================
    # MONTH NUMBER
    # ========================================================
    month_number = {
        month: i + 1
        for i, month in enumerate(months)
    }

    target_long["Month_Number"] = (
        target_long["Month"]
        .map(month_number)
    )

    # ========================================================
    # DAYS IN MONTH
    # ========================================================
    target_long["Days_In_Month"] = (
        target_long.apply(
            lambda row:
                calendar.monthrange(
                    int(row["Year"]),
                    int(row["Month_Number"])
                )[1],
            axis=1
        )
    )

    # ========================================================
    # REMOVE INVALID DAYS
    # ========================================================
    target_long = target_long[
        target_long["hari"]
        <= target_long["Days_In_Month"]
    ].copy()

    # ========================================================
    # REMOVE MISSING TEMPERATURE
    # ========================================================
    target_long = target_long.dropna(
        subset=["Temperature"]
    ).copy()

    # ========================================================
    # MONTHLY MEAN
    # ========================================================
    target_monthly_mean = (
        target_long
        .groupby("Month")["Temperature"]
        .mean()
        .reindex(months)
    )

    # ========================================================
    # MONTHLY MAXIMUM
    # ========================================================
    target_monthly_max = (
        target_long
        .groupby("Month")["Temperature"]
        .max()
        .reindex(months)
    )

    # ========================================================
    # MONTHLY MINIMUM
    # ========================================================
    target_monthly_min = (
        target_long
        .groupby("Month")["Temperature"]
        .min()
        .reindex(months)
    )

    # ========================================================
    # BASIC STATISTICS
    # ========================================================
    if not target_long.empty:

        target_mean = (
            target_long["Temperature"]
            .mean()
        )

        target_median = (
            target_long["Temperature"]
            .median()
        )

        target_max = (
            target_long["Temperature"]
            .max()
        )

        target_min = (
            target_long["Temperature"]
            .min()
        )

        target_std = (
            target_long["Temperature"]
            .std()
        )

    else:

        target_mean = np.nan
        target_median = np.nan
        target_max = np.nan
        target_min = np.nan
        target_std = np.nan

    # ========================================================
    # FILE HEADER
    # ========================================================
    st.divider()

    st.header(
        f"📁 {original_file_name}"
    )

    st.caption(
        f"📍 Station: {file_name} | "
        f"📅 Target Year: {target_year}"
    )

    # ========================================================
    # READ ERRORS
    # ========================================================
    if read_errors:

        with st.expander(
            "⚠️ Sheet yang tidak berjaya dibaca"
        ):

            error_df = pd.DataFrame(
                read_errors
            )

            st.dataframe(
                error_df,
                use_container_width=True,
                hide_index=True
            )

    # ============================================================
    # TAB 1 — MONTHLY TEMPERATURE
    # ============================================================
    with tabs[0]:

        st.subheader(
            f"📊 Monthly Mean, Maximum and Minimum "
            f"Temperature — {target_year}"
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

        fig.patch.set_facecolor(
            BG_COLOR
        )

        ax.set_facecolor(
            BG_COLOR
        )

        # ----------------------------------------------------
        # MEAN
        # ----------------------------------------------------
        ax.plot(
            x,
            target_monthly_mean.values,
            marker="o",
            linewidth=2.5,
            markersize=7,
            color=LINE_COLOR,
            label="Mean Temperature"
        )

        # ----------------------------------------------------
        # MAXIMUM
        # ----------------------------------------------------
        ax.plot(
            x,
            target_monthly_max.values,
            marker="^",
            linewidth=2,
            markersize=6,
            color=MAX_COLOR,
            label="Maximum Temperature"
        )

        # ----------------------------------------------------
        # MINIMUM
        # ----------------------------------------------------
        ax.plot(
            x,
            target_monthly_min.values,
            marker="v",
            linewidth=2,
            markersize=6,
            color=MIN_COLOR,
            label="Minimum Temperature"
        )

        # ----------------------------------------------------
        # MEAN VALUE LABEL
        # ----------------------------------------------------
        for i, value in enumerate(
            target_monthly_mean.values
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
                    fontsize=10,
                    fontweight="bold"
                )

        ax.set_title(
            f"{file_name}\n"
            f"Monthly Mean, Maximum and Minimum "
            f"Temperature — {target_year}",
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

        ax.set_ylim(
            TEMPERATURE_MIN,
            TEMPERATURE_MAX
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

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------
        monthly_table = pd.DataFrame({

            "Month":
                months,

            f"Mean Temperature {target_year} (°C)":
                target_monthly_mean.values,

            f"Maximum Temperature {target_year} (°C)":
                target_monthly_max.values,

            f"Minimum Temperature {target_year} (°C)":
                target_monthly_min.values

        }).round(2)

        st.dataframe(
            monthly_table,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # DOWNLOAD CSV
        # ----------------------------------------------------
        csv = (
            monthly_table
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "📥 Download Monthly Table CSV",
            data=csv,
            file_name=(
                f"{selected_station}_"
                f"monthly_temperature_"
                f"{target_year}.csv"
            ),
            mime="text/csv",
            key=(
                f"download_monthly_temperature_"
                f"{selected_station}_{target_year}"
            )
        )

        plt.close(fig)

    # ============================================================
    # TAB 2 — HEATMAP
    # ============================================================
    with tabs[1]:

        st.subheader(
            f"🔥 Daily Temperature Heatmap — "
            f"{target_year}"
        )

        heatmap_data = (
            target_data
            .set_index("hari")[months]
            .copy()
        )

        fig, ax = plt.subplots(
            figsize=(
                FIG_WIDTH,
                FIG_HEIGHT
            )
        )

        fig.patch.set_facecolor(
            BG_COLOR
        )

        ax.set_facecolor(
            BG_COLOR
        )

        valid_values = heatmap_data.values[
            ~pd.isna(
                heatmap_data.values
            )
        ]

        if len(valid_values) > 0:

            vmin = valid_values.min()
            vmax = valid_values.max()

            if vmin == vmax:

                vmax = vmin + 1

        else:

            vmin = TEMPERATURE_MIN
            vmax = TEMPERATURE_MAX

        im = ax.imshow(
            heatmap_data.values,
            aspect="auto",
            cmap="coolwarm",
            vmin=vmin,
            vmax=vmax
        )

        ax.set_xticks(
            range(len(months))
        )

        ax.set_xticklabels(
            months
        )

        ax.set_yticks(
            range(len(heatmap_data.index))
        )

        ax.set_yticklabels(
            heatmap_data.index.astype(int)
        )

        cbar = fig.colorbar(
            im,
            ax=ax
        )

        cbar.set_label(
            "Temperature (°C)",
            fontsize=11
        )

        ax.set_title(
            f"{file_name}\n"
            f"Daily Temperature Heatmap — "
            f"{target_year}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Month",
            fontsize=12
        )

        ax.set_ylabel(
            "Day",
            fontsize=12
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)

    # ============================================================
    # TAB 3 — ANOMALY
    # ============================================================
    with tabs[2]:

        st.subheader(
            f"📉 Temperature Anomaly {target_year} "
            f"Relative to Mean {YEAR_RANGE_TEXT}"
        )

        # ----------------------------------------------------
        # CLIMATOLOGICAL MEAN
        # ----------------------------------------------------
        period_long = period_data.melt(
            id_vars=[
                "Year",
                "hari"
            ],

            value_vars=months,

            var_name="Month",

            value_name="Temperature"
        )

        period_long["Month_Number"] = (
            period_long["Month"]
            .map(month_number)
        )

        period_long["Days_In_Month"] = (
            period_long.apply(
                lambda row:
                    calendar.monthrange(
                        int(row["Year"]),
                        int(row["Month_Number"])
                    )[1],
                axis=1
            )
        )

        period_long = period_long[
            period_long["hari"]
            <= period_long["Days_In_Month"]
        ].copy()

        period_long = period_long.dropna(
            subset=["Temperature"]
        )

        climatological_mean = (
            period_long
            .groupby("Month")["Temperature"]
            .mean()
            .reindex(months)
        )

        anomaly = (
            target_monthly_mean
            - climatological_mean
        )

        # ----------------------------------------------------
        # GRAPH
        # ----------------------------------------------------
        fig, ax = plt.subplots(
            figsize=(
                FIG_WIDTH,
                FIG_HEIGHT
            )
        )

        fig.patch.set_facecolor(
            BG_COLOR
        )

        ax.set_facecolor(
            BG_COLOR
        )

        anomaly_colors = [

            "steelblue"
            if pd.notna(value) and value >= 0
            else "darkorange"
            if pd.notna(value) and value < 0
            else "lightgray"

            for value
            in anomaly.values
        ]

        bars = ax.bar(
            x,
            anomaly.values,
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

        # ----------------------------------------------------
        # VALUE LABEL
        # ----------------------------------------------------
        for bar, value in zip(
            bars,
            anomaly.values
        ):

            if pd.notna(value):

                if value >= 0:

                    offset = 4
                    vertical = "bottom"

                else:

                    offset = -12
                    vertical = "top"

                ax.annotate(
                    f"{value:.2f}°C",
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
            f"Relative to Mean {YEAR_RANGE_TEXT}",
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

        ax.set_xticklabels(
            months
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

        # ----------------------------------------------------
        # ANOMALY TABLE
        # ----------------------------------------------------
        anomaly_table = pd.DataFrame({

            "Month":
                months,

            f"Mean Temperature {target_year} (°C)":
                target_monthly_mean.values,

            f"Mean Temperature {YEAR_RANGE_TEXT} (°C)":
                climatological_mean.values,

            "Anomaly (°C)":
                anomaly.values

        }).round(2)

        st.dataframe(
            anomaly_table,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # DOWNLOAD CSV
        # ----------------------------------------------------
        csv = (
            anomaly_table
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "📥 Download Anomaly CSV",
            data=csv,
            file_name=(
                f"{selected_station}_"
                f"temperature_anomaly_"
                f"{target_year}.csv"
            ),
            mime="text/csv",
            key=(
                f"download_temperature_anomaly_"
                f"{selected_station}_{target_year}"
            )
        )

        plt.close(fig)

    # ============================================================
    # TAB 4 — STATISTICS
    # ============================================================
    with tabs[3]:

        st.subheader(
            f"📋 Temperature Statistical Analysis "
            f"— {target_year}"
        )

        # ----------------------------------------------------
        # MONTHLY STATISTICS
        # ----------------------------------------------------
        monthly_std = (
            target_long
            .groupby("Month")["Temperature"]
            .std()
            .reindex(months)
        )

        statistics_table = pd.DataFrame({

            "Month":
                months,

            "Mean Temperature (°C)":
                target_monthly_mean.values,

            "Maximum Temperature (°C)":
                target_monthly_max.values,

            "Minimum Temperature (°C)":
                target_monthly_min.values,

            "Standard Deviation (°C)":
                monthly_std.values

        }).round(2)

        st.dataframe(
            statistics_table,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # OVERALL STATISTICS
        # ----------------------------------------------------
        st.markdown(
            "### Overall Statistics"
        )

        stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = (
            st.columns(5)
        )

        with stat_col1:

            st.metric(
                "Mean",
                (
                    f"{target_mean:.2f} °C"
                    if pd.notna(target_mean)
                    else "N.A."
                )
            )

        with stat_col2:

            st.metric(
                "Median",
                (
                    f"{target_median:.2f} °C"
                    if pd.notna(target_median)
                    else "N.A."
                )
            )

        with stat_col3:

            st.metric(
                "Maximum",
                (
                    f"{target_max:.2f} °C"
                    if pd.notna(target_max)
                    else "N.A."
                )
            )

        with stat_col4:

            st.metric(
                "Minimum",
                (
                    f"{target_min:.2f} °C"
                    if pd.notna(target_min)
                    else "N.A."
                )
            )

        with stat_col5:

            st.metric(
                "Std. Deviation",
                (
                    f"{target_std:.2f} °C"
                    if pd.notna(target_std)
                    else "N.A."
                )
            )

        overall_statistics = pd.DataFrame({

            "Statistic": [

                "Mean",
                "Median",
                "Maximum",
                "Minimum",
                "Standard Deviation"

            ],

            "Temperature (°C)": [

                target_mean,
                target_median,
                target_max,
                target_min,
                target_std

            ]

        }).round(2)

        st.dataframe(
            overall_statistics,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # DOWNLOAD CSV
        # ----------------------------------------------------
        csv = (
            statistics_table
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "📥 Download Statistics CSV",
            data=csv,
            file_name=(
                f"{selected_station}_"
                f"temperature_statistics_"
                f"{target_year}.csv"
            ),
            mime="text/csv",
            key=(
                f"download_temperature_statistics_"
                f"{selected_station}_{target_year}"
            )
        )

    # ============================================================
    # TAB 5 — DAILY TEMPERATURE
    # ============================================================
    with tabs[4]:

        st.subheader(
            f"📈 Daily Temperature — "
            f"{target_year}"
        )

        daily_plot = (
            target_long
            .sort_values(
                [
                    "Month_Number",
                    "hari"
                ]
            )
            .reset_index(drop=True)
        )

        if daily_plot.empty:

            st.warning(
                "⚠️ Tiada rekod suhu harian "
                "yang sah untuk dipaparkan."
            )

        else:

            fig, ax = plt.subplots(
                figsize=(
                    FIG_WIDTH,
                    FIG_HEIGHT
                )
            )

            fig.patch.set_facecolor(
                BG_COLOR
            )

            ax.set_facecolor(
                BG_COLOR
            )

            ax.plot(
                range(
                    len(daily_plot)
                ),
                daily_plot["Temperature"],
                linewidth=1.2,
                color=LINE_COLOR
            )

            ax.set_title(
                f"{file_name}\n"
                f"Daily Temperature — "
                f"{target_year}",
                fontsize=16,
                fontweight="bold"
            )

            ax.set_xlabel(
                "Daily Observation",
                fontsize=12
            )

            ax.set_ylabel(
                "Temperature (°C)",
                fontsize=12
            )

            ax.set_ylim(
                TEMPERATURE_MIN,
                TEMPERATURE_MAX
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

            # ------------------------------------------------
            # DAILY DATA TABLE
            # ------------------------------------------------
            daily_table = daily_plot[
                [
                    "Year",
                    "Month",
                    "hari",
                    "Temperature"
                ]
            ].copy()

            daily_table.columns = [
                "Year",
                "Month",
                "Day",
                "Temperature (°C)"
            ]

            st.dataframe(
                daily_table.round(2),
                use_container_width=True,
                hide_index=True
            )

            # ------------------------------------------------
            # DOWNLOAD CSV
            # ------------------------------------------------
            csv = (
                daily_table
                .to_csv(index=False)
                .encode("utf-8")
            )

            st.download_button(
                "📥 Download Daily Temperature CSV",
                data=csv,
                file_name=(
                    f"{selected_station}_"
                    f"daily_temperature_"
                    f"{target_year}.csv"
                ),
                mime="text/csv",
                key=(
                    f"download_daily_temperature_"
                    f"{selected_station}_{target_year}"
                )
            )

            plt.close(fig)
# ============================================================
# MAIN TAB 2 — PURATA SEPANJANG TEMPOH
# ============================================================

with main_tabs[1]:

    st.header("📊 Purata Suhu Sepanjang Tempoh")

    # ========================================================
    # PILIH STESEN
    # ========================================================

    selected_station_period = st.selectbox(
        "🏢 Pilih Stesen",
        station_names,
        key="period_station"
    )

    # ========================================================
    # CARI DATA STESEN YANG DIPILIH
    # ========================================================

    selected_period_result = None

    for result in successful_results:
        if result["file_name"] == selected_station_period:
            selected_period_result = result
            break

    if selected_period_result is None:

        st.error(
            f"❌ Data untuk stesen "
            f"'{selected_station_period}' tidak dijumpai."
        )

    else:

        # ====================================================
        # AMBIL DATA STESEN
        # ====================================================

        all_daily_period = (
            selected_period_result["all_daily"]
            .copy()
        )

        original_file_name_period = (
            selected_period_result["original_file_name"]
        )

        read_errors_period = (
            selected_period_result["read_errors"]
        )

        # ====================================================
        # FILTER TEMPOH ANALISIS
        # ====================================================

        period_data = all_daily_period[
            all_daily_period["Year"].between(
                int(START_YEAR),
                int(END_YEAR)
            )
        ].copy()

        # ====================================================
        # CHECK DATA
        # ====================================================

        if period_data.empty:

            st.warning(
                f"⚠️ Tiada data suhu yang sah bagi stesen "
                f"'{selected_station_period}' untuk tempoh "
                f"{START_YEAR} hingga {END_YEAR}."
            )

        else:

            # ====================================================
            # HEADER MAKLUMAT
            # ====================================================

            st.caption(
                f"📍 Stesen: {selected_station_period} | "
                f"📅 Tempoh Analisis: "
                f"{START_YEAR}–{END_YEAR}"
            )

            st.caption(
                f"📁 Fail: {original_file_name_period}"
            )

            # ====================================================
            # PAPAR SHEET YANG ADA ERROR
            # ====================================================

            if read_errors_period:

                with st.expander(
                    "⚠️ Sheet yang tidak berjaya dibaca"
                ):

                    error_df = pd.DataFrame(
                        read_errors_period
                    )

                    st.dataframe(
                        error_df,
                        use_container_width=True,
                        hide_index=True
                    )

            # ====================================================
            # CONVERT WIDE → LONG
            # ====================================================

            period_long = period_data.melt(
                id_vars=[
                    "Year",
                    "hari"
                ],

                value_vars=months,

                var_name="Month",

                value_name="Temperature"
            )

            # ====================================================
            # MONTH NUMBER
            # ====================================================

            month_number = {
                month: i + 1
                for i, month in enumerate(months)
            }

            period_long["Month_Number"] = (
                period_long["Month"]
                .map(month_number)
            )

            # ====================================================
            # DAYS IN MONTH
            # ====================================================

            period_long["Days_In_Month"] = (
                period_long.apply(
                    lambda row:
                        calendar.monthrange(
                            int(row["Year"]),
                            int(row["Month_Number"])
                        )[1],
                    axis=1
                )
            )

            # ====================================================
            # FILTER HARI YANG SAH
            #
            # Contoh:
            # Februari 2024 = maksimum 29 hari
            # Februari 2023 = maksimum 28 hari
            # April = maksimum 30 hari
            # ====================================================

            period_long = period_long[
                period_long["hari"]
                <= period_long["Days_In_Month"]
            ].copy()

            # ====================================================
            # BUANG DATA TEMPERATURE KOSONG
            # ====================================================

            period_long = period_long.dropna(
                subset=["Temperature"]
            ).copy()

            # ====================================================
            # CHECK DATA SELEPAS CLEANING
            # ====================================================

            if period_long.empty:

                st.warning(
                    "⚠️ Tiada data suhu yang sah selepas "
                    "proses pembersihan data."
                )

            else:

                # ====================================================
                # PENGIRAAN
                # ====================================================

                # ----------------------------------------------------
                # PURATA SUHU BULANAN
                # ----------------------------------------------------

                monthly_mean = (
                    period_long
                    .groupby("Month")["Temperature"]
                    .mean()
                    .reindex(months)
                )

                # ----------------------------------------------------
                # SUHU MAKSIMUM BULANAN
                # ----------------------------------------------------

                monthly_max = (
                    period_long
                    .groupby("Month")["Temperature"]
                    .max()
                    .reindex(months)
                )

                # ----------------------------------------------------
                # SUHU MINIMUM BULANAN
                # ----------------------------------------------------

                monthly_min = (
                    period_long
                    .groupby("Month")["Temperature"]
                    .min()
                    .reindex(months)
                )

                # ----------------------------------------------------
                # SISIHAN PIAWAI BULANAN
                # ----------------------------------------------------

                monthly_std = (
                    period_long
                    .groupby("Month")["Temperature"]
                    .std()
                    .reindex(months)
                )

                # ----------------------------------------------------
                # PURATA KESELURUHAN TEMPOH
                #
                # Semua bacaan suhu harian yang sah
                # ----------------------------------------------------

                overall_mean = (
                    period_long["Temperature"]
                    .mean()
                )

                # ----------------------------------------------------
                # MEDIAN
                # ----------------------------------------------------

                overall_median = (
                    period_long["Temperature"]
                    .median()
                )

                # ----------------------------------------------------
                # MAXIMUM KESELURUHAN
                # ----------------------------------------------------

                overall_max = (
                    period_long["Temperature"]
                    .max()
                )

                # ----------------------------------------------------
                # MINIMUM KESELURUHAN
                # ----------------------------------------------------

                overall_min = (
                    period_long["Temperature"]
                    .min()
                )

                # ----------------------------------------------------
                # STANDARD DEVIATION KESELURUHAN
                # ----------------------------------------------------

                overall_std = (
                    period_long["Temperature"]
                    .std()
                )

                # ----------------------------------------------------
                # PURATA SUHU MENGIKUT TAHUN
                # ----------------------------------------------------

                annual_mean = (
                    period_long
                    .groupby("Year")["Temperature"]
                    .mean()
                    .sort_index()
                )

                # ----------------------------------------------------
                # MAXIMUM MENGIKUT TAHUN
                # ----------------------------------------------------

                annual_max = (
                    period_long
                    .groupby("Year")["Temperature"]
                    .max()
                    .sort_index()
                )

                # ----------------------------------------------------
                # MINIMUM MENGIKUT TAHUN
                # ----------------------------------------------------

                annual_min = (
                    period_long
                    .groupby("Year")["Temperature"]
                    .min()
                    .sort_index()
                )

                # ====================================================
                # SUB TABS
                # ====================================================

                period_tabs = st.tabs([
                    "📊 Purata Bulanan",
                    "🔥 Max vs Mean vs Min",
                    "📈 Trend Tahunan",
                    "📋 Statistik",
                    "📉 Sisihan Piawai"
                ])

                # ====================================================
                # TAB 1 — PURATA BULANAN
                # ====================================================

                with period_tabs[0]:

                    st.subheader(
                        f"📊 Purata Suhu Bulanan "
                        f"({START_YEAR}–{END_YEAR})"
                    )

                    fig, ax = plt.subplots(
                        figsize=(
                            FIG_WIDTH,
                            FIG_HEIGHT
                        )
                    )

                    fig.patch.set_facecolor(
                        BG_COLOR
                    )

                    ax.set_facecolor(
                        BG_COLOR
                    )

                    bars = ax.bar(
                        months,
                        monthly_mean.values,
                        color=LINE_COLOR,
                        edgecolor="black",
                        linewidth=0.8
                    )

                    ax.set_title(
                        f"{selected_station_period}\n"
                        f"Purata Suhu Bulanan "
                        f"({START_YEAR}–{END_YEAR})",
                        fontsize=16,
                        fontweight="bold"
                    )

                    ax.set_xlabel(
                        "Bulan",
                        fontsize=12
                    )

                    ax.set_ylabel(
                        "Purata Suhu (°C)",
                        fontsize=12
                    )

                    ax.set_ylim(
                        TEMPERATURE_MIN,
                        TEMPERATURE_MAX
                    )

                    ax.grid(
                        axis="y",
                        linestyle="--",
                        alpha=0.3
                    )

                    # ------------------------------------------------
                    # LABEL NILAI
                    # ------------------------------------------------

                    for bar, value in zip(
                        bars,
                        monthly_mean.values
                    ):

                        if pd.notna(value):

                            ax.text(
                                bar.get_x()
                                + bar.get_width() / 2,

                                value,

                                f"{value:.1f}°C",

                                ha="center",
                                va="bottom",
                                fontsize=10,
                                fontweight="bold"
                            )

                    plt.tight_layout()

                    st.pyplot(
                        fig,
                        use_container_width=True
                    )

                    plt.close(fig)

                    # ------------------------------------------------
                    # TABLE
                    # ------------------------------------------------

                    monthly_table = pd.DataFrame({

                        "Bulan":
                            months,

                        "Purata Suhu (°C)":
                            monthly_mean.values

                    }).round(2)

                    st.dataframe(
                        monthly_table,
                        use_container_width=True,
                        hide_index=True
                    )

                    # ------------------------------------------------
                    # DOWNLOAD
                    # ------------------------------------------------

                    csv = (
                        monthly_table
                        .to_csv(index=False)
                        .encode("utf-8")
                    )

                    st.download_button(
                        "📥 Download Purata Bulanan CSV",

                        data=csv,

                        file_name=(
                            f"{selected_station_period}_"
                            f"purata_suhu_bulanan_"
                            f"{START_YEAR}_{END_YEAR}.csv"
                        ),

                        mime="text/csv",

                        key=(
                            f"download_period_monthly_"
                            f"{selected_station_period}"
                        )
                    )

                # ====================================================
                # TAB 2 — MAX VS MEAN VS MIN
                # ====================================================

                with period_tabs[1]:

                    st.subheader(
                        f"🔥 Suhu Maksimum, Purata dan Minimum "
                        f"({START_YEAR}–{END_YEAR})"
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

                    fig.patch.set_facecolor(
                        BG_COLOR
                    )

                    ax.set_facecolor(
                        BG_COLOR
                    )

                    ax.plot(
                        x,
                        monthly_max.values,
                        marker="^",
                        linewidth=2.5,
                        markersize=7,
                        color=MAX_COLOR,
                        label="Maximum"
                    )

                    ax.plot(
                        x,
                        monthly_mean.values,
                        marker="o",
                        linewidth=2.5,
                        markersize=7,
                        color=LINE_COLOR,
                        label="Mean"
                    )

                    ax.plot(
                        x,
                        monthly_min.values,
                        marker="v",
                        linewidth=2.5,
                        markersize=7,
                        color=MIN_COLOR,
                        label="Minimum"
                    )

                    # ------------------------------------------------
                    # LABEL PURATA
                    # ------------------------------------------------

                    for i, value in enumerate(
                        monthly_mean.values
                    ):

                        if pd.notna(value):

                            ax.annotate(
                                f"{value:.1f}",
                                (
                                    i,
                                    value
                                ),
                                xytext=(0, 9),
                                textcoords="offset points",
                                ha="center",
                                fontsize=9,
                                fontweight="bold"
                            )

                    ax.set_title(
                        f"{selected_station_period}\n"
                        f"Maximum, Mean dan Minimum "
                        f"Suhu Bulanan "
                        f"({START_YEAR}–{END_YEAR})",
                        fontsize=16,
                        fontweight="bold"
                    )

                    ax.set_xlabel(
                        "Bulan",
                        fontsize=12
                    )

                    ax.set_ylabel(
                        "Suhu (°C)",
                        fontsize=12
                    )

                    ax.set_xticks(x)

                    ax.set_xticklabels(
                        months
                    )

                    ax.set_ylim(
                        TEMPERATURE_MIN,
                        TEMPERATURE_MAX
                    )

                    ax.legend(
                        bbox_to_anchor=(1.02, 1),
                        loc="upper left"
                    )

                    ax.grid(
                        axis="y",
                        linestyle="--",
                        alpha=0.3
                    )

                    plt.tight_layout()

                    st.pyplot(
                        fig,
                        use_container_width=True
                    )

                    plt.close(fig)

                    # ------------------------------------------------
                    # TABLE
                    # ------------------------------------------------

                    comparison_table = pd.DataFrame({

                        "Bulan":
                            months,

                        "Maximum (°C)":
                            monthly_max.values,

                        "Mean (°C)":
                            monthly_mean.values,

                        "Minimum (°C)":
                            monthly_min.values

                    }).round(2)

                    st.dataframe(
                        comparison_table,
                        use_container_width=True,
                        hide_index=True
                    )

                    csv = (
                        comparison_table
                        .to_csv(index=False)
                        .encode("utf-8")
                    )

                    st.download_button(
                        "📥 Download Max Mean Min CSV",

                        data=csv,

                        file_name=(
                            f"{selected_station_period}_"
                            f"max_mean_min_"
                            f"{START_YEAR}_{END_YEAR}.csv"
                        ),

                        mime="text/csv",

                        key=(
                            f"download_max_mean_min_"
                            f"{selected_station_period}"
                        )
                    )

                # ====================================================
                # TAB 3 — TREND TAHUNAN
                # ====================================================

                with period_tabs[2]:

                    st.subheader(
                        f"📈 Trend Purata Suhu Tahunan "
                        f"({START_YEAR}–{END_YEAR})"
                    )

                    fig, ax = plt.subplots(
                        figsize=(
                            FIG_WIDTH,
                            FIG_HEIGHT
                        )
                    )

                    fig.patch.set_facecolor(
                        BG_COLOR
                    )

                    ax.set_facecolor(
                        BG_COLOR
                    )

                    # ------------------------------------------------
                    # PURATA TAHUNAN
                    # ------------------------------------------------

                    ax.plot(
                        annual_mean.index,
                        annual_mean.values,
                        marker="o",
                        linewidth=2.5,
                        markersize=6,
                        color=LINE_COLOR,
                        label="Purata Suhu"
                    )

                    # ------------------------------------------------
                    # TREND LINEAR
                    # ------------------------------------------------

                    valid = annual_mean.dropna()

                    if len(valid) >= 2:

                        x_trend = (
                            valid.index
                            .astype(float)
                            .values
                        )

                        y_trend = (
                            valid.values
                        )

                        coefficients = np.polyfit(
                            x_trend,
                            y_trend,
                            1
                        )

                        trend = np.poly1d(
                            coefficients
                        )

                        ax.plot(
                            x_trend,
                            trend(x_trend),
                            linestyle="--",
                            linewidth=2,
                            color=MAX_COLOR,
                            label="Trend Linear"
                        )

                    ax.set_title(
                        f"{selected_station_period}\n"
                        f"Purata Suhu Tahunan "
                        f"({START_YEAR}–{END_YEAR})",
                        fontsize=16,
                        fontweight="bold"
                    )

                    ax.set_xlabel(
                        "Tahun",
                        fontsize=12
                    )

                    ax.set_ylabel(
                        "Purata Suhu (°C)",
                        fontsize=12
                    )

                    ax.set_ylim(
                        TEMPERATURE_MIN,
                        TEMPERATURE_MAX
                    )

                    ax.legend()

                    ax.grid(
                        axis="y",
                        linestyle="--",
                        alpha=0.3
                    )

                    plt.tight_layout()

                    st.pyplot(
                        fig,
                        use_container_width=True
                    )

                    plt.close(fig)

                    # ------------------------------------------------
                    # METRICS
                    # ------------------------------------------------

                    col1, col2, col3 = st.columns(3)

                    with col1:

                        st.metric(
                            "Purata Keseluruhan",
                            f"{overall_mean:.2f} °C"
                        )

                    with col2:

                        highest_year = (
                            annual_mean
                            .idxmax()
                        )

                        highest_value = (
                            annual_mean
                            .max()
                        )

                        st.metric(
                            "Tahun Purata Tertinggi",
                            str(highest_year),
                            f"{highest_value:.2f} °C"
                        )

                    with col3:

                        lowest_year = (
                            annual_mean
                            .idxmin()
                        )

                        lowest_value = (
                            annual_mean
                            .min()
                        )

                        st.metric(
                            "Tahun Purata Terendah",
                            str(lowest_year),
                            f"{lowest_value:.2f} °C"
                        )

                    # ------------------------------------------------
                    # TABLE
                    # ------------------------------------------------

                    annual_table = pd.DataFrame({

                        "Tahun":
                            annual_mean.index,

                        "Purata Suhu (°C)":
                            annual_mean.values,

                        "Maximum (°C)":
                            annual_max
                            .reindex(
                                annual_mean.index
                            )
                            .values,

                        "Minimum (°C)":
                            annual_min
                            .reindex(
                                annual_mean.index
                            )
                            .values

                    }).round(2)

                    st.dataframe(
                        annual_table,
                        use_container_width=True,
                        hide_index=True
                    )

                    csv = (
                        annual_table
                        .to_csv(index=False)
                        .encode("utf-8")
                    )

                    st.download_button(
                        "📥 Download Trend Tahunan CSV",

                        data=csv,

                        file_name=(
                            f"{selected_station_period}_"
                            f"trend_tahunan_"
                            f"{START_YEAR}_{END_YEAR}.csv"
                        ),

                        mime="text/csv",

                        key=(
                            f"download_annual_trend_"
                            f"{selected_station_period}"
                        )
                    )

                # ====================================================
                # TAB 4 — STATISTIK
                # ====================================================

                with period_tabs[3]:

                    st.subheader(
                        f"📋 Statistik Suhu "
                        f"({START_YEAR}–{END_YEAR})"
                    )

                    # ------------------------------------------------
                    # METRICS
                    # ------------------------------------------------

                    col1, col2, col3, col4, col5 = (
                        st.columns(5)
                    )

                    with col1:

                        st.metric(
                            "Purata",
                            f"{overall_mean:.2f} °C"
                        )

                    with col2:

                        st.metric(
                            "Median",
                            f"{overall_median:.2f} °C"
                        )

                    with col3:

                        st.metric(
                            "Maximum",
                            f"{overall_max:.2f} °C"
                        )

                    with col4:

                        st.metric(
                            "Minimum",
                            f"{overall_min:.2f} °C"
                        )

                    with col5:

                        st.metric(
                            "Sisihan Piawai",
                            f"{overall_std:.2f} °C"
                        )

                    st.markdown("---")

                    # ------------------------------------------------
                    # STATISTICS TABLE
                    # ------------------------------------------------

                    statistics_table = pd.DataFrame({

                        "Statistik": [
                            "Bilangan Data",
                            "Purata",
                            "Median",
                            "Maximum",
                            "Minimum",
                            "Sisihan Piawai"
                        ],

                        "Nilai": [
                            f"{len(period_long):,}",
                            f"{overall_mean:.2f} °C",
                            f"{overall_median:.2f} °C",
                            f"{overall_max:.2f} °C",
                            f"{overall_min:.2f} °C",
                            f"{overall_std:.2f} °C"
                        ]

                    })

                    st.dataframe(
                        statistics_table,
                        use_container_width=True,
                        hide_index=True
                    )

                    # ------------------------------------------------
                    # MONTHLY STATISTICS
                    # ------------------------------------------------

                    st.markdown(
                        "### 📊 Statistik Mengikut Bulan"
                    )

                    monthly_statistics = pd.DataFrame({

                        "Bulan":
                            months,

                        "Purata (°C)":
                            monthly_mean.values,

                        "Maximum (°C)":
                            monthly_max.values,

                        "Minimum (°C)":
                            monthly_min.values,

                        "Sisihan Piawai (°C)":
                            monthly_std.values

                    }).round(2)

                    st.dataframe(
                        monthly_statistics,
                        use_container_width=True,
                        hide_index=True
                    )

                    csv = (
                        monthly_statistics
                        .to_csv(index=False)
                        .encode("utf-8")
                    )

                    st.download_button(
                        "📥 Download Statistik CSV",

                        data=csv,

                        file_name=(
                            f"{selected_station_period}_"
                            f"statistik_suhu_"
                            f"{START_YEAR}_{END_YEAR}.csv"
                        ),

                        mime="text/csv",

                        key=(
                            f"download_period_statistics_"
                            f"{selected_station_period}"
                        )
                    )

                # ====================================================
                # TAB 5 — SISIHAN PIAWAI
                # ====================================================

                with period_tabs[4]:

                    st.subheader(
                        f"📉 Sisihan Piawai Suhu Bulanan "
                        f"({START_YEAR}–{END_YEAR})"
                    )

                    fig, ax = plt.subplots(
                        figsize=(
                            FIG_WIDTH,
                            FIG_HEIGHT
                        )
                    )

                    fig.patch.set_facecolor(
                        BG_COLOR
                    )

                    ax.set_facecolor(
                        BG_COLOR
                    )

                    bars = ax.bar(
                        months,
                        monthly_std.values,
                        color=st.session_state.hist_color,
                        edgecolor="black",
                        linewidth=0.8
                    )

                    ax.set_title(
                        f"{selected_station_period}\n"
                        f"Sisihan Piawai Suhu Bulanan "
                        f"({START_YEAR}–{END_YEAR})",
                        fontsize=16,
                        fontweight="bold"
                    )

                    ax.set_xlabel(
                        "Bulan",
                        fontsize=12
                    )

                    ax.set_ylabel(
                        "Sisihan Piawai (°C)",
                        fontsize=12
                    )

                    ax.grid(
                        axis="y",
                        linestyle="--",
                        alpha=0.3
                    )

                    # ------------------------------------------------
                    # LABEL
                    # ------------------------------------------------

                    for bar, value in zip(
                        bars,
                        monthly_std.values
                    ):

                        if pd.notna(value):

                            ax.text(
                                bar.get_x()
                                + bar.get_width() / 2,

                                value,

                                f"{value:.2f}",

                                ha="center",
                                va="bottom",
                                fontsize=10,
                                fontweight="bold"
                            )

                    plt.tight_layout()

                    st.pyplot(
                        fig,
                        use_container_width=True
                    )

                    plt.close(fig)

                    # ------------------------------------------------
                    # TABLE
                    # ------------------------------------------------

                    std_table = pd.DataFrame({

                        "Bulan":
                            months,

                        "Sisihan Piawai (°C)":
                            monthly_std.values

                    }).round(2)

                    st.dataframe(
                        std_table,
                        use_container_width=True,
                        hide_index=True
                    )

                    csv = (
                        std_table
                        .to_csv(index=False)
                        .encode("utf-8")
                    )

                    st.download_button(
                        "📥 Download Sisihan Piawai CSV",

                        data=csv,

                        file_name=(
                            f"{selected_station_period}_"
                            f"sisihan_piawai_"
                            f"{START_YEAR}_{END_YEAR}.csv"
                        ),

                        mime="text/csv",

                        key=(
                            f"download_period_std_"
                            f"{selected_station_period}"
                        )
                    )
# ============================================================
# MAIN TAB 3 — PERBANDINGAN DATA STESEN
# ============================================================

with main_tabs[2]:

    st.header("🏢 Perbandingan Data Suhu Antara Stesen")

    # ========================================================
    # SEMAK BILANGAN STESEN
    # ========================================================

    if len(station_names) < 2:

        st.warning(
            "⚠️ Sila upload sekurang-kurangnya dua fail "
            "untuk membuat perbandingan antara stesen."
        )

    else:

        # ====================================================
        # PILIH DUA STESEN
        # ====================================================

        col1, col2 = st.columns(2)

        with col1:

            station_a = st.selectbox(
                "🏢 Stesen A",
                station_names,
                index=0,
                key="comparison_station_a"
            )

        with col2:

            station_b_options = [
                station
                for station in station_names
                if station != station_a
            ]

            station_b = st.selectbox(
                "🏢 Stesen B",
                station_b_options,
                index=0,
                key="comparison_station_b"
            )

        # ====================================================
        # FUNCTION CARI RESULT BERDASARKAN NAMA STESEN
        # ====================================================

        def get_station_result(station_name):

            for result in successful_results:

                if result["file_name"] == station_name:
                    return result

            return None

        # ====================================================
        # AMBIL DATA STESEN
        # ====================================================

        result_a = get_station_result(
            station_a
        )

        result_b = get_station_result(
            station_b
        )

        if result_a is None or result_b is None:

            st.error(
                "❌ Data bagi salah satu stesen tidak dijumpai."
            )

        else:

            data_a = (
                result_a["all_daily"]
                .copy()
            )

            data_b = (
                result_b["all_daily"]
                .copy()
            )

            # ====================================================
            # FILTER TEMPOH ANALISIS
            # ====================================================

            data_a = data_a[
                data_a["Year"].between(
                    int(START_YEAR),
                    int(END_YEAR)
                )
            ].copy()

            data_b = data_b[
                data_b["Year"].between(
                    int(START_YEAR),
                    int(END_YEAR)
                )
            ].copy()

            # ====================================================
            # FUNCTION WIDE → LONG
            # ====================================================

            def prepare_temperature_long(
                df,
                station_name
            ):

                if df.empty:
                    return pd.DataFrame()

                long_df = df.melt(
                    id_vars=[
                        "Year",
                        "hari"
                    ],

                    value_vars=months,

                    var_name="Month",

                    value_name="Temperature"
                )

                # ------------------------------------------------
                # MONTH NUMBER
                # ------------------------------------------------

                month_number = {
                    month: i + 1
                    for i, month in enumerate(months)
                }

                long_df["Month_Number"] = (
                    long_df["Month"]
                    .map(month_number)
                )

                # ------------------------------------------------
                # DAYS IN MONTH
                # ------------------------------------------------

                long_df["Days_In_Month"] = (
                    long_df.apply(
                        lambda row:
                            calendar.monthrange(
                                int(row["Year"]),
                                int(row["Month_Number"])
                            )[1],
                        axis=1
                    )
                )

                # ------------------------------------------------
                # REMOVE INVALID DAYS
                # ------------------------------------------------

                long_df = long_df[
                    long_df["hari"]
                    <= long_df["Days_In_Month"]
                ].copy()

                # ------------------------------------------------
                # REMOVE MISSING TEMPERATURE
                # ------------------------------------------------

                long_df = long_df.dropna(
                    subset=["Temperature"]
                ).copy()

                # ------------------------------------------------
                # STATION
                # ------------------------------------------------

                long_df["Station"] = (
                    station_name
                )

                # ------------------------------------------------
                # CREATE DATE
                # ------------------------------------------------

                long_df["Date"] = pd.to_datetime(
                    dict(
                        year=long_df["Year"].astype(int),
                        month=long_df[
                            "Month_Number"
                        ].astype(int),
                        day=long_df["hari"].astype(int)
                    ),
                    errors="coerce"
                )

                long_df = long_df.dropna(
                    subset=["Date"]
                ).copy()

                return long_df

            # ====================================================
            # PREPARE DATA
            # ====================================================

            long_a = prepare_temperature_long(
                data_a,
                station_a
            )

            long_b = prepare_temperature_long(
                data_b,
                station_b
            )

            # ====================================================
            # SEMAK DATA
            # ====================================================

            if long_a.empty or long_b.empty:

                st.warning(
                    "⚠️ Data suhu tidak mencukupi untuk membuat "
                    "perbandingan antara kedua-dua stesen."
                )

            else:

                # =================================================
                # PURATA BULANAN STESEN A
                # =================================================

                mean_a = (
                    long_a
                    .groupby("Month")[
                        "Temperature"
                    ]
                    .mean()
                    .reindex(months)
                )

                # =================================================
                # MAXIMUM BULANAN STESEN A
                # =================================================

                max_a = (
                    long_a
                    .groupby("Month")[
                        "Temperature"
                    ]
                    .max()
                    .reindex(months)
                )

                # =================================================
                # MINIMUM BULANAN STESEN A
                # =================================================

                min_a = (
                    long_a
                    .groupby("Month")[
                        "Temperature"
                    ]
                    .min()
                    .reindex(months)
                )

                # =================================================
                # PURATA BULANAN STESEN B
                # =================================================

                mean_b = (
                    long_b
                    .groupby("Month")[
                        "Temperature"
                    ]
                    .mean()
                    .reindex(months)
                )

                # =================================================
                # MAXIMUM BULANAN STESEN B
                # =================================================

                max_b = (
                    long_b
                    .groupby("Month")[
                        "Temperature"
                    ]
                    .max()
                    .reindex(months)
                )

                # =================================================
                # MINIMUM BULANAN STESEN B
                # =================================================

                min_b = (
                    long_b
                    .groupby("Month")[
                        "Temperature"
                    ]
                    .min()
                    .reindex(months)
                )

                # =================================================
                # PURATA TAHUNAN
                # =================================================

                annual_a = (
                    long_a
                    .groupby("Year")[
                        "Temperature"
                    ]
                    .mean()
                    .sort_index()
                )

                annual_b = (
                    long_b
                    .groupby("Year")[
                        "Temperature"
                    ]
                    .mean()
                    .sort_index()
                )

                # =================================================
                # TAHUN YANG SAMA
                # =================================================

                common_years = sorted(
                    set(annual_a.index)
                    .intersection(
                        set(annual_b.index)
                    )
                )

                # =================================================
                # SUB TABS
                # =================================================

                comparison_tabs = st.tabs([
                    "📊 Purata Bulanan",
                    "🔥 Maximum & Minimum",
                    "📉 Perbezaan Suhu",
                    "📈 Trend Tahunan",
                    "📋 Error Analysis"
                ])

                # =================================================
                # TAB 1 — PURATA BULANAN
                # =================================================

                with comparison_tabs[0]:

                    st.subheader(
                        f"📊 Perbandingan Purata Suhu Bulanan "
                        f"({START_YEAR}–{END_YEAR})"
                    )

                    x = np.arange(
                        len(months)
                    )

                    width = 0.35

                    fig, ax = plt.subplots(
                        figsize=(
                            FIG_WIDTH,
                            FIG_HEIGHT
                        )
                    )

                    fig.patch.set_facecolor(
                        BG_COLOR
                    )

                    ax.set_facecolor(
                        BG_COLOR
                    )

                    bars_a = ax.bar(
                        x - width / 2,
                        mean_a.values,
                        width,
                        color=LINE_COLOR,
                        edgecolor="black",
                        label=station_a
                    )

                    bars_b = ax.bar(
                        x + width / 2,
                        mean_b.values,
                        width,
                        color=MAX_COLOR,
                        edgecolor="black",
                        label=station_b
                    )

                    ax.set_title(
                        f"Purata Suhu Bulanan\n"
                        f"{station_a} vs {station_b}",
                        fontsize=16,
                        fontweight="bold"
                    )

                    ax.set_xlabel(
                        "Bulan"
                    )

                    ax.set_ylabel(
                        "Purata Suhu (°C)"
                    )

                    ax.set_xticks(
                        x
                    )

                    ax.set_xticklabels(
                        months
                    )

                    ax.set_ylim(
                        TEMPERATURE_MIN,
                        TEMPERATURE_MAX
                    )

                    ax.legend()

                    ax.grid(
                        axis="y",
                        linestyle="--",
                        alpha=0.3
                    )

                    plt.tight_layout()

                    st.pyplot(
                        fig,
                        use_container_width=True
                    )

                    plt.close(fig)

                    # ------------------------------------------------
                    # TABLE
                    # ------------------------------------------------

                    table_mean = pd.DataFrame({

                        "Bulan":
                            months,

                        f"{station_a} (°C)":
                            mean_a.values,

                        f"{station_b} (°C)":
                            mean_b.values,

                        "Perbezaan A-B (°C)":
                            (
                                mean_a.values
                                - mean_b.values
                            )

                    }).round(2)

                    st.dataframe(
                        table_mean,
                        use_container_width=True,
                        hide_index=True
                    )

                    # ------------------------------------------------
                    # DOWNLOAD
                    # ------------------------------------------------

                    csv = (
                        table_mean
                        .to_csv(index=False)
                        .encode("utf-8")
                    )

                    st.download_button(
                        "📥 Download Purata Bulanan CSV",
                        data=csv,
                        file_name=(
                            f"{station_a}_vs_"
                            f"{station_b}_"
                            f"purata_bulanan.csv"
                        ),
                        mime="text/csv",
                        key="download_comparison_mean"
                    )

                # =================================================
                # TAB 2 — MAXIMUM & MINIMUM
                # =================================================

                with comparison_tabs[1]:

                    st.subheader(
                        "🔥 Perbandingan Suhu Maximum "
                        "dan Minimum"
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

                    fig.patch.set_facecolor(
                        BG_COLOR
                    )

                    ax.set_facecolor(
                        BG_COLOR
                    )

                    # ------------------------------------------------
                    # STATION A MAX
                    # ------------------------------------------------

                    ax.plot(
                        x,
                        max_a.values,
                        marker="^",
                        linewidth=2,
                        color=MAX_COLOR,
                        label=f"{station_a} Maximum"
                    )

                    # ------------------------------------------------
                    # STATION A MIN
                    # ------------------------------------------------

                    ax.plot(
                        x,
                        min_a.values,
                        marker="v",
                        linewidth=2,
                        color=MIN_COLOR,
                        label=f"{station_a} Minimum"
                    )

                    # ------------------------------------------------
                    # STATION B MAX
                    # ------------------------------------------------

                    ax.plot(
                        x,
                        max_b.values,
                        marker="^",
                        linestyle="--",
                        linewidth=2,
                        color="darkorange",
                        label=f"{station_b} Maximum"
                    )

                    # ------------------------------------------------
                    # STATION B MIN
                    # ------------------------------------------------

                    ax.plot(
                        x,
                        min_b.values,
                        marker="v",
                        linestyle="--",
                        linewidth=2,
                        color="purple",
                        label=f"{station_b} Minimum"
                    )

                    ax.set_title(
                        f"Maximum dan Minimum Suhu Bulanan\n"
                        f"{station_a} vs {station_b}",
                        fontsize=16,
                        fontweight="bold"
                    )

                    ax.set_xlabel(
                        "Bulan"
                    )

                    ax.set_ylabel(
                        "Suhu (°C)"
                    )

                    ax.set_xticks(
                        x
                    )

                    ax.set_xticklabels(
                        months
                    )

                    ax.set_ylim(
                        TEMPERATURE_MIN,
                        TEMPERATURE_MAX
                    )

                    ax.legend(
                        bbox_to_anchor=(1.02, 1),
                        loc="upper left"
                    )

                    ax.grid(
                        axis="y",
                        linestyle="--",
                        alpha=0.3
                    )

                    plt.tight_layout()

                    st.pyplot(
                        fig,
                        use_container_width=True
                    )

                    plt.close(fig)

                    # ------------------------------------------------
                    # TABLE
                    # ------------------------------------------------

                    max_min_table = pd.DataFrame({

                        "Bulan":
                            months,

                        f"{station_a} Max (°C)":
                            max_a.values,

                        f"{station_a} Min (°C)":
                            min_a.values,

                        f"{station_b} Max (°C)":
                            max_b.values,

                        f"{station_b} Min (°C)":
                            min_b.values

                    }).round(2)

                    st.dataframe(
                        max_min_table,
                        use_container_width=True,
                        hide_index=True
                    )

                    csv = (
                        max_min_table
                        .to_csv(index=False)
                        .encode("utf-8")
                    )

                    st.download_button(
                        "📥 Download Maximum & Minimum CSV",
                        data=csv,
                        file_name=(
                            f"{station_a}_vs_"
                            f"{station_b}_"
                            f"maximum_minimum.csv"
                        ),
                        mime="text/csv",
                        key="download_comparison_max_min"
                    )

                # =================================================
                # TAB 3 — PERBEZAAN SUHU
                # =================================================

                with comparison_tabs[2]:

                    st.subheader(
                        f"📉 Perbezaan Purata Suhu "
                        f"({station_a} − {station_b})"
                    )

                    monthly_difference = (
                        mean_a - mean_b
                    )

                    difference_values = (
                        monthly_difference.values
                    )

                    fig, ax = plt.subplots(
                        figsize=(
                            FIG_WIDTH,
                            FIG_HEIGHT
                        )
                    )

                    fig.patch.set_facecolor(
                        BG_COLOR
                    )

                    ax.set_facecolor(
                        BG_COLOR
                    )

                    difference_colors = [
                        LINE_COLOR
                        if pd.notna(value)
                        and value >= 0
                        else MIN_COLOR
                        if pd.notna(value)
                        else "lightgray"
                        for value
                        in difference_values
                    ]

                    bars = ax.bar(
                        months,
                        difference_values,
                        color=difference_colors,
                        edgecolor="black",
                        linewidth=0.8
                    )

                    ax.axhline(
                        0,
                        color="black",
                        linewidth=1
                    )

                    ax.set_title(
                        f"Perbezaan Purata Suhu\n"
                        f"{station_a} − {station_b}",
                        fontsize=16,
                        fontweight="bold"
                    )

                    ax.set_xlabel(
                        "Bulan"
                    )

                    ax.set_ylabel(
                        "Perbezaan Suhu (°C)"
                    )

                    ax.grid(
                        axis="y",
                        linestyle="--",
                        alpha=0.3
                    )

                    # ------------------------------------------------
                    # LABEL
                    # ------------------------------------------------

                    for bar, value in zip(
                        bars,
                        difference_values
                    ):

                        if pd.notna(value):

                            if value >= 0:
                                offset = 4
                                va = "bottom"
                            else:
                                offset = -12
                                va = "top"

                            ax.annotate(
                                f"{value:.2f}°C",

                                (
                                    bar.get_x()
                                    + bar.get_width() / 2,
                                    value
                                ),

                                xytext=(
                                    0,
                                    offset
                                ),

                                textcoords=(
                                    "offset points"
                                ),

                                ha="center",
                                va=va,
                                fontsize=9,
                                fontweight="bold"
                            )

                    plt.tight_layout()

                    st.pyplot(
                        fig,
                        use_container_width=True
                    )

                    plt.close(fig)

                    # ------------------------------------------------
                    # METRICS
                    # ------------------------------------------------

                    valid_difference = (
                        monthly_difference
                        .dropna()
                    )

                    if not valid_difference.empty:

                        col1, col2, col3 = (
                            st.columns(3)
                        )

                        with col1:

                            st.metric(
                                "Purata Perbezaan",
                                f"{valid_difference.mean():.2f} °C"
                            )

                        with col2:

                            st.metric(
                                "Perbezaan Maksimum",
                                f"{valid_difference.max():.2f} °C"
                            )

                        with col3:

                            st.metric(
                                "Perbezaan Minimum",
                                f"{valid_difference.min():.2f} °C"
                            )

                    # ------------------------------------------------
                    # TABLE
                    # ------------------------------------------------

                    difference_table = pd.DataFrame({

                        "Bulan":
                            months,

                        f"{station_a} (°C)":
                            mean_a.values,

                        f"{station_b} (°C)":
                            mean_b.values,

                        "Perbezaan A-B (°C)":
                            monthly_difference.values

                    }).round(2)

                    st.dataframe(
                        difference_table,
                        use_container_width=True,
                        hide_index=True
                    )

                    csv = (
                        difference_table
                        .to_csv(index=False)
                        .encode("utf-8")
                    )

                    st.download_button(
                        "📥 Download Perbezaan CSV",
                        data=csv,
                        file_name=(
                            f"{station_a}_vs_"
                            f"{station_b}_"
                            f"perbezaan_suhu.csv"
                        ),
                        mime="text/csv",
                        key="download_comparison_difference"
                    )

                # =================================================
                # TAB 4 — TREND TAHUNAN
                # =================================================

                with comparison_tabs[3]:

                    st.subheader(
                        f"📈 Trend Purata Suhu Tahunan "
                        f"({START_YEAR}–{END_YEAR})"
                    )

                    if len(common_years) == 0:

                        st.warning(
                            "⚠️ Tiada tahun yang sama antara "
                            "kedua-dua stesen dalam tempoh "
                            "yang dipilih."
                        )

                    else:

                        annual_a_common = (
                            annual_a
                            .reindex(common_years)
                        )

                        annual_b_common = (
                            annual_b
                            .reindex(common_years)
                        )

                        fig, ax = plt.subplots(
                            figsize=(
                                FIG_WIDTH,
                                FIG_HEIGHT
                            )
                        )

                        fig.patch.set_facecolor(
                            BG_COLOR
                        )

                        ax.set_facecolor(
                            BG_COLOR
                        )

                        ax.plot(
                            common_years,
                            annual_a_common.values,
                            marker="o",
                            linewidth=2.5,
                            color=LINE_COLOR,
                            label=station_a
                        )

                        ax.plot(
                            common_years,
                            annual_b_common.values,
                            marker="s",
                            linewidth=2.5,
                            color=MAX_COLOR,
                            label=station_b
                        )

                        ax.set_title(
                            f"Trend Purata Suhu Tahunan\n"
                            f"{station_a} vs {station_b}",
                            fontsize=16,
                            fontweight="bold"
                        )

                        ax.set_xlabel(
                            "Tahun"
                        )

                        ax.set_ylabel(
                            "Purata Suhu (°C)"
                        )

                        ax.set_ylim(
                            TEMPERATURE_MIN,
                            TEMPERATURE_MAX
                        )

                        ax.legend()

                        ax.grid(
                            axis="y",
                            linestyle="--",
                            alpha=0.3
                        )

                        plt.tight_layout()

                        st.pyplot(
                            fig,
                            use_container_width=True
                        )

                        plt.close(fig)

                        # --------------------------------------------
                        # TABLE
                        # --------------------------------------------

                        annual_comparison = pd.DataFrame({

                            "Tahun":
                                common_years,

                            f"{station_a} (°C)":
                                annual_a_common.values,

                            f"{station_b} (°C)":
                                annual_b_common.values,

                            "Perbezaan A-B (°C)":
                                (
                                    annual_a_common.values
                                    - annual_b_common.values
                                )

                        }).round(2)

                        st.dataframe(
                            annual_comparison,
                            use_container_width=True,
                            hide_index=True
                        )

                        csv = (
                            annual_comparison
                            .to_csv(index=False)
                            .encode("utf-8")
                        )

                        st.download_button(
                            "📥 Download Trend Tahunan CSV",
                            data=csv,
                            file_name=(
                                f"{station_a}_vs_"
                                f"{station_b}_"
                                f"trend_tahunan.csv"
                            ),
                            mime="text/csv",
                            key="download_comparison_annual"
                        )

                # =================================================
                # TAB 5 — ERROR ANALYSIS
                # =================================================

                with comparison_tabs[4]:

                    st.subheader(
                        "📋 Error Analysis Antara Stesen"
                    )

                    # =================================================
                    # PADANKAN TARIKH YANG SAMA
                    # =================================================

                    daily_a = long_a[
                        [
                            "Date",
                            "Year",
                            "Month",
                            "hari",
                            "Temperature"
                        ]
                    ].copy()

                    daily_b = long_b[
                        [
                            "Date",
                            "Year",
                            "Month",
                            "hari",
                            "Temperature"
                        ]
                    ].copy()

                    daily_a = daily_a.rename(
                        columns={
                            "Temperature":
                                "Temperature_A"
                        }
                    )

                    daily_b = daily_b.rename(
                        columns={
                            "Temperature":
                                "Temperature_B"
                        }
                    )

                    merged_daily = pd.merge(
                        daily_a,
                        daily_b,

                        on=[
                            "Date",
                            "Year",
                            "Month",
                            "hari"
                        ],

                        how="inner"
                    )

                    merged_daily = (
                        merged_daily
                        .dropna(
                            subset=[
                                "Temperature_A",
                                "Temperature_B"
                            ]
                        )
                        .copy()
                    )

                    # =================================================
                    # SEMAK DATA SEPADAN
                    # =================================================

                    if merged_daily.empty:

                        st.warning(
                            "⚠️ Tiada tarikh yang sepadan antara "
                            "kedua-dua stesen."
                        )

                    else:

                        # =============================================
                        # DIFFERENCE
                        # =============================================

                        merged_daily["Difference"] = (
                            merged_daily["Temperature_A"]
                            - merged_daily["Temperature_B"]
                        )

                        # =============================================
                        # ABSOLUTE ERROR
                        # =============================================

                        merged_daily["Absolute_Error"] = (
                            merged_daily["Difference"]
                            .abs()
                        )

                        # =============================================
                        # BIAS
                        # =============================================

                        bias = (
                            merged_daily[
                                "Difference"
                            ].mean()
                        )

                        # =============================================
                        # MAE
                        # =============================================

                        mae = (
                            merged_daily[
                                "Absolute_Error"
                            ].mean()
                        )

                        # =============================================
                        # MAX ABSOLUTE ERROR
                        # =============================================

                        max_absolute_error = (
                            merged_daily[
                                "Absolute_Error"
                            ].max()
                        )

                        # =============================================
                        # NUMBER OF MATCHED DATA
                        # =============================================

                        matched_data = (
                            len(merged_daily)
                        )

                        # =============================================
                        # METRICS
                        # =============================================

                        col1, col2, col3, col4 = (
                            st.columns(4)
                        )

                        with col1:

                            st.metric(
                                "Bias / Mean Difference",
                                f"{bias:.3f} °C"
                            )

                        with col2:

                            st.metric(
                                "MAE",
                                f"{mae:.3f} °C"
                            )

                        with col3:

                            st.metric(
                                "Maximum Absolute Error",
                                f"{max_absolute_error:.3f} °C"
                            )

                        with col4:

                            st.metric(
                                "Bilangan Data",
                                f"{matched_data:,}"
                            )

                        # =============================================
                        # HISTOGRAM ERROR
                        # =============================================

                        st.markdown(
                            "### 📊 Taburan Perbezaan Suhu"
                        )

                        fig, ax = plt.subplots(
                            figsize=(
                                FIG_WIDTH,
                                FIG_HEIGHT
                            )
                        )

                        fig.patch.set_facecolor(
                            BG_COLOR
                        )

                        ax.set_facecolor(
                            BG_COLOR
                        )

                        ax.hist(
                            merged_daily[
                                "Difference"
                            ],
                            bins=20,
                            edgecolor="black",
                            color=st.session_state.hist_color,
                        )

                        ax.axvline(
                            0,
                            color="black",
                            linestyle="--",
                            linewidth=2
                        )

                        ax.axvline(
                            bias,
                            color=MAX_COLOR,
                            linestyle="--",
                            linewidth=2,
                            label=f"Bias = {bias:.3f} °C"
                        )

                        ax.set_title(
                            f"Taburan Perbezaan Suhu\n"
                            f"{station_a} − {station_b}",
                            fontsize=16,
                            fontweight="bold"
                        )

                        ax.set_xlabel(
                            "Perbezaan Suhu (°C)"
                        )

                        ax.set_ylabel(
                            "Bilangan Data"
                        )

                        ax.legend()

                        ax.grid(
                            axis="y",
                            linestyle="--",
                            alpha=0.3
                        )

                        plt.tight_layout()

                        st.pyplot(
                            fig,
                            use_container_width=True
                        )

                        plt.close(fig)

                        # =============================================
                        # ERROR TABLE
                        # =============================================

                        error_table = merged_daily[
                            [
                                "Date",
                                "Year",
                                "Month",
                                "hari",
                                "Temperature_A",
                                "Temperature_B",
                                "Difference",
                                "Absolute_Error"
                            ]
                        ].copy()

                        error_table = (
                            error_table
                            .rename(
                                columns={
                                    "Temperature_A":
                                        station_a,

                                    "Temperature_B":
                                        station_b,

                                    "hari":
                                        "Day"
                                }
                            )
                        )

                        error_table = error_table.round(
                            {
                                station_a: 2,
                                station_b: 2,
                                "Difference": 3,
                                "Absolute_Error": 3
                            }
                        )

                        st.dataframe(
                            error_table,
                            use_container_width=True,
                            hide_index=True
                        )

                        # =============================================
                        # DOWNLOAD ERROR DATA
                        # =============================================

                        csv = (
                            error_table
                            .to_csv(index=False)
                            .encode("utf-8")
                        )

                        st.download_button(
                            "📥 Download Error Analysis CSV",

                            data=csv,

                            file_name=(
                                f"{station_a}_vs_"
                                f"{station_b}_"
                                f"error_analysis.csv"
                            ),

                            mime="text/csv",

                            key=(
                                "download_comparison_error"
                            )
                        )
# ============================================================
# MAIN TAB 4 — SUHU TERTINGGI / EKSTREM
# ============================================================

with main_tabs[3]:

    st.header("🔥 Analisis Suhu Ekstrem")

    # ========================================================
    # PILIH STESEN
    # ========================================================

    selected_station_extreme = st.selectbox(
        "🏢 Pilih Stesen",
        station_names,
        key="extreme_station"
    )

    # ========================================================
    # AMBIL DATA STESEN
    # ========================================================

    selected_extreme_result = None

    for result in successful_results:
        if result["file_name"] == selected_station_extreme:
            selected_extreme_result = result
            break

    if selected_extreme_result is None:

        st.error(
            f"Data stesen '{selected_station_extreme}' "
            f"tidak dapat ditemui."
        )

        st.stop()

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

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
            f"Tiada data suhu bagi tempoh "
            f"{START_YEAR} hingga {END_YEAR}."
        )

        st.stop()

    # ========================================================
    # CONVERT WIDE → LONG
    # ========================================================

    extreme_long = period_data_extreme.melt(
        id_vars=["Year", "hari"],
        value_vars=months,
        var_name="Month",
        value_name="Temperature"
    )

    # ========================================================
    # PASTIKAN DATA NUMERIC
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
    # NOMBOR BULAN
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
    # BILANGAN HARI SEBENAR DALAM BULAN
    # ========================================================

    extreme_long["Days_In_Month"] = extreme_long.apply(
        lambda row: calendar.monthrange(
            int(row["Year"]),
            int(row["Month_Number"])
        )[1],
        axis=1
    )

    # ========================================================
    # BUANG HARI TIDAK SAH
    # Contoh:
    # April 31 → dibuang
    # February 30/31 → dibuang
    # ========================================================

    extreme_long = extreme_long[
        (extreme_long["hari"] >= 1) &
        (extreme_long["hari"] <= extreme_long["Days_In_Month"])
    ].copy()

    # ========================================================
    # BINA TARIKH
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
    # SEMAK DATA
    # ========================================================

    if extreme_long.empty:

        st.warning(
            "Tiada data suhu yang sah untuk dianalisis."
        )

        st.stop()

    # ========================================================
    # PENGIRAAN SUHU EKSTREM
    # ========================================================

    highest_index = (
        extreme_long["Temperature"].idxmax()
    )

    lowest_index = (
        extreme_long["Temperature"].idxmin()
    )

    highest_row = extreme_long.loc[
        highest_index
    ]

    lowest_row = extreme_long.loc[
        lowest_index
    ]

    highest_temperature = (
        highest_row["Temperature"]
    )

    lowest_temperature = (
        lowest_row["Temperature"]
    )

    # ========================================================
    # SUB TABS
    # ========================================================

    extreme_tabs = st.tabs([
        "🌡️ Rekod Ekstrem",
        "🏆 Top 10 Tertinggi",
        "❄️ Top 10 Terendah",
        "📅 Maximum Mengikut Tahun",
        "📈 Trend Maximum"
    ])

    # ========================================================
    # TAB 1 — REKOD EKSTREM
    # ========================================================

    with extreme_tabs[0]:

        st.subheader(
            f"🌡️ Rekod Suhu Ekstrem "
            f"({START_YEAR}–{END_YEAR})"
        )

        # ----------------------------------------------------
        # MAKLUMAT STESEN
        # ----------------------------------------------------

        st.caption(
            f"Stesen: {selected_station_extreme}"
        )

        st.caption(
            f"Tempoh analisis: {START_YEAR}–{END_YEAR}"
        )

        st.markdown("---")

        col1, col2 = st.columns(2)

        # ====================================================
        # SUHU TERTINGGI
        # ====================================================

        with col1:

            st.metric(
                "🔥 Suhu Tertinggi",
                f"{highest_temperature:.1f} °C"
            )

            st.write(
                f"**Tarikh:** "
                f"{highest_row['Date'].strftime('%d/%m/%Y')}"
            )

            st.write(
                f"**Tahun:** "
                f"{int(highest_row['Year'])}"
            )

            st.write(
                f"**Bulan:** "
                f"{highest_row['Month']}"
            )

            st.write(
                f"**Hari:** "
                f"{int(highest_row['hari'])}"
            )

        # ====================================================
        # SUHU TERENDAH
        # ====================================================

        with col2:

            st.metric(
                "❄️ Suhu Terendah",
                f"{lowest_temperature:.1f} °C"
            )

            st.write(
                f"**Tarikh:** "
                f"{lowest_row['Date'].strftime('%d/%m/%Y')}"
            )

            st.write(
                f"**Tahun:** "
                f"{int(lowest_row['Year'])}"
            )

            st.write(
                f"**Bulan:** "
                f"{lowest_row['Month']}"
            )

            st.write(
                f"**Hari:** "
                f"{int(lowest_row['hari'])}"
            )

        # ====================================================
        # RANGE SUHU
        # ====================================================

        st.markdown("---")

        temperature_range = (
            highest_temperature -
            lowest_temperature
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Maximum",
                f"{highest_temperature:.2f} °C"
            )

        with col2:

            st.metric(
                "Minimum",
                f"{lowest_temperature:.2f} °C"
            )

        with col3:

            st.metric(
                "Julat Suhu",
                f"{temperature_range:.2f} °C"
            )

    # ========================================================
    # TAB 2 — TOP 10 SUHU TERTINGGI
    # ========================================================

    with extreme_tabs[1]:

        st.subheader(
            f"🏆 Top 10 Suhu Tertinggi "
            f"({START_YEAR}–{END_YEAR})"
        )

        top10_high = (
            extreme_long
            .nlargest(10, "Temperature")
            .copy()
        )

        top10_high["Tarikh"] = (
            top10_high["Date"]
            .dt.strftime("%d/%m/%Y")
        )

        top10_high = top10_high[
            [
                "Tarikh",
                "Year",
                "Month",
                "Temperature"
            ]
        ].copy()

        top10_high.columns = [
            "Tarikh",
            "Tahun",
            "Bulan",
            "Suhu (°C)"
        ]

        top10_high = (
            top10_high
            .reset_index(drop=True)
        )

        top10_high.index = (
            top10_high.index + 1
        )

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        st.dataframe(
            top10_high,
            use_container_width=True
        )

        # ----------------------------------------------------
        # GRAPH
        # ----------------------------------------------------

        fig, ax = plt.subplots(
            figsize=(FIG_WIDTH, FIG_HEIGHT)
        )

        bars = ax.bar(
            top10_high["Tarikh"],
            top10_high["Suhu (°C)"]
        )

        ax.set_title(
            "Top 10 Suhu Tertinggi",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel("Tarikh")
        ax.set_ylabel("Suhu (°C)")

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.3
        )

        for bar, value in zip(
            bars,
            top10_high["Suhu (°C)"]
        ):

            ax.text(
                bar.get_x() +
                bar.get_width() / 2,
                value,
                f"{value:.1f}",
                ha="center",
                va="bottom"
            )

        plt.xticks(
            rotation=45,
            ha="right"
        )

        plt.tight_layout()

        st.pyplot(fig)

        plt.close(fig)

    # ========================================================
    # TAB 3 — TOP 10 SUHU TERENDAH
    # ========================================================

    with extreme_tabs[2]:

        st.subheader(
            f"❄️ Top 10 Suhu Terendah "
            f"({START_YEAR}–{END_YEAR})"
        )

        top10_low = (
            extreme_long
            .nsmallest(10, "Temperature")
            .copy()
        )

        top10_low["Tarikh"] = (
            top10_low["Date"]
            .dt.strftime("%d/%m/%Y")
        )

        top10_low = top10_low[
            [
                "Tarikh",
                "Year",
                "Month",
                "Temperature"
            ]
        ].copy()

        top10_low.columns = [
            "Tarikh",
            "Tahun",
            "Bulan",
            "Suhu (°C)"
        ]

        top10_low = (
            top10_low
            .reset_index(drop=True)
        )

        top10_low.index = (
            top10_low.index + 1
        )

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        st.dataframe(
            top10_low,
            use_container_width=True
        )

        # ----------------------------------------------------
        # GRAPH
        # ----------------------------------------------------

        fig, ax = plt.subplots(
            figsize=(FIG_WIDTH, FIG_HEIGHT)
        )

        bars = ax.bar(
            top10_low["Tarikh"],
            top10_low["Suhu (°C)"]
        )

        ax.set_title(
            "Top 10 Suhu Terendah",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel("Tarikh")
        ax.set_ylabel("Suhu (°C)")

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.3
        )

        for bar, value in zip(
            bars,
            top10_low["Suhu (°C)"]
        ):

            ax.text(
                bar.get_x() +
                bar.get_width() / 2,
                value,
                f"{value:.1f}",
                ha="center",
                va="bottom"
            )

        plt.xticks(
            rotation=45,
            ha="right"
        )

        plt.tight_layout()

        st.pyplot(fig)

        plt.close(fig)

    # ========================================================
    # TAB 4 — MAXIMUM MENGIKUT TAHUN
    # ========================================================

    with extreme_tabs[3]:

        st.subheader(
            f"📅 Suhu Maximum Mengikut Tahun "
            f"({START_YEAR}–{END_YEAR})"
        )

        annual_max = (
            extreme_long
            .groupby("Year")["Temperature"]
            .max()
            .sort_index()
        )

        if annual_max.empty:

            st.warning(
                "Tiada data maximum tahunan."
            )

        else:

            # ------------------------------------------------
            # GRAPH
            # ------------------------------------------------

            fig, ax = plt.subplots(
                figsize=(FIG_WIDTH, FIG_HEIGHT)
            )

            bars = ax.bar(
                annual_max.index.astype(str),
                annual_max.values
            )

            ax.set_title(
                "Suhu Maximum Mengikut Tahun",
                fontsize=16,
                fontweight="bold"
            )

            ax.set_xlabel("Tahun")
            ax.set_ylabel(
                "Suhu Maximum (°C)"
            )

            ax.grid(
                axis="y",
                linestyle="--",
                alpha=0.3
            )

            # -----------------------------------------------
            # LABEL NILAI
            # -----------------------------------------------

            for bar, value in zip(
                bars,
                annual_max.values
            ):

                ax.text(
                    bar.get_x() +
                    bar.get_width() / 2,
                    value,
                    f"{value:.1f}",
                    ha="center",
                    va="bottom"
                )

            plt.xticks(
                rotation=45
            )

            plt.tight_layout()

            st.pyplot(fig)

            plt.close(fig)

            # ------------------------------------------------
            # TABLE
            # ------------------------------------------------

            annual_max_table = pd.DataFrame({
                "Tahun": annual_max.index.astype(int),
                "Suhu Maximum (°C)": annual_max.values
            })

            st.dataframe(
                annual_max_table,
                use_container_width=True,
                hide_index=True
            )

    # ========================================================
    # TAB 5 — TREND SUHU MAXIMUM
    # ========================================================

    with extreme_tabs[4]:

        st.subheader(
            f"📈 Trend Suhu Maximum Tahunan "
            f"({START_YEAR}–{END_YEAR})"
        )

        annual_max = (
            extreme_long
            .groupby("Year")["Temperature"]
            .max()
            .sort_index()
        )

        if annual_max.empty:

            st.warning(
                "Tiada data maximum tahunan "
                "untuk menghasilkan trend."
            )

        else:

            # ------------------------------------------------
            # GRAPH
            # ------------------------------------------------

            fig, ax = plt.subplots(
                figsize=(FIG_WIDTH, FIG_HEIGHT)
            )

            ax.plot(
                annual_max.index,
                annual_max.values,
                marker="o",
                linewidth=2,
                label="Suhu Maximum"
            )

            # =================================================
            # TREND LINE
            # =================================================

            valid = annual_max.dropna()

            if len(valid) >= 2:

                x = valid.index.astype(float).values
                y = valid.values.astype(float)

                coefficients = np.polyfit(
                    x,
                    y,
                    1
                )

                trend = np.poly1d(
                    coefficients
                )

                ax.plot(
                    x,
                    trend(x),
                    linestyle="--",
                    linewidth=2,
                    label="Trend Linear"
                )

            ax.set_title(
                "Trend Suhu Maximum Tahunan",
                fontsize=16,
                fontweight="bold"
            )

            ax.set_xlabel("Tahun")
            ax.set_ylabel(
                "Suhu Maximum (°C)"
            )

            ax.legend()

            ax.grid(
                linestyle="--",
                alpha=0.3
            )

            plt.tight_layout()

            st.pyplot(fig)

            plt.close(fig)

            # =================================================
            # TAHUN MAXIMUM TERTINGGI / TERENDAH
            # =================================================

            max_year = annual_max.idxmax()
            max_year_value = annual_max.max()

            min_year = annual_max.idxmin()
            min_year_value = annual_max.min()

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Tahun Suhu Maximum Tertinggi",
                    str(int(max_year)),
                    f"{max_year_value:.2f} °C"
                )

            with col2:

                st.metric(
                    "Tahun Suhu Maximum Terendah",
                    str(int(min_year)),
                    f"{min_year_value:.2f} °C"
                )
