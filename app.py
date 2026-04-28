import streamlit as st
import requests
import math

# Configuración de la página para móviles
st.set_page_config(page_title="PokeKikos App", page_icon="🔥")

# --- 1. CONSTANTES DE REFERENCIA ---
REFERENCIAS = {
    'hp':  (1, 128, 255), 
    'atk': (5, 85, 165), 
    'def': (5, 117, 230), 
    'spa': (10, 77, 145),
    'spd': (20, 125, 230),
    'spe': (5, 82, 160),
    'cha': (0, 150, 252)  # 255 - Capture Rate
}

NOMBRES_DND = {
    'hp': 'CONSTITUCIÓN (CON)', 
    'atk': 'FUERZA (FUE)', 
    'def': 'DEFENSA (DEF)',
    'spa': 'INTELIGENCIA (INT)', 
    'spd': 'SABIDURÍA (SAB)', 
    'spe': 'DESTREZA (DES)',
    'cha': 'CARISMA (CAR)'
}

# --- 2. FUNCIONES LÓGICAS ---
def convertir_a_dnd(stat, tipo):
    minimo, media, maximo = REFERENCIAS[tipo]
    if stat <= media:
        v = 1 + (stat - minimo) * (9 / (media - minimo))
    else:
        v = 10 + (stat - media) * (10 / (maximo - media))
    return round(v)

@st.cache_data
def obtener_nombres_pokedex():
    res = requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000")
    return sorted([p['name'] for p in res.json()['results']])

# --- 3. INTERFAZ DE USUARIO ---
st.title("⚔️ PokeKikos: Fichas de Rol")
st.markdown("Generador de estadísticas para el juego de tablero.")

nombres = obtener_nombres_pokedex()
pokemon_elegido = st.selectbox("Busca o selecciona tu Pokémon:", [""] + nombres)

if pokemon_elegido:
    # Obtener datos del Pokémon y de su especie
    res_pkmn = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_elegido}")
    data = res_pkmn.json()
    
    res_species = requests.get(data['species']['url'])
    data_species = res_species.json()
    
    st.header(f"📊 {data['name'].upper()}")
    
    # Procesar estadísticas base
    raw = {s['stat']['name']: s['base_stat'] for s in data['stats']}
    
    # Lógica de Carisma (Inversión del Ratio de Captura)
    ratio_captura = data_species.get('capture_rate', 100)
    raw['cha'] = max(0, 255 - ratio_captura)
    
    mapping = [
        ('hp', 'hp'), ('attack', 'atk'), ('defense', 'def'),
        ('special-attack', 'spa'), ('special-defense', 'spd'), 
        ('speed', 'spe'), ('cha', 'cha')
    ]
    
    dnd_final = {}
    
    # Listado de Atributos
    st.subheader("Atributos D&D")
    for api_name, ref_key in mapping:
        base_val = raw.get(api_name, 0)
        score = convertir_a_dnd(base_val, ref_key)
        mod = math.floor((score - 10) / 2)
        dnd_final[ref_key] = {'score': score, 'mod': mod}
        
        signo = "+" if mod >= 0 else ""
        label = NOMBRES_DND[ref_key]
        
        # Resaltar si es legendario (>20)
        if score > 20:
            st.write(f"🔥 **{label}**: `{score} ({signo}{mod})`")
        else:
            st.write(f"**{label}**: `{score} ({signo}{mod})`")

    st.divider()
    
    # Cálculos para el Tablero
    hp_final = (dnd_final['hp']['score'] * 2) + 10
    ac_final = 10 + dnd_final['def']['mod']
    mov = max(2, round(dnd_final['spe']['score'] / 2))
    ini = dnd_final['spe']['mod']

    # Visualización en métricas (ideal para móvil)
    st.subheader("Estadísticas de Combate")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("❤️ Vida (HP)", hp_final)
        st.metric("🛡️ Armadura (AC)", ac_final)
    with c2:
        st.metric("🏃 Movimiento", f"{mov} hex")
        st.metric("⚡ Iniciativa", f"{'+' if ini >= 0 else ''}{ini}")

    if any(v['score'] > 20 for v in dnd_final.values()):
        st.warning("⚠️ ESTA CRIATURA SUPERA LOS LÍMITES HUMANOS (PODER LEYENDA)")