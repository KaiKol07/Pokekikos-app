import streamlit as st
import requests
import math

# Configuración de la página
st.set_page_config(page_title="PokeKikos: God Mode", page_icon="🔥")

# --- 1. CONSTANTES DE REFERENCIA AJUSTADAS ---
# He bajado el "Máximo Normal" para que los stats de Megas/Legendarios 
# superen el 20 y tengan modificadores de +6, +7, etc.
REFERENCIAS = {
    'hp':  (1, 70, 150),  # Antes 255
    'atk': (5, 75, 150),  # Antes 190
    'def': (5, 70, 150),  # Antes 230
    'spa': (10, 70, 150), # Antes 194
    'spd': (20, 70, 150), # Antes 230
    'spe': (5, 65, 140)   # Antes 180
}

NOMBRES_DND = {
    'hp': 'CONSTITUCIÓN (CON)', 'atk': 'FUERZA (FUE)', 'def': 'DEFENSA (DEF)',
    'spa': 'INTELIGENCIA (INT)', 'spd': 'SABIDURÍA (SAB)', 'spe': 'DESTREZA (DES)'
}

def convertir_a_dnd(stat, tipo):
    minimo, media, maximo = REFERENCIAS[tipo]
    if stat <= media:
        # Tramo A: 1 a 10
        v = 1 + (stat - minimo) * (9 / (media - minimo))
    else:
        # Tramo B: 10 a 20 (y más allá si el stat > maximo)
        v = 10 + (stat - media) * (10 / (maximo - media))
    return round(v)

# --- 2. INTERFAZ ---
st.title("⚔️ PokeKikos: Fichas Tácticas")
st.info("Nota: Los Pokémon Legendarios y Megas ahora pueden superar el límite de 20.")

@st.cache_data
def obtener_nombres():
    res = requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000")
    return sorted([p['name'] for p in res.json()['results']])

nombres = obtener_nombres()
pokemon_elegido = st.selectbox("Busca un Pokémon:", [""] + nombres)

if pokemon_elegido:
    res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_elegido}")
    data = res.json()
    
    st.header(f"📊 {data['name'].upper()}")
    
    raw = {s['stat']['name']: s['base_stat'] for s in data['stats']}
    mapping = [
        ('hp', 'hp'), ('attack', 'atk'), ('defense', 'def'),
        ('special-attack', 'spa'), ('special-defense', 'spd'), ('speed', 'spe')
    ]
    
    dnd_final = {}
    
    # Mostrar Stats con detección de "Límite Roto"
    for api_name, ref_key in mapping:
        base = raw[api_name]
        score = convertir_a_dnd(base, ref_key)
        mod = math.floor((score - 10) / 2)
        dnd_final[ref_key] = {'score': score, 'mod': mod}
        
        signo = "+" if mod >= 0 else ""
        
        # Estética: Si supera 20, lo ponemos en negrita y con fuego
        if score > 20:
            st.write(f"🔥 **{api_name.capitalize()}**: {base} → `{score} ({signo}{mod})` — **{NOMBRES_DND[ref_key]}**")
        else:
            st.write(f"{api_name.capitalize()}: {base} → `{score} ({signo}{mod})` — {NOMBRES_DND[ref_key]}")

    st.divider()
    
    # Cálculos Tácticos
    hp_final = (dnd_final['hp']['score'] * 2) + 10
    ac_final = 10 + dnd_final['def']['mod']
    mov = max(2, round(dnd_final['spe']['score'] / 2))
    ini = dnd_final['spe']['mod']

    col1, col2 = st.columns(2)
    with col1:
        st.metric("❤️ Vida (HP)", hp_final)
        st.metric("🛡️ Armadura (AC)", ac_final)
    with col2:
        st.metric("🏃 Movimiento", f"{mov} hex")
        st.metric("⚡ Iniciativa", f"{'+' if ini >= 0 else ''}{ini}")

    # Mensaje de advertencia si es una bestia parda
    if any(v['score'] > 20 for v in dnd_final.values()):
        st.warning("⚠️ ESTA CRIATURA TIENE PODER LEGENDARIO (SUPERIOR A 20)")