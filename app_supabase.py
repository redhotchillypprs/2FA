"""
Autenticador 2FA — Versión Supabase
Autenticación y almacenamiento persistente con Supabase.
Cada usuario tiene su cuenta y sus llaves guardadas en la nube.
"""

import time
import pyotp
import streamlit as st
from supabase import create_client, Client

# ──────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Autenticador 2FA",
    page_icon="🔐",
    layout="centered",
)

# ──────────────────────────────────────────────
# CLIENTE SUPABASE
# ──────────────────────────────────────────────

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase()

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
    .codigo-numero.expirando { color: #d29922; }
    .codigo-numero.critico   { color: #f85149; }

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

    .auth-card {
        background: #0d1117;
        border: 1px solid #21262d;
        border-radius: 16px;
        padding: 32px 28px;
        margin-top: 1rem;
    }
    .auth-card h2 {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 16px;
        color: #c9d1d9;
        margin: 0 0 20px 0;
        letter-spacing: 1px;
    }

    .user-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #0d2010;
        border: 1px solid #3fb95033;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 12px;
        color: #3fb950;
        font-family: 'IBM Plex Mono', monospace;
        margin-bottom: 1rem;
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
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# FUNCIONES TOTP
# ──────────────────────────────────────────────

def generar_codigo(secreto: str) -> str:
    try:
        totp = pyotp.TOTP(secreto.strip().upper().replace(" ", ""))
        return totp.now()
    except Exception:
        return "INVALID"

def tiempo_restante() -> int:
    return 30 - (int(time.time()) % 30)

# ──────────────────────────────────────────────
# FUNCIONES DE AUTENTICACIÓN
# ──────────────────────────────────────────────

def registrar(email: str, password: str):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        return res, None
    except Exception as e:
        return None, str(e)

def iniciar_sesion(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return res, None
    except Exception as e:
        return None, str(e)

def cerrar_sesion():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.clear()

# ──────────────────────────────────────────────
# FUNCIONES DE BASE DE DATOS
# ──────────────────────────────────────────────

def cargar_llaves(token: str) -> list:
    try:
        supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )
        res = supabase.table("llaves").select("id, nombre, secreto").order("creado_en").execute()
        return res.data or []
    except Exception:
        return []

def guardar_llave(nombre: str, secreto: str) -> bool:
    try:
        supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )
        supabase.table("llaves").insert({
            "user_id": st.session_state.user_id,
            "nombre": nombre,
            "secreto": secreto
        }).execute()
        return True
    except Exception:
        return False

def eliminar_llave(llave_id: str) -> bool:
    try:
        supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )
        supabase.table("llaves").delete().eq("id", llave_id).execute()
        return True
    except Exception:
        return False

# ──────────────────────────────────────────────
# ESTADO DE SESIÓN
# ──────────────────────────────────────────────

if "pantalla" not in st.session_state:
    st.session_state.pantalla = "login"
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

autenticado = st.session_state.access_token is not None

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
# PANTALLAS SIN SESIÓN: LOGIN / REGISTRO
# ──────────────────────────────────────────────

if not autenticado:

    tab_login, tab_registro = st.tabs(["Iniciar sesión", "Crear cuenta"])

    with tab_login:
        st.markdown('<div class="auth-card"><h2>ACCEDER</h2>', unsafe_allow_html=True)
        email_l    = st.text_input("Correo electrónico", key="login_email")
        password_l = st.text_input("Contraseña", type="password", key="login_pass")

        if st.button("Entrar →", type="primary", use_container_width=True, key="btn_login"):
            if not email_l or not password_l:
                st.error("Completa todos los campos.")
            else:
                with st.spinner("Verificando..."):
                    res, err = iniciar_sesion(email_l, password_l)
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.session_state.access_token  = res.session.access_token
                    st.session_state.refresh_token = res.session.refresh_token
                    st.session_state.user_id        = res.user.id
                    st.session_state.user_email     = res.user.email
                    st.session_state.pantalla       = "codigos"
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_registro:
        st.markdown('<div class="auth-card"><h2>CREAR CUENTA</h2>', unsafe_allow_html=True)
        email_r    = st.text_input("Correo electrónico", key="reg_email")
        password_r = st.text_input("Contraseña (mínimo 6 caracteres)", type="password", key="reg_pass")
        password_r2 = st.text_input("Confirmar contraseña", type="password", key="reg_pass2")

        if st.button("Crear cuenta →", type="primary", use_container_width=True, key="btn_registro"):
            if not email_r or not password_r or not password_r2:
                st.error("Completa todos los campos.")
            elif password_r != password_r2:
                st.error("❌ Las contraseñas no coinciden.")
            elif len(password_r) < 6:
                st.error("❌ La contraseña debe tener al menos 6 caracteres.")
            else:
                with st.spinner("Creando cuenta..."):
                    res, err = registrar(email_r, password_r)
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.success("✅ Cuenta creada. Revisa tu correo para confirmar tu cuenta y luego inicia sesión.")
        st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PANTALLAS CON SESIÓN ACTIVA
