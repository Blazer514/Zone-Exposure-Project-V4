import math
import streamlit as st

# --- Core Functions ---
def shutter_to_ev(shutter_speed):
    if not shutter_speed:
        return None
    try:
        shutter_speed = float(shutter_speed)
    except:
        return None
    return -math.log2(shutter_speed)

def ev_to_shutter(ev):
    return 1 / (2 ** ev)

def shutter_label(shutter_speed):
    if shutter_speed >= 1:
        return f"{shutter_speed:.0f}s"
    else:
        return f"1/{round(1/shutter_speed):.0f}s"

def recommend_exposure(aperture, iso, zone_choice, brightest=None, darkest=None, midtone=None, subject=None):
    readings = {}
    if brightest: readings['brightest'] = shutter_to_ev(brightest)
    if darkest: readings['darkest'] = shutter_to_ev(darkest)
    if midtone: readings['midtone'] = shutter_to_ev(midtone)
    if subject: readings['subject'] = shutter_to_ev(subject)

    readings = {k: v for k, v in readings.items() if v is not None}
    if not readings:
        return "No valid readings provided."

    output = []

    # Scene range
    if 'brightest' in readings and 'darkest' in readings:
        scene_range = readings['brightest'] - readings['darkest']
        output.append(f"Scene brightness range: {scene_range:.2f} stops")

    # Zone placement suggestion
    if 'darkest' in readings:
        zone_offset = zone_choice - 1  # Zone II = +1, Zone III = +2 relative to darkest
        suggested_ev = readings['darkest'] + zone_offset
        output.append(f"Place shadows on Zone {zone_choice} → Suggested EV: {suggested_ev:.2f}")
        if 'brightest' in readings:
            highlight_zone = readings['brightest'] - suggested_ev
            output.append(f"Highlights would fall at Zone {5 + highlight_zone:.1f}")
    elif 'subject' in readings:
        suggested_ev = readings['subject']
        output.append(f"Place subject on Zone V → Suggested EV: {suggested_ev:.2f}")
    elif 'midtone' in readings:
        suggested_ev = readings['midtone']
        output.append(f"Use midtone reading (Zone V) → Suggested EV: {suggested_ev:.2f}")
    else:
        suggested_ev = list(readings.values())[0]
        output.append(f"Fallback: using first reading → Suggested EV: {suggested_ev:.2f}")

    # Adjust EV for aperture and ISO (reference EV is f/16 ISO 100)
    reference_aperture = 16
    reference_iso = 100
    aperture_adjust = math.log2((aperture / reference_aperture) ** 2)
    iso_adjust = math.log2(iso / reference_iso)
    adjusted_ev = suggested_ev - aperture_adjust - iso_adjust

    # Convert EV back to shutter speed
    shutter_speed = ev_to_shutter(adjusted_ev)
    if shutter_speed >= 1:
        shutter_str = f"{shutter_speed:.0f}s"
    else:
        shutter_str = f"1/{round(1/shutter_speed):.0f}s"

    output.append(f"Suggested exposure ≈ {shutter_str} at f/{aperture} ISO {iso}")

    return "\n".join(output)

# --- Web App (Streamlit with styled UI + sliders + aperture/ISO) ---
st.set_page_config(page_title="Zone System Calculator", layout="centered")

st.title("🎞️ Zone System Exposure Calculator")

# --- Top controls: Aperture, ISO, Zone placement ---
st.subheader("Camera Settings")
col_top1, col_top2, col_top3 = st.columns(3)

aperture_list = [1.0, 1.4, 2.0, 2.8, 4.0, 5.6, 8.0, 11.0, 16.0, 22.0, 32.0, 45.0, 64.0]
iso_list = [25, 50, 100, 200, 400, 800, 1600, 3200, 6400, 12800]

with col_top1:
    aperture = st.selectbox("🔘 Aperture (f-stop)", aperture_list, index=aperture_list.index(16.0))
with col_top2:
    iso = st.selectbox("🎞️ ISO", iso_list, index=iso_list.index(100))
with col_top3:
    zone_choice = st.radio("🌓 Place darkest part of scene in:", options=[2, 3], index=1)

st.markdown("---")

# --- Sliders for shutter readings ---
st.subheader("Light Meter Readings")

shutter_speeds = [
    30, 15, 8, 4, 2, 1,
    1/2, 1/4, 1/8, 1/15, 1/30, 1/60, 1/125,
    1/250, 1/500, 1/1000, 1/2000, 1/4000
]

col1, col2 = st.columns(2)
with col1:
    brightest = st.select_slider("☀️ Brightest part of the scene", options=shutter_speeds, value=1/125, format_func=shutter_label)
    midtone = st.select_slider("🌗 Mid-tone reading", options=shutter_speeds, value=1/60, format_func=shutter_label)
with col2:
    darkest = st.select_slider("🌑 Darkest part of the scene", options=shutter_speeds, value=1/15, format_func=shutter_label)
    subject = st.select_slider("🎯 Subject reading", options=shutter_speeds, value=1/30, format_func=shutter_label)

st.markdown("---")

if st.button("📸 Calculate Exposure"):
    result = recommend_exposure(aperture, iso, zone_choice, brightest, darkest, midtone, subject)
    st.markdown(f"<div class='result-box'><pre>{result}</pre></div>", unsafe_allow_html=True)
