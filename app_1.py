
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath


st.set_page_config(page_title="Riyadh Medical Cluster Dashboard")

# --- CSS Styling ---
def local_css(css_code):
    st.markdown(f"<style>{css_code}</style>", unsafe_allow_html=True)

css = """
/* الخلفية العامة */
body {
    background-color: #070F2B;
    color: #FFFADC;
}

/* الشريط الجانبي */
section[data-testid="stSidebar"] {
    background-color: #1B1A55;
    color: #FFFADC;
}

/* العناوين والنصوص */
h1, h2, h3, h4, h5, h6, p, div, span {
    color: #FFFADC !important;
    font-family: 'Arial', sans-serif !important;
}

/* القوائم المنسدلة */
.css-1v0mbdj, .css-10trblm, .stSelectbox div {
    color: #FFFADC !important;
}

/* الأزرار */
.stButton > button {
    background-color: #1B1A55;
    color: #FFFADC;
}

/* تحسين العرض على الموبايل */
@media only screen and (max-width: 768px) {
    h1 {
        font-size: 1.5rem;
    }
    .stApp {
        padding: 1rem;
    }
    section[data-testid="stSidebar"] {
        padding: 1rem;
    }
}
"""

local_css(css)


df = pd.read_csv("sample_delivery_data.csv")
drivers = pd.read_csv("drivers_info.csv")

tab1, tab2 = st.tabs(["📊 Overview", "🚗 Driver Performance"])

