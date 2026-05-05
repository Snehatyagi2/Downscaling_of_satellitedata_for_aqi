import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from src.predict import generate_report, satellite_downscaling
from src.api_weather import get_weather

import folium
from streamlit_folium import st_folium

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AQI Intelligence System",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_report(city):
    return generate_report(city)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_satellite_weather(city):
    return get_weather(city)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_satellite_grid(city):
    weather = cached_satellite_weather(city)
    if weather is None:
        return None
    temp, humidity, lat, lon = weather
    return satellite_downscaling(temp, humidity, lat, lon, city=city)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Import Google Font ─── */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ─── */
    html, body, .stApp {
        font-family: 'Outfit', sans-serif;
        background: #050505;
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(20, 15, 40, 0.6), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(10, 25, 40, 0.6), transparent 25%);
        color: #E2E8F0;
    }
    .stApp > header { background: transparent !important; }

    /* ── Sidebar ─── */
    section[data-testid="stSidebar"] {
        background: rgba(10, 10, 12, 0.7) !important;
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        border-right: 1px solid rgba(255,255,255,0.04) !important;
    }
    section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar { display: none !important; }
    section[data-testid="stSidebar"] > div:first-child { scrollbar-width: none !important; }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] label {
        color: #A1A1AA !important;
    }
    
    /* ── Glass Card (Premium SaaS) ─── */
    .glass-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4);
        border-color: rgba(255, 255, 255, 0.1);
    }

    /* ── Typography & Headers ─── */
    h1, h2, h3, h4, h5, h6 { font-family: 'Outfit', sans-serif !important; }

    /* ── Metrics ─── */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    [data-testid="stMetricLabel"] { color: #A1A1AA !important; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; font-size: 0.8rem; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 700; font-family: 'Outfit'; }

    /* ── Buttons ─── */
    .stButton > button {
        background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 100%) !important;
        color: #0f172a !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(255, 255, 255, 0.2) !important;
        background: #ffffff !important;
    }

    /* ── Input & Selectbox ─── */
    .stTextInput > div > div > input, div[data-baseweb="select"] > div {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-family: 'Outfit' !important;
        transition: border 0.3s ease !important;
    }
    div[data-baseweb="select"] > div:hover {
        border: 1px solid rgba(255,255,255,0.2) !important;
    }
    .stTextInput label, .stSelectbox label { color: #A1A1AA !important; font-weight: 500 !important; }
    ul[data-baseweb="menu"] {
        background-color: #0a0a0c !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    li[role="option"] {
        color: #e8edf2 !important;
        background-color: transparent !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* ── Tabs ─── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,0.02);
        border-radius: 14px;
        padding: 6px;
        border: 1px solid rgba(255,255,255,0.04);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
        color: #A1A1AA;
        transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.1) !important;
        color: #ffffff !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }

    /* ── Dividers ─── */
    .custom-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
        margin: 30px 0;
    }

    /* ── Info Box ─── */
    .info-box {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 20px;
        color: #A1A1AA;
        font-size: 0.9rem;
        line-height: 1.6;
    }

    /* ── Expander ─── */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.03) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-family: 'Outfit' !important;
    }

    /* Hide Defaults */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #050505; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
