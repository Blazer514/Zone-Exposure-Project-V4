
import math
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# --- Utility functions ---
def shutter_to_ev(t_seconds: float) -> float:
    return -math.log2(t_seconds)

def ev_to_shutter(ev: float) -> float:
    return 1 / (2 ** ev)

def format_shutter(t: float) -> str:
    if t >= 1:
        return f"{int(round(t))}s"
    else:
        return f"1/{int(round(1/t))}s"

STANDARD_SHUTTERS = [
    30, 15, 8, 4, 2, 1,
    1/2, 1/4, 1/8, 1/15, 1/30, 1/60,
    1/125, 1/250, 1/500, 1/1000, 1/2000, 1/4000
]

def nearest_standard_shutter(t: float) -> float:
    return min(STANDARD_SHUTTERS, key=lambda s: abs(s - t))

# --- Zone System Logic ---
def compute_zone5_ev(zone_choice: int, readings_ev: dict) -> float:
    if 'Darkest' in readings_ev:
        return readings_ev['Darkest'] + (5 - zone_choice)
    elif 'Subject' in readings_ev:
        return readings_ev['Subject']
    elif 'Midtone' in readings_ev:
        return readings_ev['Midtone']
    else:
        return list(readings_ev.values())[0]

def zone_from_reading(ev_read: float, ev_final: float) -> float:
    return 5 + (ev_final - ev_read)

def recommend_exposure(aperture: float, iso: int, zone_choice: int,
                       brightest=None, darkest=None, midtone=None, subject=None):
    readings_ev = {}
    if brightest is not None: readings_ev['Brightest'] = shutter_to_ev(brightest)
    if darkest   is not None: readings_ev['Darkest']   = shutter_to_ev(darkest)
    if midtone   is not None: readings_ev['Midtone']   = shutter_to_ev(midtone)
    if subject   is not None: readings_ev['Subject']   = shutter_to_ev(subject)

    if not readings_ev:
        return "No valid readings provided.", None, {}, None

    ev_final = compute_zone5_ev(zone_choice, readings_ev)

    lines = []
    if 'Brightest' in readings_ev and 'Darkest' in readings_ev:
        scene_range = readings_ev['Brightest'] - readings_ev['Darkest']
        lines.append(f"Scene brightness range: {scene_range:.2f} stops")

    if 'Darkest' in readings_ev:
        lines.append(f"Placing darkest on Zone {zone_choice} → Zone V EV = {ev_final:.2f}")
    elif 'Subject' in readings_ev:
        lines.append(f"Using subject as Zone V → Zone V EV = {ev_final:.2f}")
    elif 'Midtone' in readings_ev:
        lines.append(f"Using midtone as Zone V → Zone V EV = {ev_final:.2f}")

    reference_aperture = 16
    reference_iso = 100
    aperture_adjust = math.log2((aperture / reference_aperture) ** 2)
    iso_adjust = math.log2(iso / reference_iso)
    ev_for_shutter = ev_final - aperture_adjust - iso_adjust

    t = ev_to_shutter(ev_for_shutter)
    t_std = nearest_standard_shutter(t)
    shutter_str = format_shutter(t_std)
    lines.append(f"Suggested exposure ≈ {shutter_str} at f/{aperture} ISO {iso}")

    zones_map = {label: zone_from_reading(ev, ev_final) for label, ev in readings_ev.items()}

    return "\n".join(lines), ev_final, zones_map, t_std

# --- Visualization ---
def plot_zone_system(zones_map: dict):
    fig, ax = plt.subplots(figsize=(10, 2.6))
    gradient = np.linspace(0, 1, 1100).reshape(1, -1)
    ax.imshow(gradient, aspect='auto', cmap='gray', extent=[0, 10, 0, 1])

    for z in range(0, 11):
        ax.axvline(z, color='white', linestyle='--', linewidth=0.5, alpha=0.4)

    colors = {
        'Brightest': 'gold',
        'Darkest':   'royalblue',
        'Midtone':   'seagreen',
        'Subject':   'purple',
        'Suggested': 'red'
    }

    ax.plot(5, 1.10, 'o', color=colors['Suggested'], markersize=10)
    ax.text(5, 1.22, 'Suggested (Z5)', color=colors['Suggested'], ha='center', va='bottom', fontsize=10)

    for label, zpos in zones_map.items():
        z = max(0, min(10, zpos))
        ax.plot(z, 1.08, 'o', color=colors.get(label, 'black'), markersize=8)
        ax.text(z, 1.20, f"{label} (Z{zpos:.1f})", color=colors.get(label, 'black'),
                ha='center', va='bottom', fontsize=9)

    ax.set_xlim(0, 10)
    ax.set_xticks(range(0, 11))
    ax.set_yticks([])
    ax.set_xlabel('Zone System (0–10)')
    ax.set_ylim(0, 1.28)
    plt.tight_layout()
    return fig

# --- Streamlit UI ---
st.set_page_config(page_title="Zone System Calculator", layout="centered")
st.title("🎞️ Zone System Exposure Calculator")

colA, colB, colC = st.columns(3)
with colA:
    aperture = st.selectbox("🔘 Aperture (f-stop)",
                            [1.4, 2, 2.8, 4, 5.6, 8, 11, 16, 22, 32],
                            index=7)
with colB:
    iso = st.selectbox("🎞️ ISO", [25, 50, 100, 200, 400, 800, 1600, 3200], index=2)
with colC:
    zone_choice = st.radio("🌑 Place darkest in:", [2, 3], index=1, horizontal=True)

st.markdown("---")

st.subheader("Light Meter Readings (Shutter Speeds)")
col1, col2 = st.columns(2)
with col1:
    brightest = st.select_slider("☀️ Brightest part", options=STANDARD_SHUTTERS,
                                 value=1/125, format_func=format_shutter)
    midtone   = st.select_slider("🌗 Mid-tone", options=STANDARD_SHUTTERS,
                                 value=1/60, format_func=format_shutter)
with col2:
    darkest = st.select_slider("🌑 Darkest part", options=STANDARD_SHUTTERS,
                               value=1/30, format_func=format_shutter)
    subject = st.select_slider("🎯 Subject", options=STANDARD_SHUTTERS,
                               value=1/60, format_func=format_shutter)

st.markdown("---")

if st.button("📸 Calculate Exposure"):
    text, ev_final, zones_map, t_std = recommend_exposure(aperture, iso, zone_choice,
                                                          brightest=brightest, darkest=darkest,
                                                          midtone=midtone, subject=subject)
    st.markdown(
        f"<div style='background:#f8f9fa;border-radius:14px;padding:16px;"
        f"box-shadow:0 4px 8px rgba(0,0,0,0.06)'><pre>{text}</pre></div>",
        unsafe_allow_html=True
    )
    if ev_final is not None:
        fig = plot_zone_system(zones_map)
        st.pyplot(fig)
