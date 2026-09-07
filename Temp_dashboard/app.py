import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import calendar
import io
import streamlit as st
import xlrd
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
if selected_chart == "Monthly Temperature":

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


    for i, uploaded_file in enumerate(
        uploaded_files
    ):

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
                )
                * 100
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


if not successful_results:

    st.stop()


# ============================================================
# AVAILABLE YEARS
# ============================================================
available_years = sorted(

    set(

        year

        for result in successful_results

        for year
        in result["all_daily"]["Year"]
        .dropna()
        .unique()

    )

)


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
station_options = [

    result["file_name"]

    for result
    in successful_results

]


selected_station = st.sidebar.selectbox(

    "📍 Select Station",

    station_options,

    key="main_station"

)


# ============================================================
# FILTER DISPLAY RESULT
# ============================================================
display_results = [

    result

    for result
    in successful_results

    if result["file_name"]
    == selected_station

]


if not selected_station:

    st.warning(
        "Sila pilih sekurang-kurangnya satu stesen."
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
    # DISPLAY EACH FILE
    # ========================================================
    for result in display_results:

        file_name = result["file_name"]
        original_file_name = result["original_file_name"]
        all_daily = result["all_daily"]

        target_data = all_daily[
            all_daily["Year"] == target_year
        ].copy()

        read_errors = result["read_errors"]

        # ====================================================
        # CONVERT TARGET YEAR TO LONG FORMAT
        # ====================================================
        target_long = target_data.melt(
            id_vars=["Year", "hari"],
            value_vars=months,
            var_name="Month",
            value_name="Temperature"
        )

        month_number = {
            month: i + 1
            for i, month in enumerate(months)
        }

        target_long["Month_Number"] = (
            target_long["Month"]
            .map(month_number)
        )

        # ----------------------------------------------------
        # REMOVE INVALID DAYS
        # ----------------------------------------------------
        target_long["Days_In_Month"] = target_long.apply(
            lambda row: calendar.monthrange(
                int(row["Year"]),
                int(row["Month_Number"])
            )[1],
            axis=1
        )

        target_long = target_long[
            target_long["hari"]
            <= target_long["Days_In_Month"]
        ].copy()

        target_long = target_long.dropna(
            subset=["Temperature"]
        )

        # ====================================================
        # MONTHLY STATISTICS
        # ====================================================
        target_monthly_mean = (
            target_data[months]
            .mean()
        )

        target_monthly_max = (
            target_data[months]
            .max()
        )

        target_monthly_min = (
            target_data[months]
            .min()
        )

        # ====================================================
        # BASIC TARGET YEAR STATISTICS
        # ====================================================
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

        # ====================================================
        # FILE HEADER
        # ====================================================
        st.divider()

        st.header(
            f"📁 {original_file_name}"
        )

        # ====================================================
        # READ ERROR
        # ====================================================
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

        # ====================================================
        # BASIC METRICS
        # ====================================================
        col1, col2, col3, col4 = st.columns(4)

        with col1:

            if pd.notna(target_mean):

                st.metric(
                    f"Mean {target_year}",
                    f"{target_mean:.2f} °C"
                )

            else:

                st.metric(
                    f"Mean {target_year}",
                    "N.A."
                )

        with col2:

            if pd.notna(target_min):

                st.metric(
                    f"Minimum {target_year}",
                    f"{target_min:.2f} °C"
                )

            else:

                st.metric(
                    f"Minimum {target_year}",
                    "N.A."
                )

        with col3:

            if pd.notna(target_max):

                st.metric(
                    f"Maximum {target_year}",
                    f"{target_max:.2f} °C"
                )

            else:

                st.metric(
                    f"Maximum {target_year}",
                    "N.A."
                )

        with col4:

            if pd.notna(target_std):

                st.metric(
                    "Standard Deviation",
                    f"{target_std:.2f} °C"
                )

            else:

                st.metric(
                    "Standard Deviation",
                    "N.A."
                )

        # ====================================================
        # VALID DAILY RECORDS
        # ====================================================
        st.caption(
            f"Valid Daily Temperature Records: "
            f"{len(target_long):,}"
        )


        # ====================================================
        # TAB 1 — MONTHLY TEMPERATURE
        # ====================================================
        with tabs[0]:

            st.subheader(
                f"Monthly Temperature "
                f"{target_year}"
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
            # MEAN
            # ------------------------------------------------
            ax.plot(
                x,
                target_monthly_mean.values,
                marker="o",
                linewidth=2.5,
                markersize=7,
                label="Mean Temperature"
            )

            # ------------------------------------------------
            # MAX
            # ------------------------------------------------
            ax.plot(
                x,
                target_monthly_max.values,
                marker="^",
                linewidth=2,
                markersize=6,
                label="Maximum Temperature"
            )

            # ------------------------------------------------
            # MIN
            # ------------------------------------------------
            ax.plot(
                x,
                target_monthly_min.values,
                marker="v",
                linewidth=2,
                markersize=6,
                label="Minimum Temperature"
            )

            # ------------------------------------------------
            # MEAN LABELS
            # ------------------------------------------------
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
                f"Monthly Mean, Maximum and "
                f"Minimum Temperature {target_year}",
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

            # ------------------------------------------------
            # TABLE
            # ------------------------------------------------
            plot_table = pd.DataFrame({

                "Month":
                    months,

                f"Mean Temperature {target_year} (°C)":
                    target_monthly_mean.values,

                f"Maximum Temperature {target_year} (°C)":
                    target_monthly_max.values,

                f"Minimum Temperature {target_year} (°C)":
                    target_monthly_min.values

            })

            plot_table = plot_table.round(2)

            st.dataframe(
                plot_table,
                use_container_width=True,
                hide_index=True
            )

            # ------------------------------------------------
            # DOWNLOAD CSV
            # ------------------------------------------------
            csv = (
                plot_table
                .to_csv(index=False)
                .encode("utf-8")
            )

            st.download_button(
                "📥 Download Table CSV",
                data=csv,
                file_name=(
                    f"{selected_station}_"
                    f"monthly_temperature_"
                    f"{target_year}.csv"
                ),
                mime="text/csv",
                key=(
                    f"download_temperature_table_"
                    f"{selected_station}_{target_year}"
                )
            )

            plt.close(fig)


        # ====================================================
        # TAB 2 — HEATMAP
        # ====================================================
        with tabs[1]:

            st.subheader(
                f"Daily Temperature Heatmap "
                f"{target_year}"
            )

            heatmap_data = (
                target_data
                .set_index("hari")[months]
            )

            fig, ax = plt.subplots(
                figsize=(14, 8)
            )

            fig.patch.set_facecolor(
                BG_COLOR
            )

            ax.set_facecolor(
                BG_COLOR
            )

            plot_data = heatmap_data.copy()

            valid_values = plot_data.values[
                ~pd.isna(
                    plot_data.values
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
                plot_data.values,
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
                range(len(plot_data.index))
            )

            ax.set_yticklabels(
                plot_data.index.astype(str)
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
                f"Daily Temperature Heatmap "
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


        # ====================================================
        # TAB 3 — ANOMALY
        # ====================================================
        with tabs[2]:

            st.subheader(
                f"Monthly Temperature Anomaly "
                f"{target_year}"
            )

            # ------------------------------------------------
            # CLIMATOLOGICAL MEAN
            # ------------------------------------------------
            monthly_mean_all = (
                all_daily[months]
                .mean()
            )

            anomaly = (
                target_monthly_mean
                - monthly_mean_all
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

            bar_colors = [
                "red" if value > 0
                else "blue" if value < 0
                else "gray"
                for value in anomaly.values
            ]

            ax.bar(
                x,
                anomaly.values,
                edgecolor="black",
                linewidth=0.8
            )

            ax.axhline(
                0,
                linewidth=1.2
            )

            ax.set_title(
                f"{file_name}\n"
                f"Temperature Anomaly "
                f"{target_year}",
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

            # ------------------------------------------------
            # ANOMALY TABLE
            # ------------------------------------------------
            anomaly_table = pd.DataFrame({

                "Month":
                    months,

                f"Temperature {target_year} (°C)":
                    target_monthly_mean.values,

                "Climatological Mean (°C)":
                    monthly_mean_all.values,

                "Anomaly (°C)":
                    anomaly.values

            }).round(2)

            st.dataframe(
                anomaly_table,
                use_container_width=True,
                hide_index=True
            )

            plt.close(fig)


        # ====================================================
        # TAB 4 — STATISTICS
        # ====================================================
        with tabs[3]:

            st.subheader(
                f"Temperature Statistics "
                f"{target_year}"
            )

            stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = (
                st.columns(5)
            )

            with stat_col1:
                st.metric(
                    "Mean",
                    f"{target_mean:.2f} °C"
                    if pd.notna(target_mean)
                    else "N.A."
                )

            with stat_col2:
                st.metric(
                    "Median",
                    f"{target_median:.2f} °C"
                    if pd.notna(target_median)
                    else "N.A."
                )

            with stat_col3:
                st.metric(
                    "Maximum",
                    f"{target_max:.2f} °C"
                    if pd.notna(target_max)
                    else "N.A."
                )

            with stat_col4:
                st.metric(
                    "Minimum",
                    f"{target_min:.2f} °C"
                    if pd.notna(target_min)
                    else "N.A."
                )

            with stat_col5:
                st.metric(
                    "Std. Deviation",
                    f"{target_std:.2f} °C"
                    if pd.notna(target_std)
                    else "N.A."
                )

            statistics_table = pd.DataFrame({

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
                statistics_table,
                use_container_width=True,
                hide_index=True
            )


        # ====================================================
        # TAB 5 — DAILY TEMPERATURE
        # ====================================================
        with tabs[4]:

            st.subheader(
                f"Daily Temperature "
                f"{target_year}"
            )

            daily_plot = (
                target_long
                .sort_values(
                    ["Month_Number", "hari"]
                )
                .reset_index(drop=True)
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
                range(len(daily_plot)),
                daily_plot["Temperature"],
                linewidth=1.2
            )

            ax.set_title(
                f"{file_name}\n"
                f"Daily Temperature "
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

            plt.close(fig)
