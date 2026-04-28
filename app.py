import streamlit as st
import requests
import math

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="PokeKikos: Tactic Tool", page_icon="⚔️")

# --- 1. CONSTANTES DE REFERENCIA (Manual PokeKikos) ---
REFERENCIAS = {
    'hp':  (1, 70, 200), 
    'atk': (5, 78, 165), 
    'def': (5, 72, 200), 
    'spa': (10, 71, 145),
    'spd': (20, 70, 200),
    'spe': (5, 67, 160),
    'cha': (0, 150, 252)
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

# --- 2. FUNCIONES LÓGICAS COMPARTIDAS ---
def convertir_a_dnd(stat, tipo):
    """Aplica interpolación bilineal según el manual[cite: 9, 11, 36]."""
    minimo, media, maximo = REFERENCIAS[tipo]
    if stat <= media:
        v = 1 + (stat - minimo) * (9 / (media - minimo))
    else:
        v = 10 + (stat - media) * (10 / (maximo - media))
    return round(v)

def get_dice_damage(power):
    """Convierte potencia base en dados de daño."""
    if not power: return "---"
    if power <= 45: return "1d6"
    if power <= 85: return "1d10"
    if power <= 110: return "2d8"
    return "3d10"

@st.cache_data
def obtener_nombres_pokedex():
    res = requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000")
    return sorted([p['name'] for p in res.json()['results']])

@st.cache_data
def obtener_nombres_movimientos():
    res = requests.get("https://pokeapi.co/api/v2/move?limit=1000")
    return sorted([m['name'] for m in res.json()['results']])

# --- 3. NAVEGACIÓN ---
st.sidebar.title("🎮 PokeKikos Hub")
opcion = st.sidebar.radio("Selecciona herramienta:", ["Generador de Pokémon", "Buscador de Ataques"])

# --- SECCIÓN A: GENERADOR DE POKÉMON (Basado en NOapp.py) ---
if opcion == "Generador de Pokémon":
    st.title("🛡️ Generador de Fichas")
    
    nombres = obtener_nombres_pokedex()
    pokemon_elegido = st.selectbox("Selecciona tu Pokémon:", [""] + nombres)

    if pokemon_elegido:
        res_pkmn = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_elegido}")
        data = res_pkmn.json()
        res_species = requests.get(data['species']['url'])
        data_species = res_species.json()
        
        st.header(f"📊 {data['name'].upper()}")
        raw = {s['stat']['name']: s['base_stat'] for s in data['stats']}
        ratio_captura = data_species.get('capture_rate', 100)
        raw['cha'] = max(0, 255 - ratio_captura)
        
        mapping = [('hp', 'hp'), ('attack', 'atk'), ('defense', 'def'),
                   ('special-attack', 'spa'), ('special-defense', 'spd'), 
                   ('speed', 'spe'), ('cha', 'cha')]
        
        dnd_final = {}
        st.subheader("Atributos D&D")
        for api_name, ref_key in mapping:
            base_val = raw.get(api_name, 0)
            score = convertir_a_dnd(base_val, ref_key)
            mod = math.floor((score - 10) / 2)
            dnd_final[ref_key] = {'score': score, 'mod': mod}
            
            signo = "+" if mod >= 0 else ""
            label = NOMBRES_DND[ref_key]
            if score > 20:
                st.write(f"🔥 **{label}**: `{score} ({signo}{mod})`")
            else:
                st.write(f"**{label}**: `{score} ({signo}{mod})`")

        st.divider()
        
        # Estadísticas de Combate [cite: 20, 21, 23]
        hp_final = (dnd_final['hp']['score'] * 2) + 10
        ac_final = 10 + dnd_final['def']['mod']
        mov = max(2, round(dnd_final['spe']['score'] / 2))
        
        st.subheader("Combate")
        c1, c2 = st.columns(2)
        c1.metric("❤️ Vida (HP)", hp_final)
        c1.metric("🛡️ Armadura (AC)", ac_final)
        c2.metric("🏃 Movimiento", f"{mov} hex")
        c2.metric("⚡ Iniciativa", f"{'+' if dnd_final['spe']['mod'] >= 0 else ''}{dnd_final['spe']['mod']}")

# --- SECCIÓN B: BUSCADOR DE ATAQUES (Nuevo) ---
else:
    st.title("⚔️ Calculadora de Movimientos")
    st.markdown("Calcula el daño y el tipo de defensa según las reglas de PokeKikos.")
    
    lista_ataques = obtener_nombres_movimientos()
    ataque_elegido = st.selectbox("Busca un ataque (Inglés):", [""] + lista_ataques)

    if ataque_elegido:
        res = requests.get(f"https://pokeapi.co/api/v2/move/{ataque_elegido}")
        if res.status_code == 200:
            m_data = res.json()
            power = m_data.get('power')
            tipo = m_data['type']['name'].upper()
            clase = m_data['damage_class']['name']
            acc = m_data.get('accuracy', 100)
            dice = get_dice_damage(power)
            
            # Asignación de atributo para el ataque [cite: 42, 43]
            attr_mod = "FUERZA" if clase == "physical" else "INTELIGENCIA"
            if clase == "status": attr_mod = "SAB/INT"

            # Color por tipo
            colors = {"fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030", "psychic": "#F85888"}
            bg_color = colors.get(m_data['type']['name'], "#68A090")

            st.markdown(f"""
            <div style="border: 4px solid {bg_color}; border-radius: 12px; padding: 15px; background-color: #fff; color: #333;">
                <h2 style="background-color: {bg_color}; color: white; padding: 5px; border-radius: 5px; text-align: center;">
                    {m_data['name'].replace('-', ' ').upper()}
                </h2>
                <div style="display: flex; justify-content: space-between; font-weight: bold;">
                    <span>TIPO: {tipo}</span>
                    <span>CLASE: {clase.upper()}</span>
                </div>
                <hr>
                <h3 style="margin: 0; color: #d32f2f;">DAÑO: {dice} + Mod. {attr_mod}</h3>
                <p><b>PRECISIÓN:</b> {acc if acc else '---'} | <b>POTENCIA BASE:</b> {power if power else '0'}</p>
                <div style="background: #f0f0f0; padding: 10px; border-radius: 5px; font-size: 0.9em;">
                    <b>EFECTO:</b> {m_data['effect_entries'][0]['short_effect'] if m_data['effect_entries'] else 'No special effect.'}
                </div>
            </div>
            """, unsafe_allow_html=True)