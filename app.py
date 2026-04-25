"""
Autenticador 2FA — Streamlit Cloud
Almacena llaves en st.secrets (secrets.toml)
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
    /* Fuente y fondo general */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* Ocultar el menú hamburguesa y footer de Streamlit */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Contenedor principal más angosto */
    .block-container {
        max-width: 680px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Tarjeta de código individual */
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

    /* Barra de tiempo */
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

    /* Header de la app */
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

    /* Sección de instrucciones */
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

    /* Caja para copiar la línea TOML */
    .toml-box {
        background: #0d1117;
        border: 1px solid #3fb950;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 14px;
        color: #3fb950;
        word-break: break-all;
    }

    /* Botones personalizados */
    .stButton > button {
        border-radius: 8px;
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 500;
        transition: all 0.15s ease;
    }

    /* Separador */
    .sep {
        border: none;
        border-top: 1px solid #21262d;
        margin: 1.5rem 0;
    }

    /* Badge contador */
    .badge-tiempo {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
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

def cargar_llaves() -> dict:
    """
    Lee las llaves desde st.secrets[llaves].
    Retorna un dict {nombre: secreto}.
    Si no existe la sección, retorna vacío.
    """
    try:
        return dict(st.secrets["llaves"])
    except (KeyError, FileNotFoundError):
        return {}

# ──────────────────────────────────────────────
# ESTADO DE SESIÓN
# ──────────────────────────────────────────────

if "pantalla" not in st.session_state:
    st.session_state.pantalla = "codigos"

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

col1, col2 = st.columns(2)
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

st.markdown('<hr class="sep">', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PANTALLA: CÓDIGOS EN VIVO
# ──────────────────────────────────────────────

if st.session_state.pantalla == "codigos":

    llaves = cargar_llaves()

    if not llaves:
        st.markdown("""
        <div class="instruccion-box">
            <p>⚠️ No hay llaves registradas todavía.<br>
            Ve a <strong>Agregar llave</strong> para registrar tu primera clave 2FA.</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        seg = tiempo_restante()
        pct = (seg / 30) * 100

        # Color según urgencia
        if seg > 10:
            color_barra = "#3fb950"
            color_clase = "codigo-numero"
        elif seg > 5:
            color_barra = "#d29922"
            color_clase = "codigo-numero expirando"
        else:
            color_barra = "#f85149"
            color_clase = "codigo-numero critico"

        # Contador global
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

        # Tarjetas de códigos
        for nombre, secreto in llaves.items():
            codigo = generar_codigo(secreto)
            # Formatear código con espacio en el medio: 123 456
            codigo_fmt = f"{codigo[:3]} {codigo[3:]}" if len(codigo) == 6 else codigo

            st.markdown(f"""
            <div class="codigo-card">
                <div>
                    <div class="codigo-nombre">{nombre}</div>
                    <div class="{color_clase}">{codigo_fmt}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Esperar 1 segundo y refrescar (el "tick" del contador)
        time.sleep(1)
        st.rerun()

# ──────────────────────────────────────────────
# PANTALLA: AGREGAR LLAVE
# ──────────────────────────────────────────────

elif st.session_state.pantalla == "agregar":

    st.markdown("""
    <div class="instruccion-box">
        <p>
        Las llaves se guardan en <code>st.secrets</code>, el sistema seguro de Streamlit Cloud.<br><br>
        <strong>Para agregar una nueva llave:</strong><br>
        1. Completa el formulario de abajo para generar la línea de configuración.<br>
        2. Ve al panel de tu app en <code>share.streamlit.io</code>.<br>
        3. Entra a <code>Settings → Secrets</code> y pega la línea generada.<br>
        4. Guarda — la app se reinicia sola y la llave aparece.
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
        type="password"  # oculta mientras escribes
    )

    if nombre and secreto:
        secreto_limpio = secreto.strip().upper().replace(" ", "")
        codigo_prueba  = generar_codigo(secreto_limpio)

        if codigo_prueba == "INVALID":
            st.error("❌ La clave secreta no es un Base32 válido. Verifica que la copiaste correctamente.")
        else:
            st.success(f"✅ Clave válida · Código actual: **{codigo_prueba[:3]} {codigo_prueba[3:]}**")

            nombre_toml = nombre.strip().replace(" ", "_")

            st.markdown("**Copia esta línea y pégala en `Settings → Secrets` de tu app:**")
            st.markdown(f"""
            <div class="toml-box">
                [llaves]<br>
                {nombre_toml} = "{secreto_limpio}"
            </div>
            """, unsafe_allow_html=True)

            st.info("""
💡 Si ya tienes otras llaves en `[llaves]`, **no repitas** la cabecera `[llaves]`.
Solo agrega la nueva línea `nombre = "secreto"` debajo de las existentes.
            """)

            # Mostrar llaves ya existentes para facilitar el copy-paste completo
            llaves_existentes = cargar_llaves()
            if llaves_existentes:
                st.markdown("**Tu sección `[llaves]` completa quedaría así:**")
                lineas = ["[llaves]"]
                for n, s in llaves_existentes.items():
                    lineas.append(f'{n} = "{s}"')
                lineas.append(f'{nombre_toml} = "{secreto_limpio}"')
                st.code("\n".join(lineas), language="toml")