</style>
""", unsafe_allow_html=True)

# ─── Helper Functions ────────────────────────────────────────────────────────

def get_aqi_level(aqi):
    """Return (label, css_class, color_hex) based on AQI value."""
    if aqi <= 50:
        return "Good", "aqi-good", "#00e676"
    elif aqi <= 100:
        return "Moderate", "aqi-moderate", "#ffeb3b"
    elif aqi <= 150:
        return "Unhealthy (SG)", "aqi-unhealthy-sg", "#ff9800"
    elif aqi <= 200:
        return "Unhealthy", "aqi-unhealthy", "#ff5252"
    elif aqi <= 300:
        return "Very Unhealthy", "aqi-very-unhealthy", "#e040fb"
    else:
        return "Hazardous", "aqi-hazardous", "#d50000"


def get_area_badge(area):
    """Return the badge HTML for an area type."""
    css = f"badge-{area.lower()}"
    return f'<span class="badge {css}">{area}</span>'


def create_aqi_gauge(aqi_value, title="AQI"):
    """Create a circular gauge chart for AQI."""
    _, _, color = get_aqi_level(aqi_value)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=aqi_value,
        title={"text": title, "font": {"size": 14, "color": "#7a8ba3"}},
        number={"font": {"size": 42, "color": color, "family": "Outfit"}, "suffix": ""},
        gauge={
            "axis": {"range": [0, 500], "tickwidth": 1, "tickcolor": "rgba(255,255,255,0.1)",
                     "tickfont": {"color": "#5a6a7a", "size": 10}},
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": "rgba(255,255,255,0.02)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50], "color": "rgba(0,230,118,0.08)"},
                {"range": [50, 100], "color": "rgba(255,235,59,0.08)"},
                {"range": [100, 150], "color": "rgba(255,152,0,0.08)"},
                {"range": [150, 200], "color": "rgba(255,82,82,0.08)"},
                {"range": [200, 300], "color": "rgba(224,64,251,0.08)"},
                {"range": [300, 500], "color": "rgba(213,0,0,0.08)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.8,
                "value": aqi_value
            }
        }
    ))

    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Outfit"}
    )

    return fig


def create_forecast_chart(forecast_values):
    """Create a 7-day forecast line chart."""
    import datetime
    today = datetime.datetime.now()
    # Create actual dates for the next 7 days
    days = [(today + datetime.timedelta(days=i+1)).strftime("%a, %b %d") for i in range(len(forecast_values))]
    
    colors = [get_aqi_level(v)[2] for v in forecast_values]

    fig = go.Figure()

    # Glowing shadow for the line
    fig.add_trace(go.Scatter(
        x=days, y=forecast_values,
        mode='lines',
        line=dict(color='rgba(0, 210, 255, 0.3)', width=8, shape='spline'),
        hoverinfo='skip',
        showlegend=False
    ))

    # Main Area fill
    fig.add_trace(go.Scatter(
        x=days, y=forecast_values,
        fill='tozeroy',
        fillcolor='rgba(0, 210, 255, 0.15)',
        line=dict(color='#00d2ff', width=3, shape='spline'),
        mode='lines+markers',
        marker=dict(size=12, color=colors, line=dict(width=3, color='#1a1a2e')),
        hovertemplate="<b>%{x}</b><br>Predicted AQI: %{y}<extra></extra>",
        showlegend=False
    ))

    # Color threshold bands
    # Color threshold bands with slightly higher opacity
    fig.add_hrect(y0=0, y1=50, fillcolor="rgba(0,230,118,0.06)", line_width=0)
    fig.add_hrect(y0=50, y1=100, fillcolor="rgba(255,235,59,0.06)", line_width=0)
    fig.add_hrect(y0=100, y1=150, fillcolor="rgba(255,152,0,0.06)", line_width=0)
    fig.add_hrect(y0=150, y1=200, fillcolor="rgba(255,82,82,0.06)", line_width=0)
    fig.add_hrect(y0=200, y1=300, fillcolor="rgba(224,64,251,0.06)", line_width=0)
    fig.add_hrect(y0=300, y1=500, fillcolor="rgba(213,0,0,0.06)", line_width=0)

    fig.update_layout(
        height=260,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            color="#5a6a7a",
            tickfont=dict(family="Outfit", size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            color="#5a6a7a",
            tickfont=dict(family="Outfit", size=11),
            title=dict(text="AQI", font=dict(size=12, color="#5a6a7a"))
        ),
        showlegend=False,
        font=dict(family="Outfit"),
        hoverlabel=dict(
            bgcolor="#1a1a2e",
            bordercolor="rgba(0,210,255,0.3)",
            font=dict(color="#e8edf2", family="Outfit")
        )
    )

    return fig


def create_folium_map(df, center_lat, center_lon):
    """Create a Folium map for satellite AQI grid."""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="CartoDB dark_matter")

    for idx, row in df.iterrows():
        lat = row["lat"]
        lon = row["lon"]
        aqi = row["aqi"]
        
        _, _, color = get_aqi_level(aqi)

        popup_html = f"""
        <div style="font-family: 'Outfit', sans-serif; min-width: 150px; padding: 5px;">
            <h4 style="margin: 0 0 10px 0; color: #333;">Air Quality Point</h4>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <b>AQI:</b> <span style="color: {color}; font-weight: bold; font-size: 16px;">{aqi:.0f}</span>
            </div>
            <div style="font-size: 12px; color: #666; margin-top: 8px;">
                Lat: {lat:.3f}<br>Lon: {lon:.3f}
            </div>
        </div>
        """
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"AQI: {aqi:.0f}",
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2
        ).add_to(m)

    return m


def create_pollutant_bar(pm25, pm10, no2):
    """Create a horizontal bar chart for pollutant breakdown."""
    pollutants = ["PM2.5", "PM10", "NO₂"]
    values = [pm25, pm10, no2]
    colors = ["#ff6b6b", "#ffa726", "#7c4dff"]

    fig = go.Figure()

    for i, (p, v, c) in enumerate(zip(pollutants, values, colors)):
        fig.add_trace(go.Bar(
            y=[p], x=[v],
            orientation='h',
            name=p,
            marker=dict(color=c, cornerradius=6),
            text=[f"{v:.1f}"],
            textposition="outside",
            textfont=dict(color=c, size=12, family="Outfit"),
            hovertemplate=f"<b>{p}</b>: {v:.1f} µg/m³<extra></extra>"
        ))

    fig.update_layout(
        height=140,
        margin=dict(l=0, r=40, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, showticklabels=False, range=[0, max(values) * 1.4]),
        yaxis=dict(
            showgrid=False,
            color="#7a8ba3",
            tickfont=dict(family="Outfit", size=12, color="#9ab0c4")
        ),
        showlegend=False,
        barmode="group",
        bargap=0.35,
        font=dict(family="Outfit"),
        hoverlabel=dict(
            bgcolor="#1a1a2e",
            bordercolor="rgba(0,210,255,0.3)",
            font=dict(color="#e8edf2", family="Outfit")
        )
    )

    return fig


# ─── Navbar & Controls ───────────────────────────────────────────────────────

nav_left, nav_right = st.columns([1.2, 2.5], gap="large")

with nav_left:
    st.markdown('''
    <div style="display: flex; align-items: center; gap: 12px; height: 100%; padding-top: 12px;">
        <div style="font-size: 2.5rem; filter: drop-shadow(0 0 15px rgba(255, 255, 255, 0.4));">🌍</div>
        <div>
            <h1 style="font-family: 'Outfit', sans-serif; font-size: 1.6rem; font-weight: 800; margin: 0; padding: 0; color: #FFFFFF; letter-spacing: -0.5px; line-height: 1.2;">
                AQI <span style="color: #A1A1AA;">Intelligence</span>
            </h1>
            <p style="margin: 0; font-size: 0.75rem; color: #71717A; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;">Live Dashboard</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)

AVAILABLE_CITIES = sorted([
    "Agra", "Ahmedabad", "Ajmer", "Akola", "Aligarh", "Allahabad", "Amravati", "Amritsar", "Asansol", "Aurangabad",
    "Bareilly", "Belgaum", "Bengaluru", "Bhavnagar", "Bhilai", "Bhiwandi", "Bhopal", "Bhubaneswar", "Bikaner", "Chandigarh",
    "Chennai", "Coimbatore", "Cuttack", "Dehradun", "Delhi", "Dhanbad", "Dubai", "Durgapur", "Erode", "Faridabad", 
    "Firozabad", "Gaya", "Ghaziabad", "Gorakhpur", "Gulbarga", "Guntur", "Gurgaon", "Guwahati", "Gwalior", "Hong Kong",
    "Howrah", "Hubli-Dharwad", "Hyderabad", "Indore", "Jabalpur", "Jaipur", "Jakarta", "Jalandhar", "Jalgaon", "Jammu", 
    "Jamnagar", "Jamshedpur", "Jhansi", "Jodhpur", "Kalyan-Dombivli", "Kanpur", "Karachi", "Kochi", "Kolhapur", "Kolkata", 
    "Kota", "Kuala Lumpur", "London", "Loni", "Los Angeles", "Lucknow", "Ludhiana", "Madurai", "Maheshtala", "Malegaon", 
    "Mangalore", "Meerut", "Mira-Bhayandar", "Moradabad", "Mumbai", "Mysore", "Nagpur", "Nanded", "Nashik", "Navi Mumbai", 
    "Nellore", "New Delhi", "New York", "Noida", "Paris", "Patna", "Pimpri-Chinchwad", "Pune", "Raipur", "Rajkot", 
    "Ranchi", "Rourkela", "Saharanpur", "Salem", "Sangli-Miraj & Kupwad", "Seoul", "Shanghai", "Siliguri", "Singapore", 
    "Solapur", "Srinagar", "Surat", "Sydney", "Thane", "Tiruchirappalli", "Tirunelveli", "Tokyo", "Udaipur", "Ujjain", 
    "Ulhasnagar", "Vadodara", "Varanasi", "Vasai-Virar", "Vijayawada", "Visakhapatnam", "Warangal"
])

with nav_right:
    ctrl1, ctrl2, ctrl3 = st.columns([1.5, 1.5, 1])
    
    with ctrl1:
        default_index = AVAILABLE_CITIES.index("Delhi") if "Delhi" in AVAILABLE_CITIES else 0
        city = st.selectbox("🏙️ City", AVAILABLE_CITIES, index=default_index, label_visibility="collapsed")
    
    with ctrl2:
        analysis_mode = st.radio(
            "Mode",
            ["Full AQI Report", "Satellite Downscaling"],
            horizontal=True,
            label_visibility="collapsed"
        )
    
    with ctrl3:
        run_analysis = st.button("Run", use_container_width=True)

with st.expander("ℹ️ System Information & AQI Legend"):
    ecol1, ecol2 = st.columns(2)
    with ecol1:
        st.markdown("""
        <div class="info-box" style="margin-bottom: 0;">
            <strong style="color: #00d2ff;">ℹ️ About</strong><br><br>
            This system uses <strong>Machine Learning</strong> and real-time data to predict and forecast Air Quality Index.
            <br><br>
            <strong>Data Sources:</strong>
            <ul style="margin: 6px 0 0 0; padding-left: 18px;">
                <li>OpenWeatherMap (Weather)</li>
                <li>OpenAQ (Pollution)</li>
                <li>Satellite Simulation</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with ecol2:
        st.markdown("""
        <div style="padding-left: 20px;">
            <p style="color: #5a6a7a; font-size: 0.75rem; text-transform: uppercase;
                      letter-spacing: 1.5px; font-weight: 600; margin-bottom: 10px;">
                AQI Scale
            </p>
            <div style="display: flex; flex-direction: column; gap: 5px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:12px;height:12px;border-radius:3px;background:#00e676;"></div>
                    <span style="color:#7a8ba3;font-size:0.78rem;">0–50 Good</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:12px;height:12px;border-radius:3px;background:#ffeb3b;"></div>
                    <span style="color:#7a8ba3;font-size:0.78rem;">51–100 Moderate</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:12px;height:12px;border-radius:3px;background:#ff9800;"></div>
                    <span style="color:#7a8ba3;font-size:0.78rem;">101–150 Unhealthy (SG)</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:12px;height:12px;border-radius:3px;background:#ff5252;"></div>
                    <span style="color:#7a8ba3;font-size:0.78rem;">151–200 Unhealthy</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:12px;height:12px;border-radius:3px;background:#e040fb;"></div>
                    <span style="color:#7a8ba3;font-size:0.78rem;">201–300 Very Unhealthy</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:12px;height:12px;border-radius:3px;background:#d50000;"></div>
                    <span style="color:#7a8ba3;font-size:0.78rem;">301+ Hazardous</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent); margin: 24px 0;">', unsafe_allow_html=True)


# ─── Analysis Execution ─────────────────────────────────────────────────────
if run_analysis:

    if analysis_mode == "Full AQI Report":
        with st.spinner("🔄 Fetching live data & generating predictions..."):
            data = cached_report(city)

        if data is None:
            st.markdown("""
            <div style="text-align: center; padding: 60px 20px;">
                <span style="font-size: 4rem;">😔</span>
                <h3 style="color: #e8edf2; margin-top: 16px;">Data Not Available</h3>
                <p style="color: #7a8ba3; max-width: 400px; margin: 10px auto;">
                    Could not retrieve data for <strong>{}</strong>.
                    Please check the city name or try again later.
                </p>
            </div>
            """.format(city), unsafe_allow_html=True)
        else:
            # ── Summary Metrics Row ──
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

            avg_aqi = sum(d["aqi"] for d in data) / len(data)
            max_aqi = max(d["aqi"] for d in data)
            min_aqi = min(d["aqi"] for d in data)
            avg_level, avg_class, avg_color = get_aqi_level(avg_aqi)

            def metric_card(title, value, icon, color="#00D4FF"):
                return f'''
                <div class="glass-card" style="padding: 16px; margin-bottom: 0; display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                        <span style="color: #94A3B8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{title}</span>
                        <span style="font-size: 1.2rem; filter: drop-shadow(0 0 8px {color});">{icon}</span>
                    </div>
                    <div style="display: flex; align-items: baseline; gap: 8px;">
                        <span style="color: #E2E8F0; font-size: 2rem; font-weight: 800; letter-spacing: -1px; line-height: 1;">{value}</span>
                    </div>
                </div>
                '''

            col1, col2, col3, col4 = st.columns(4)
            with col1: st.markdown(metric_card("Avg AQI", f"{avg_aqi:.0f}", "📊", avg_color), unsafe_allow_html=True)
            with col2: st.markdown(metric_card("Worst AQI", f"{max_aqi:.0f}", "📉", "#EF4444"), unsafe_allow_html=True)
            with col3: st.markdown(metric_card("Best AQI", f"{min_aqi:.0f}", "📈", "#22C55E"), unsafe_allow_html=True)
            with col4: st.markdown(metric_card("Stations", f"{len(data)}", "📍", "#7C5CFF"), unsafe_allow_html=True)

            st.markdown('<div class="custom-divider" style="margin-top: 24px;"></div>', unsafe_allow_html=True)

            # ── Dashboard Layout ──
            dash_left, dash_right = st.columns([7, 5], gap="large")

            with dash_left:
                st.markdown('<h3 style="color: #E2E8F0; font-size: 1.1rem; margin-bottom: 16px;">City 7-Day Forecast</h3>', unsafe_allow_html=True)
                # Use the forecast from the first station as the city representative forecast
                city_forecast = data[0]["forecast"]
                fig_forecast = create_forecast_chart(city_forecast)
                st.plotly_chart(fig_forecast, use_container_width=True, key="main_forecast")

            with dash_right:
                st.markdown('<h3 style="color: #E2E8F0; font-size: 1.1rem; margin-bottom: 16px;">Monitoring Stations</h3>', unsafe_allow_html=True)
                
                list_html = '<div class="glass-card" style="padding: 20px; display: flex; flex-direction: column; gap: 16px;">\n'
                
                for idx, d in enumerate(data):
                    level_label, _, level_color = get_aqi_level(d["aqi"])
                    list_html += f'''<div style="display:flex; justify-content:space-between; align-items:center; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05);">
<div style="display:flex; flex-direction:column; gap:4px;">
<span style="color: #E2E8F0; font-weight: 600; font-size: 0.95rem;">{d['location']}</span>
<span style="color: #94A3B8; font-size: 0.8rem;">{d['reason']}</span>
</div>
<div style="text-align:right;">
<span style="color: {level_color}; font-weight: 800; font-size: 1.2rem;">{d['aqi']:.0f}</span><br>
<span style="color: #94A3B8; font-size: 0.75rem; text-transform: uppercase;">{level_label}</span>
</div>
</div>\n'''
                list_html += '</div>'
                st.markdown(list_html, unsafe_allow_html=True)


    elif analysis_mode == "Satellite Downscaling":
        with st.spinner("🛰️ Generating satellite downscaling grid..."):
            weather = get_weather(city)

        if weather is None:
            st.markdown("""
            <div style="text-align: center; padding: 60px 20px;">
                <span style="font-size: 4rem;">🌧️</span>
                <h3 style="color: #e8edf2; margin-top: 16px;">Weather Data Unavailable</h3>
                <p style="color: #7a8ba3; max-width: 400px; margin: 10px auto;">
                    Could not fetch weather data. Please check your API key and city name.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.spinner("🔄 Running satellite downscaling model..."):
                sat_data = cached_satellite_grid(city)

            if sat_data is None:
                st.markdown("""
                <div style="text-align: center; padding: 60px 20px;">
                    <span style="font-size: 4rem;">🌧️</span>
                    <h3 style="color: #e8edf2; margin-top: 16px;">Weather Data Unavailable</h3>
                    <p style="color: #7a8ba3; max-width: 400px; margin: 10px auto;">
                        Could not fetch weather data. Please check your API key and city name.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                temp, humidity, lat, lon = cached_satellite_weather(city)

                df = pd.DataFrame(sat_data)

                st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

            # ── Weather + Summary Metrics ──
                avg_aqi = df["aqi"].mean()
                max_aqi = df["aqi"].max()
                min_aqi = df["aqi"].min()
                level_label, _, level_color = get_aqi_level(avg_aqi)

                def metric_card(title, value, icon, color="#00D4FF"):
                    return f'''
                    <div class="glass-card" style="padding: 16px; margin-bottom: 0; display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                            <span style="color: #94A3B8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{title}</span>
                            <span style="font-size: 1.2rem; filter: drop-shadow(0 0 8px {color});">{icon}</span>
                        </div>
                        <div style="display: flex; align-items: baseline; gap: 8px;">
                            <span style="color: #E2E8F0; font-size: 2rem; font-weight: 800; letter-spacing: -1px; line-height: 1;">{value}</span>
                        </div>
                    </div>
                    '''

                mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
                with mcol1: st.markdown(metric_card("Temperature", f"{temp}°C", "🌡️"), unsafe_allow_html=True)
                with mcol2: st.markdown(metric_card("Humidity", f"{humidity}%", "💧"), unsafe_allow_html=True)
                with mcol3: st.markdown(metric_card("Avg AQI", f"{avg_aqi:.0f}", "📊", level_color), unsafe_allow_html=True)
                with mcol4: st.markdown(metric_card("Max AQI", f"{max_aqi:.0f}", "📈", "#EF4444"), unsafe_allow_html=True)
                with mcol5: st.markdown(metric_card("Min AQI", f"{min_aqi:.0f}", "📉", "#22C55E"), unsafe_allow_html=True)

                st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

            # ── Dashboard Split View ──
                dash_left, dash_right = st.columns([7, 5], gap="large")
            
                with dash_left:
                    st.markdown('<h3 style="color: #E2E8F0; font-size: 1.1rem; margin-bottom: 16px;">Interactive Map</h3>', unsafe_allow_html=True)
                    m = create_folium_map(df, lat, lon)
                    st_folium(m, height=450, use_container_width=True, returned_objects=[])
                    
                    # Distribution Chart below map
                    st.markdown('<h3 style="color: #E2E8F0; font-size: 1.1rem; margin-top: 24px; margin-bottom: 8px;">Distribution</h3>', unsafe_allow_html=True)

                import numpy as np
                fig_hist = go.Figure()

                counts, bins = np.histogram(df["aqi"], bins=15)
                bin_centers = 0.5 * (bins[:-1] + bins[1:])

            # Smooth trendline overlay
            fig_hist.add_trace(go.Scatter(
                x=bin_centers,
                y=counts,
                mode='lines+markers',
                line=dict(color='rgba(255, 255, 255, 0.4)', width=2, shape='spline'),
                marker=dict(size=6, color='white', line=dict(color='#1a1a2e', width=1)),
                hoverinfo='skip',
                showlegend=False
            ))

            # Gradient Bars
            fig_hist.add_trace(go.Bar(
                x=bin_centers,
                y=counts,
                width=(bins[1]-bins[0]) * 0.85,
                marker=dict(
                    color=bin_centers,
                    colorscale=[
                        [0.0, "#00e676"],
                        [0.16, "#ffeb3b"],
                        [0.33, "#ff9800"],
                        [0.50, "#ff5252"],
                        [0.66, "#e040fb"],
                        [1.0, "#d50000"]
                    ],
                    cmin=0,
                    cmax=300,
                    line=dict(color="rgba(255,255,255,0.05)", width=1)
                ),
                opacity=0.9,
                hovertemplate="<b>AQI Range:</b> ~%{x:.1f}<br><b>Grid Points:</b> %{y}<extra></extra>",
                showlegend=False
            ))
            fig_hist.update_layout(
                height=280,
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    title=dict(text="AQI Value", font=dict(color="#5a6a7a", size=12)),
                    showgrid=False, color="#5a6a7a",
                    tickfont=dict(family="Outfit", size=11)
                ),
                yaxis=dict(
                    title=dict(text="Frequency", font=dict(color="#5a6a7a", size=12)),
                    showgrid=True, gridcolor="rgba(255,255,255,0.04)", color="#5a6a7a",
                    tickfont=dict(family="Outfit", size=11)
                ),
                font=dict(family="Outfit"),
                hoverlabel=dict(
                    bgcolor="#1a1a2e",
                    bordercolor="rgba(0,210,255,0.3)",
                    font=dict(color="#e8edf2", family="Outfit")
                )
            )
            st.plotly_chart(fig_hist, use_container_width=True, key="hist")

            with dash_right:
                st.markdown('<h3 style="color: #E2E8F0; font-size: 1.1rem; margin-bottom: 16px;">AI Insights & Analysis</h3>', unsafe_allow_html=True)
                
                # Compute insights
                sorted_df = df.sort_values(by="aqi", ascending=False)
                top_polluted = sorted_df.head(3)
                cleanest = sorted_df.tail(3)
                
                def get_advisory(label):
                    advisories = {
                        "Good": "Air quality is satisfactory. Enjoy outdoor activities.",
                        "Moderate": "Acceptable air quality. Unusually sensitive people should consider limiting prolonged outdoor exertion.",
                        "Unhealthy (SG)": "Members of sensitive groups may experience health effects. The general public is less likely to be affected.",
                        "Unhealthy": "Everyone may begin to experience health effects; sensitive groups may experience more serious effects.",
                        "Very Unhealthy": "Health alert: everyone may experience more serious health effects.",
                        "Hazardous": "Health warnings of emergency conditions. The entire population is more likely to be affected."
                    }
                    return advisories.get(label, "Take standard precautions.")

                st.markdown(f"""
                <div class="glass-card" style="border-left: 4px solid {level_color}; padding: 20px;">
                    <strong style="color: #E2E8F0; font-size: 1rem; display: flex; align-items: center; gap: 8px;">
                        <span>🛡️</span> Health Advisory
                    </strong>
                    <div style="margin-top: 8px; color: #94A3B8; font-size: 0.85rem; line-height: 1.5;">
                        Average AQI is <strong style="color: {level_color};">{level_label}</strong>. {get_advisory(level_label)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Top polluted list
                html_top = '''<div class="glass-card" style="padding: 20px;">
<strong style="color: #E2E8F0; font-size: 0.95rem; display: flex; align-items: center; gap: 8px;">
<span>⚠️</span> Top Polluted Zones
</strong>
<div style="margin-top: 16px; display: flex; flex-direction: column; gap: 12px;">\n'''
                for _, row in top_polluted.iterrows():
                    html_top += f'''<div style="display:flex; justify-content:space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.05);">
<span style="color:#94A3B8;font-size:0.85rem; font-family: monospace;">{row["lat"]:.3f}, {row["lon"]:.3f}</span>
<span style="color:#EF4444;font-weight:700;font-size:0.9rem;">{row["aqi"]:.0f} AQI</span>
</div>\n'''
                html_top += '</div></div>'
                st.markdown(html_top, unsafe_allow_html=True)
                
                # Cleanest list
                html_clean = '''<div class="glass-card" style="padding: 20px;">
<strong style="color: #E2E8F0; font-size: 0.95rem; display: flex; align-items: center; gap: 8px;">
<span>🌿</span> Cleanest Zones
</strong>
<div style="margin-top: 16px; display: flex; flex-direction: column; gap: 12px;">\n'''
                for _, row in cleanest.tail(3).iterrows():
                    html_clean += f'''<div style="display:flex; justify-content:space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.05);">
<span style="color:#94A3B8;font-size:0.85rem; font-family: monospace;">{row["lat"]:.3f}, {row["lon"]:.3f}</span>
<span style="color:#22C55E;font-weight:700;font-size:0.9rem;">{row["aqi"]:.0f} AQI</span>
</div>\n'''
                html_clean += '</div></div>'
                st.markdown(html_clean, unsafe_allow_html=True)

else:
    # ── Welcome / Landing State (ThreeJS) ──
    components.html('''
    <div id="globe-container" style="width: 100%; height: 100%; min-height: 480px; display: flex; justify-content: center; align-items: center; position: relative; font-family: 'Outfit', sans-serif;">
        <div style="position: absolute; z-index: 10; text-align: center; pointer-events: none;">
            <h1 style="font-size: 4rem; font-weight: 800; color: #fff; margin: 0; letter-spacing: -1px; text-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                Next-Gen <span style="background: linear-gradient(135deg, #ffffff, #a1a1aa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AQI</span> Intelligence
            </h1>
            <p style="color: #A1A1AA; font-size: 1.2rem; margin-top: 10px; font-weight: 300; letter-spacing: 0.5px;">
                Real-time downscaling and AI forecasting at scale.
            </p>
            <div style="margin-top: 30px; display: flex; justify-content: center; gap: 20px;">
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 15px 25px; border-radius: 12px; backdrop-filter: blur(10px);">
                    <span style="display: block; font-size: 1.5rem; font-weight: 700; color: #fff;">🛰️</span>
                    <span style="font-size: 0.8rem; color: #A1A1AA; text-transform: uppercase; letter-spacing: 1px;">Satellite</span>
                </div>
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 15px 25px; border-radius: 12px; backdrop-filter: blur(10px);">
                    <span style="display: block; font-size: 1.5rem; font-weight: 700; color: #fff;">🧠</span>
                    <span style="font-size: 0.8rem; color: #A1A1AA; text-transform: uppercase; letter-spacing: 1px;">AI Models</span>
                </div>
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 15px 25px; border-radius: 12px; backdrop-filter: blur(10px);">
                    <span style="display: block; font-size: 1.5rem; font-weight: 700; color: #fff;">🌍</span>
                    <span style="font-size: 0.8rem; color: #A1A1AA; text-transform: uppercase; letter-spacing: 1px;">Global</span>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        const container = document.getElementById('globe-container');
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x050505, 0.12);

        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.z = 5;

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer.domElement);

        // Core Sphere
        const geometry = new THREE.SphereGeometry(1.5, 64, 64);
        const material = new THREE.MeshBasicMaterial({
            color: 0x333333,
            wireframe: true,
            transparent: true,
            opacity: 0.15
        });
        const sphere = new THREE.Mesh(geometry, material);
        scene.add(sphere);

        // Particles
        const particleGeometry = new THREE.BufferGeometry();
        const particleCount = 5000;
        const posArray = new Float32Array(particleCount * 3);
        const colorArray = new Float32Array(particleCount * 3);

        for(let i = 0; i < particleCount; i++) {
            const u = Math.random();
            const v = Math.random();
            const theta = u * 2.0 * Math.PI;
            const phi = Math.acos(2.0 * v - 1.0);
            const r = 1.52 + Math.random() * 0.05;

            posArray[i*3] = r * Math.sin(phi) * Math.cos(theta);
            posArray[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
            posArray[i*3+2] = r * Math.cos(phi);

            // Silver/White/Cyan premium mix
            const rand = Math.random();
            if (rand > 0.8) {
                colorArray[i*3] = 0.0; colorArray[i*3+1] = 0.82; colorArray[i*3+2] = 1.0; // Cyan
            } else if (rand > 0.4) {
                colorArray[i*3] = 1.0; colorArray[i*3+1] = 1.0; colorArray[i*3+2] = 1.0; // White
            } else {
                colorArray[i*3] = 0.6; colorArray[i*3+1] = 0.6; colorArray[i*3+2] = 0.65; // Silver
            }
        }

        particleGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
        particleGeometry.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));

        const particleMaterial = new THREE.PointsMaterial({
            size: 0.012,
            vertexColors: true,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending
        });

        const particlesMesh = new THREE.Points(particleGeometry, particleMaterial);
        scene.add(particlesMesh);

        // Outer Glow Ring
        const ringGeo = new THREE.RingGeometry(1.9, 1.92, 64);
        const ringMat = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, transparent: true, opacity: 0.1 });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = Math.PI / 2;
        scene.add(ring);

        // Animation
        let mouseX = 0;
        let mouseY = 0;
        let targetX = 0;
        let targetY = 0;

        container.addEventListener('mousemove', (event) => {
            const rect = container.getBoundingClientRect();
            mouseX = (event.clientX - rect.left - container.clientWidth / 2) * 0.001;
            mouseY = (event.clientY - rect.top - container.clientHeight / 2) * 0.001;
        });

        const animate = () => {
            requestAnimationFrame(animate);

            targetX = mouseX * 0.5;
            targetY = mouseY * 0.5;

            particlesMesh.rotation.y += 0.0015;
            sphere.rotation.y += 0.001;
            
            particlesMesh.rotation.x += 0.05 * (targetY - particlesMesh.rotation.x);
            particlesMesh.rotation.y += 0.05 * (targetX - particlesMesh.rotation.y);
            
            ring.rotation.z -= 0.0005;

            renderer.render(scene, camera);
        };
        animate();

        window.addEventListener('resize', () => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });
    </script>
    <style>
        body { margin: 0; overflow: hidden; background: transparent; }
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    </style>
    ''', height=480)
    
    st.markdown('''
    <div style="text-align: center; margin-top: 20px;">
        <p style="color: #71717A; font-size: 0.9rem; font-family: 'Outfit', sans-serif;">
            Select a city and analysis mode from the controls above to begin.
        </p>
    </div>
    ''', unsafe_allow_html=True)