with tab1:
    st.markdown("<h1 style='text-align: center; color:#FFFADC;'>Riyadh Medical Cluster II</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color:#FFFADC;'>Reporting : ✌️ Mohamed Abdulmuniem ✌️</h3>", unsafe_allow_html=True)
    st.divider()

    total_samples = df["عدد العينات"].sum()
    avg_delivery_time = df["زمن التوصيل (دقائق)"].mean()
    num_centers = df["المركز الصحي"].nunique()
    num_labs = df["المختبر"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Samples", int(total_samples))
    col2.metric("Avg Delivery Time (min)", f"{avg_delivery_time:.1f}")
    col3.metric("Total Centers", num_centers)
    col4.metric("Total Labs", num_labs)

    st.subheader("Top 5 Centers by Samples")
    top_centers = df.groupby("المركز الصحي")["عدد العينات"].sum().sort_values(ascending=False).head(5)
    fig1 = px.bar(top_centers, x=top_centers.index, y=top_centers.values, title="Top Centers", color_discrete_sequence=["#FFFADC"])
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Sample Distribution by Lab")
    lab_dist = df.groupby("المختبر")["عدد العينات"].sum()
    fig2 = px.pie(values=lab_dist.values, names=lab_dist.index, title="Sample Distribution by Lab", color_discrete_sequence=px.colors.sequential.Pinkyl)
    st.plotly_chart(fig2, use_container_width=True)

    #st.subheader("Samples Over Time (by Date)")
    #df["date"] = pd.to_datetime(df["وقت الاستلام"])
    #daily = df.groupby("date")["عدد العينات"].sum()
    #fig3 = px.line(daily, x=daily.index, y=daily.values, title="Samples Over Time", color_discrete_sequence=["#535C91"])
    #st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Total Delivery Time Over Time")

    df["date"] = pd.to_datetime(df["تاريخ الاستلام"], errors="coerce")
    df_clean = df.dropna(subset=["date", "زمن التوصيل (دقائق)"])
    daily = df_clean.groupby("date", as_index=False)["زمن التوصيل (دقائق)"].sum()

    fig = px.line(
    daily,
    x="date",
    y="زمن التوصيل (دقائق)",
    title="Total Delivery Time Over Time",
    markers=True,
    color_discrete_sequence=["#FFFADC"])
    st.plotly_chart(fig, use_container_width=True)



    st.subheader("Total Delivery Time Over Time Heatmap")
    df["تاريخ الاستلام"] = pd.to_datetime(df["تاريخ الاستلام"], errors="coerce")
    df["اليوم"] = df["تاريخ الاستلام"].dt.strftime('%A')  # مثال: Saturday
    df["الشهر"] = df["تاريخ الاستلام"].dt.strftime('%B')  # مثال: June
    # اختيار مستوى التجميع (مثلاً: حسب اليوم)
    pivot = df.pivot_table(
    index="اليوم",               # أو "الشهر"
    columns="المندوب",
    values="زمن التوصيل (دقائق)",
    aggfunc="sum"
    ).fillna(0)

    z = pivot.values
    x = list(pivot.columns)
    y = list(pivot.index)

    colorscale = [
    [0.0, "#FCFFC1"],
    [0.5, "#FCC737"],
    [1.0, "#F26B0F"]
]


    fig = ff.create_annotated_heatmap(
    z,
    x=x,
    y=y,
    colorscale=colorscale,
    showscale=True,
    annotation_text=[[f"{val:.0f}" for val in row] for row in z],
    font_colors=["Black"]
    
)
    st.plotly_chart(fig, use_container_width=True)



    st.subheader("Centers & Labs Map")
    df["خط العرض"] = pd.to_numeric(df["خط العرض"], errors="coerce")
    df["خط الطول"] = pd.to_numeric(df["خط الطول"], errors="coerce")
    df["خط العرض_lab"] = pd.to_numeric(df["خط العرض_lab"], errors="coerce")
    df["خط الطول_lab"] = pd.to_numeric(df["خط الطول_lab"], errors="coerce")

    m = folium.Map(location=[24.75, 46.75], zoom_start=11)
    
    centers_summary = df.groupby(["المركز الصحي", "خط العرض", "خط الطول"])["عدد العينات"].sum().reset_index()
    for _, row in centers_summary.iterrows():
        folium.CircleMarker(
            location=[row["خط العرض"], row["خط الطول"]],
            radius=6,
            color="blue",
            fill=True,
            fill_color="blue",
            tooltip=f"Center: {row['المركز الصحي']}\nSamples: {int(row['عدد العينات'])}"
        ).add_to(m)

    labs_summary = df.groupby(["المختبر", "خط العرض_lab", "خط الطول_lab"])["عدد العينات"].sum().reset_index()
    for _, row in labs_summary.iterrows():
        folium.CircleMarker(
            location=[row["خط العرض_lab"], row["خط الطول_lab"]],
            radius=7,
            color="green",
            fill=True,
            fill_color="green",
            tooltip=f"Lab: {row['المختبر']}\nReceived: {int(row['عدد العينات'])}"
        ).add_to(m)

    st_folium(m, width=700, height=500 , key="overview_map")

    

with tab2:
    st.sidebar.title("Driver Filter")
    all_drivers = ["All"] + sorted(drivers["الاسم"].unique())
    selected_driver = st.sidebar.selectbox("Select Driver", all_drivers)

    if selected_driver == "All":
        driver_filtered_df = df.copy()
    else:
        driver_filtered_df = df[df["المندوب"] == selected_driver]

    selected_month = st.sidebar.selectbox("Select Month", ["All"] + sorted(driver_filtered_df["شهر الاستلام"].unique()))
    if selected_month != "All":
        month_filtered_df = driver_filtered_df[driver_filtered_df["شهر الاستلام"] == selected_month]
        selected_day = st.sidebar.selectbox("Select Day", ["All"] + sorted(month_filtered_df["يوم الاستلام"].unique()))
    else:
        month_filtered_df = driver_filtered_df.copy()
        selected_day = st.sidebar.selectbox("Select Day", ["All"] + sorted(driver_filtered_df["يوم الاستلام"].unique()))

    if selected_day != "All":
        filtered_df = month_filtered_df[month_filtered_df["يوم الاستلام"] == selected_day]
    else:
        filtered_df = month_filtered_df.copy()

    if selected_driver != "All" and selected_driver in drivers["الاسم"].values:
        driver_data = drivers[drivers["الاسم"] == selected_driver].iloc[0]
        col1, col2, = st.columns([1, 2])
        with col1:
            st.image(driver_data["صورة"], width=200)
        with col2:
            st.write("### Driver Info")
            st.write(f"**Name:** {driver_data['الاسم']}")
            st.write(f"**Phone:** {driver_data['الجوال']}")
            st.write(f"**ID:** {driver_data['ID']}")
            st.write(f"**Plate:** {driver_data['لوحة السيارة']}")
            st.write(f"**Centers:** {driver_data['المراكز']}")
            st.write(f"**Lab:** {driver_data['المختبر']}")
            st.write(f"**Company:** {driver_data['الشركة المشغلة']}")

    #st.sidebar.markdown("Made by Mohamed Abdulonem")  
    st.sidebar.markdown("""
    <style>
        .sidebar-footer {
            
            bottom: 20px;
            left: 0;
            width: 100%;
            text-align: center;
            font-size: 14px;
            color: #FFFADC;
        }
    
    </style>
    <hr style='margin-top: 50px; margin-bottom: 10px;'>
    <div class="sidebar-footer">
        Made with by✌️ <strong>Mohamed Abdulmonem</strong>
    </div>
""", unsafe_allow_html=True)

      
    st.subheader("Driver KPIs")
    st.write(f"Total Samples: {filtered_df['عدد العينات'].sum()}")
    st.write(f"Avg Delivery Time: {filtered_df['زمن التوصيل (دقائق)'].mean():.2f} min")

    fig4 = px.bar(filtered_df, x="المركز الصحي", y="عدد العينات", color="المختبر", title="Samples by Center", color_discrete_sequence=["#FFFADC"])
    st.plotly_chart(fig4, use_container_width=True)

    fig5 = px.line(filtered_df, x="وقت الاستلام", y="زمن التوصيل (دقائق)", markers=True, title="Delivery Time Over Day", color_discrete_sequence=["#FFFADC"])
    st.plotly_chart(fig5, use_container_width=True)

    m2 = folium.Map(location=[24.75, 46.75], zoom_start=11)
    centers_summary = filtered_df.groupby(["المركز الصحي", "خط العرض", "خط الطول"])["عدد العينات"].sum().reset_index()
    for _, row in centers_summary.iterrows():
        folium.CircleMarker(
            location=[row["خط العرض"], row["خط الطول"]],
            radius=6,
            color="blue",
            fill=True,
            fill_color="blue",
            tooltip=f"Center: {row['المركز الصحي']}\nSamples: {int(row['عدد العينات'])}"
        ).add_to(m2)

    
    

    st.subheader("Connection Map (Centers → Labs) For Selected Drivers")

    m_driver = folium.Map(location=[24.75, 46.75], zoom_start=11)

    # استخدام البيانات بحسب الفلاتر: filtered_df عند اختيار مندوب أو df بالكامل عند All
    map_data = filtered_df if selected_driver != "All" else df.copy()

    # جمع بيانات المراكز
    centers_summary = map_data.groupby(["المركز الصحي", "خط العرض", "خط الطول"])["عدد العينات"].sum().reset_index()
    for _, row in centers_summary.iterrows():
        folium.CircleMarker(
        location=[row["خط العرض"], row["خط الطول"]],
        radius=6,
        color="green",
        fill=True,
        fill_color="green",
        tooltip=f"Center: {row['المركز الصحي']}\nSamples: {int(row['عدد العينات'])}"
    ).add_to(m_driver)

    # جمع بيانات المختبرات
    labs_summary = map_data.groupby(["المختبر", "خط العرض_lab", "خط الطول_lab"])["عدد العينات"].sum().reset_index()
    for _, row in labs_summary.iterrows():
        folium.CircleMarker(
        location=[row["خط العرض_lab"], row["خط الطول_lab"]],
        radius=7,
        color="red",
        fill=True,
        fill_color="red",
        tooltip=f"Lab: {row['المختبر']}\nReceived: {int(row['عدد العينات'])}"
    ).add_to(m_driver)

    # رسم الخطوط باستخدام AntPath (خط متحرك مقوس)

    for _, row in map_data.iterrows():
        try:
            lat1, lon1 = float(row["خط العرض"]), float(row["خط الطول"])
            lat2, lon2 = float(row["خط العرض_lab"]), float(row["خط الطول_lab"])

            AntPath(
             locations=[(lat1, lon1), (lat2, lon2)],
                color="blue",
                weight=2,
                delay=1000
            ).add_to(m_driver)

        except:
            continue

    st_folium(m_driver,width= 800, height=500, key="driver_connection_map")



