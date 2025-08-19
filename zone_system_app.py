
import math
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# --- Core Functions ---
standard_shutters = [
    30, 15, 8, 4, 2, 1,
    1/2, 1/4, 1/8, 1/15, 1/30, 1/60,
    1/125, 1/250, 1/500, 1/1000, 1/2000, 1/4000
]

def nearest_standard_shutter(value):
    return min(standard_shutters, key=lambda x: abs(x - value))

def shutter_to_ev(shutter_speed):
    if not shutter_speed:
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
    if brightest: readings['Brightest'] = shutter_to_ev(brightest)
    if darkest: readings['Darkest'] = shutter_to_ev(darkest)
    if midtone: readings['Midtone'] = shutter_to_ev(midtone)
    if subject: readings['Subject'] = shutter_to_ev(subject)

    readings = {k: v for k, v in readings.items() if v is not None}
    if not readings:
        return "No valid readings provided.", None, {}

    output = []

    # Zone placement suggestion
    if 'Darkest' in readings:
        zone_offset = 2 if zone_choice == "Zone II" else 3
        suggested_ev = readings['Darkest'] + zone_offset
        output.append(f"Place darkest part on {zone_choice} → Suggested EV: {suggested_ev:.2f}")
    elif 'Subject' in readings:
        suggested_ev = readings['Subject']
        output.append(f"Place subject on Zone V → Suggested EV: {suggested_ev:.2f}")
    elif 'Midtone' in readings:
        suggested_ev = readings['Midtone']
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

    # Convert EV back to shutter speed and snap to nearest standard
    shutter_speed = ev_to_shutter(adjusted_ev)
    shutter_speed = nearest_standard_shutter(shutter_speed)
    shutter_str = shutter_label(shutter_speed)

    output.append(f"Suggested exposure ≈ {shutter_str} at f/{aperture} ISO {iso}")

    return "\n".join(output), adjusted_ev, readings

def plot_zone_system(adjusted_ev, readings):
    fig, ax = plt.subplots(figsize=(10, 2))
    zones = np.arange(0, 11)
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    ax.imshow(gradient, aspect="auto", cmap="gray", extent=[0, 10, 0, 1])

    # Plot suggested exposure
    suggested_zone = adjusted_ev
    ax.plot([suggested_zone, suggested_zone], [0, 1], color="red", linewidth=2, label="Suggested")
    ax.text(suggested_zone, 1.05, "Suggested", color="red", ha="center")

    # Plot other readings
    colors = {"Brightest": "yellow", "Darkest": "blue", "Midtone": "green", "Subject": "purple"}
    for label, ev in readings.items():
        zone_pos = ev
        ax.plot([zone_pos, zone_pos], [0, 1], color=colors[label], linewidth=2, label=label)
        ax.text(zone_pos, -0.3, label, color=colors[label], ha="center")

    ax.set_xlim(0, 10)
    ax.set_xticks(zones)
    ax.set_yticks([])
    ax.set_xlabel("Zone System (0–10)")
    ax.legend(loc="upper right")
    plt.tight_layout()
    return fig

# --- Streamlit UI ---
st.set_page_config(page_title="Zone System Calculator", layout="centered")
st.title("🎞️ Zone System Exposure Calculator")

# Top controls
aperture = st.selectbox("🔘 Aperture (f-stop)", [1.4, 2, 2.8, 4, 5.6, 8, 11, 16, 22, 32], index=7)
iso = st.selectbox("🎞️ ISO", [25, 50, 100, 200, 400, 800, 1600, 3200], index=2)
zone_choice = st.radio("🌑 Place darkest part in:", ["Zone II", "Zone III"], horizontal=True)

col1, col2 = st.columns(2)
with col1:
    brightest = st.select_slider("☀️ Brightest part of the scene", options=standard_shutters, value=1/125,
                                 format_func=shutter_label)
    midtone = st.select_slider("🌗 Mid-tone reading", options=standard_shutters, value=1/60,
                               format_func=shutter_label)
with col2:
    darkest = st.select_slider("🌑 Darkest part of the scene", options=standard_shutters, value=1/30,
                               format_func=shutter_label)
    subject = st.select_slider("🎯 Subject reading", options=standard_shutters, value=1/60,
                               format_func=shutter_label)

if st.button("📸 Calculate Exposure"):
    result, adjusted_ev, readings = recommend_exposure(aperture, iso, zone_choice, brightest, darkest, midtone, subject)
    st.markdown(f"<div class='result-box'><pre>{result}</pre></div>", unsafe_allow_html=True)
    if adjusted_ev is not None:
        fig = plot_zone_system(adjusted_ev, readings)
        st.pyplot(fig)