# ──────────────────────────────────────────────

else:

    # Badge de usuario + botón cerrar sesión
    col_user, col_logout = st.columns([4, 1])
    with col_user:
        st.markdown(f"""
        <div class="user-badge">
            ● {st.session_state.user_email}
        </div>
        """, unsafe_allow_html=True)
    with col_logout:
        if st.button("Salir", type="secondary"):
            cerrar_sesion()
            st.rerun()

    # Navegación
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

    # ── CÓDIGOS EN VIVO ──────────────────────────

    if st.session_state.pantalla == "codigos":

        llaves = cargar_llaves(st.session_state.access_token)

        if not llaves:
            st.markdown("""
            <div class="instruccion-box">
                <p>⚠️ No tienes llaves registradas todavía.<br>
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

            for llave in llaves:
                codigo     = generar_codigo(llave["secreto"])
                codigo_fmt = f"{codigo[:3]} {codigo[3:]}" if len(codigo) == 6 else codigo

                st.markdown(f"""
                <div class="codigo-card">
                    <div>
                        <div class="codigo-nombre">{llave['nombre']}</div>
                        <div class="{color_clase}">{codigo_fmt}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            time.sleep(1)
            st.rerun()

    # ── AGREGAR LLAVE ────────────────────────────

    elif st.session_state.pantalla == "agregar":

        st.markdown("""
        <div class="instruccion-box">
            <p>
            Ingresa el nombre del servicio y la clave secreta Base32.<br><br>
            <strong>¿Dónde encuentro la clave Base32?</strong><br>
            Al activar 2FA en cualquier servicio, aparece un código QR y debajo
            una opción como <code>¿No puedes escanear?</code> o
            <code>Ingresar manualmente</code> — ahí está tu clave Base32.
            </p>
        </div>
        """, unsafe_allow_html=True)

        nombre  = st.text_input("Nombre del servicio", placeholder="Ej: GitHub, Google, Banco...", max_chars=40)
        secreto = st.text_input("Clave secreta (Base32)", placeholder="Ej: JBSWY3DPEHPK3PXP", type="password")

        if nombre and secreto:
            secreto_limpio = secreto.strip().upper().replace(" ", "")
            codigo_prueba  = generar_codigo(secreto_limpio)

            if codigo_prueba == "INVALID":
                st.error("❌ La clave secreta no es un Base32 válido. Verifica que la copiaste correctamente.")
            else:
                st.success(f"✅ Clave válida · Código actual: **{codigo_prueba[:3]} {codigo_prueba[3:]}**")

                if st.button("💾  Guardar en Supabase", type="primary"):
                    with st.spinner("Guardando..."):
                        ok = guardar_llave(nombre.strip(), secreto_limpio)
                    if ok:
                        st.success(f"✅ **{nombre}** guardada correctamente.")
                        st.session_state.pantalla = "codigos"
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar. Intenta de nuevo.")

    # ── GESTIONAR LLAVES ─────────────────────────

    elif st.session_state.pantalla == "gestionar":

        llaves = cargar_llaves(st.session_state.access_token)

        if not llaves:
            st.markdown("""
            <div class="instruccion-box">
                <p>No tienes llaves registradas todavía.<br>
                Ve a <strong>Agregar llave</strong> para registrar tu primera clave 2FA.</p>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
            <div class="instruccion-box">
                <p>Tienes <strong>{len(llaves)}</strong> llave{'s' if len(llaves) != 1 else ''} guardadas en Supabase.</p>
            </div>
            """, unsafe_allow_html=True)

            for llave in llaves:
                col_nombre, col_btn = st.columns([4, 1])
                with col_nombre:
                    st.markdown(f"""
                    <div style="
                        background:#0d1117;
                        border:1px solid #21262d;
                        border-radius:10px;
                        padding:10px 16px;
                        margin-bottom:8px;
                        font-family:'IBM Plex Mono',monospace;
                        font-size:13px;
                        color:#3fb950;
                    ">{llave['nombre']}</div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    if st.button("🗑️", key=f"del_{llave['id']}", help=f"Eliminar {llave['nombre']}"):
                        with st.spinner("Eliminando..."):
                            ok = eliminar_llave(llave["id"])
                        if ok:
                            st.rerun()
                        else:
                            st.error("Error al eliminar.")
