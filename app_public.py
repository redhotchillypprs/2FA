"""
Autenticador 2FA — Versión Pública
Las llaves se guardan en st.session_state (memoria de sesión).
Cada usuario maneja sus propias llaves. Al cerrar el navegador, se borran.
"""

import time
import pyotp
import streamlit as st

# ──────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Autenticador 2FA",
    page_icon="🔐",
    layout="centered",
)

# ──────────────────────────────────────────────
# ESTILOS
# ──────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    .block-container {
        max-width: 680px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .codigo-card {
        background: #0d1117;
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .codigo-nombre {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 13px;
        color: #8b949e;
        margin-bottom: 4px;
    }
    .codigo-numero {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 28px;
        font-weight: 600;
        color: #3fb950;
        letter-spacing: 6px;
    }
    .codigo-numero.expirando {
        color: #d29922;
    }
    .codigo-numero.critico {
        color: #f85149;
    }

    .barra-wrap {
        background: #21262d;
        border-radius: 4px;
        height: 4px;
        margin-top: 8px;
        overflow: hidden;
    }
    .barra-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.8s linear;
    }

    .app-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .app-header h1 {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 22px;
        font-weight: 600;
        color: #3fb950;
        letter-spacing: 2px;
        margin: 0;
    }
    .app-header p {
        font-size: 13px;
        color: #8b949e;
        margin: 4px 0 0;
    }

    .instruccion-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 3px solid #3fb950;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
    .instruccion-box p {
        margin: 0;
        font-size: 13px;
        color: #c9d1d9;
        line-height: 1.6;
    }
    .instruccion-box code {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 2px 6px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        color: #3fb950;
    }

    .aviso-sesion {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 3px solid #d29922;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 16px;
        font-size: 12px;
        color: #8b949e;
        line-height: 1.6;
    }

    .stButton > button {
        border-radius: 8px;
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 500;
        transition: all 0.15s ease;
    }

    .sep {
        border: none;
        border-top: 1px solid #21262d;
        margin: 1.5rem 0;
    }

    .badge-tiempo {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
    }

    .llave-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #0d1117;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 8px;
        font-size: 13px;
        color: #c9d1d9;
    }
    .llave-nombre {
        font-family: 'IBM Plex Mono', monospace;
        color: #3fb950;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# FUNCIONES TOTP
# ──────────────────────────────────────────────

def generar_codigo(secreto: str) -> str:
    """Genera el código TOTP actual para un secreto Base32."""
    try:
        totp = pyotp.TOTP(secreto.strip().upper().replace(" ", ""))
        return totp.now()
    except Exception:
        return "INVALID"

def tiempo_restante() -> int:
    """Segundos restantes en el ciclo TOTP actual (0-30)."""
    return 30 - (int(time.time()) % 30)

# ──────────────────────────────────────────────
# ESTADO DE SESIÓN
# ──────────────────────────────────────────────

if "pantalla" not in st.session_state:
    st.session_state.pantalla = "codigos"

if "llaves" not in st.session_state:
    st.session_state.llaves = {}   # {nombre: secreto}

# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────

st.markdown("""
<div class="app-header">
    <h1>🔐 AUTENTICADOR 2FA</h1>
    <p>Códigos de un solo uso · TOTP RFC 6238</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# NAVEGACIÓN
# ──────────────────────────────────────────────

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📋  Ver códigos", use_container_width=True,
                 type="primary" if st.session_state.pantalla == "codigos" else "secondary"):
        st.session_state.pantalla = "codigos"
        st.rerun()
with col2:
    if st.button("➕  Agregar llave", use_container_width=True,
                 type="primary" if st.session_state.pantalla == "agregar" else "secondary"):
        st.session_state.pantalla = "agregar"
        st.rerun()
with col3:
    if st.button("🗂️  Mis llaves", use_container_width=True,
                 type="primary" if st.session_state.pantalla == "gestionar" else "secondary"):
        st.session_state.pantalla = "gestionar"
        st.rerun()

st.markdown('<hr class="sep">', unsafe_allow_html=True)

# Aviso de sesión siempre visible
st.markdown("""
<div class="aviso-sesion">
    ⚠️ <strong>Sesión temporal</strong> · Tus llaves solo existen mientras esta pestaña esté abierta.
    Al cerrar el navegador o recargar la página, se borran. No se guardan en ningún servidor.
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PANTALLA: CÓDIGOS EN VIVO
# ──────────────────────────────────────────────

if st.session_state.pantalla == "codigos":

    llaves = st.session_state.llaves

    if not llaves:
        st.markdown("""
        <div class="instruccion-box">
            <p>⚠️ No hay llaves en esta sesión todavía.<br>
            Ve a <strong>Agregar llave</strong> para registrar tu primera clave 2FA.</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        seg = tiempo_restante()
        pct = (seg / 30) * 100

        if seg > 10:
            color_barra = "#3fb950"
            color_clase = "codigo-numero"
        elif seg > 5:
            color_barra = "#d29922"
            color_clase = "codigo-numero expirando"
        else:
            color_barra = "#f85149"
            color_clase = "codigo-numero critico"

        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:20px;">
            <span style="font-family:'IBM Plex Sans',sans-serif; font-size:13px; color:#8b949e;">
                Próxima actualización
            </span>
            <span class="badge-tiempo" style="
                background:{'#0d2010' if seg > 10 else '#1c1700' if seg > 5 else '#1c0800'};
                color:{color_barra};
                border: 1px solid {color_barra}33;
            ">{seg:02d}s</span>
        </div>
        <div class="barra-wrap" style="margin-bottom:24px;">
            <div class="barra-fill" style="width:{pct:.0f}%; background:{color_barra};"></div>
        </div>
        """, unsafe_allow_html=True)

        for nombre, secreto in llaves.items():
            codigo = generar_codigo(secreto)
            codigo_fmt = f"{codigo[:3]} {codigo[3:]}" if len(codigo) == 6 else codigo

            st.markdown(f"""
            <div class="codigo-card">
                <div>
                    <div class="codigo-nombre">{nombre}</div>
                    <div class="{color_clase}">{codigo_fmt}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        time.sleep(1)
        st.rerun()

# ──────────────────────────────────────────────
# PANTALLA: AGREGAR LLAVE
# ──────────────────────────────────────────────

elif st.session_state.pantalla == "agregar":

    st.markdown("""
    <div class="instruccion-box">
        <p>
        Ingresa el nombre del servicio y la clave secreta Base32 que te dio la app
        o sitio web al activar el 2FA.<br><br>
        <strong>¿Dónde encuentro la clave Base32?</strong><br>
        Al activar 2FA en cualquier servicio, normalmente aparece un código QR
        y debajo una opción como <code>¿No puedes escanear?</code> o
        <code>Ingresar manualmente</code> — ahí está tu clave Base32.
        </p>
    </div>
    """, unsafe_allow_html=True)

    nombre = st.text_input(
        "Nombre del servicio",
        placeholder="Ej: GitHub, Google, Banco...",
        max_chars=40
    )
    secreto = st.text_input(
        "Clave secreta (Base32)",
        placeholder="Ej: JBSWY3DPEHPK3PXP",
        type="password"
    )

    if nombre and secreto:
        secreto_limpio = secreto.strip().upper().replace(" ", "")
        codigo_prueba = generar_codigo(secreto_limpio)

        if codigo_prueba == "INVALID":
            st.error("❌ La clave secreta no es un Base32 válido. Verifica que la copiaste correctamente.")
        else:
            st.success(f"✅ Clave válida · Código actual: **{codigo_prueba[:3]} {codigo_prueba[3:]}**")

            nombre_clave = nombre.strip()

            if nombre_clave in st.session_state.llaves:
                st.warning(f"⚠️ Ya existe una llave llamada **{nombre_clave}**. Guardar reemplazará la anterior.")

            if st.button("💾  Guardar llave en esta sesión", type="primary"):
                st.session_state.llaves[nombre_clave] = secreto_limpio
                st.success(f"✅ **{nombre_clave}** guardada. Ya puedes ver su código en **Ver códigos**.")
                st.session_state.pantalla = "codigos"
                st.rerun()

# ──────────────────────────────────────────────
# PANTALLA: GESTIONAR LLAVES
# ──────────────────────────────────────────────

elif st.session_state.pantalla == "gestionar":

    llaves = st.session_state.llaves

    if not llaves:
        st.markdown("""
        <div class="instruccion-box">
            <p>No hay llaves en esta sesión todavía.<br>
            Ve a <strong>Agregar llave</strong> para registrar tu primera clave 2FA.</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div class="instruccion-box">
            <p>Tienes <strong>{len(llaves)}</strong> llave{'s' if len(llaves) != 1 else ''} en esta sesión.
            Puedes eliminar las que ya no necesites.</p>
        </div>
        """, unsafe_allow_html=True)

        for nombre in list(llaves.keys()):
            col_nombre, col_btn = st.columns([4, 1])
            with col_nombre:
                st.markdown(f"""
                <div class="llave-row">
                    <span class="llave-nombre">{nombre}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if st.button("🗑️", key=f"del_{nombre}", help=f"Eliminar {nombre}"):
                    del st.session_state.llaves[nombre]
                    st.rerun()

        st.markdown('<hr class="sep">', unsafe_allow_html=True)

        if st.button("🗑️  Borrar todas las llaves", type="secondary"):
            st.session_state.llaves = {}
            st.session_state.pantalla = "codigos"
            st.rerun()
