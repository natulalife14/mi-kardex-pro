import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Kardex Cloud Pro", layout="wide")

# --- 2. DISEÑO LILA Y NEGRO (TU ESTILO) ---
st.markdown("""
    <style>
    .main { background-color: #f7f5ff; }
    .header-box { 
        background-color: #e6deff; padding: 25px; border-radius: 20px; 
        text-align: center; border: 1px solid #dcd0ff; margin-bottom: 25px;
    }
    h1, h3 { color: #000000 !important; font-weight: 800 !important; }
    label { color: #000000 !important; font-weight: bold !important; font-size: 14px; }
    .stButton>button { 
        background-color: #835af1 !important; color: white !important; 
        border-radius: 50px; width: 100%; height: 50px; font-weight: bold;
    }
    .stDataFrame, .stTable { background-color: white; border-radius: 15px; border: 1px solid #f0eaff; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='header-box'><h1>🚀 Kardex Dinámico Cloud v2.0</h1><p style='color:black;'>Sincronizado con Google Sheets</p></div>", unsafe_allow_html=True)

# --- 3. CONEXIÓN A GOOGLE SHEETS ---
# Esta parte conecta la App con tu archivo de Excel en la nube
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Leer datos existentes (ttl=0 asegura que siempre traiga lo último)
    df_existente = conn.read(ttl=0)
except:
    # Si la hoja está vacía, crear estructura básica
    df_existente = pd.DataFrame(columns=["Fecha", "Producto", "Categoría", "Código", "Lote", "Tipo", "Cant", "Unidad", "Neto"])

# --- 4. FORMULARIO DE REGISTRO (ALINEADO) ---
with st.container():
    st.subheader("📝 Registro de Movimientos")
    col1, col2 = st.columns(2)
    
    with col1:
        prod = st.text_input("Producto:", placeholder="Nombre del artículo")
        cat = st.selectbox("Categoría:", ['Materia Prima Fresca', 'Materia Prima Seca', 'Envase', 'Empaque', 'Producto Terminado'])
        uni = st.selectbox("Unidad Medida:", ['Kg', 'Millares', 'Unidad', 'Litros'])
        cant = st.number_input("Cantidad:", min_value=0.0, step=0.1)
        
    with col2:
        lot = st.text_input("Lote:", placeholder="N° de Lote")
        cod = st.text_input("Código:", placeholder="Código manual")
        tipo = st.selectbox("Operación:", ["Entrada (+)", "Salida (-)"])

    if st.button("REGISTRAR EN LA NUBE"):
        if prod and cant > 0:
            val_neto = cant if "Entrada" in tipo else -cant
            nuevo_mov = pd.DataFrame([{
                "Fecha": (datetime.utcnow() - timedelta(hours=5)).strftime("%d/%m/%Y %H:%M"),
                "Producto": prod.capitalize(),
                "Categoría": cat,
                "Código": cod.upper(),
                "Lote": lot.upper(),
                "Tipo": "ENTRADA" if val_neto > 0 else "SALIDA",
                "Cant": cant,
                "Unidad": uni,
                "Neto": val_neto
            }])
            
            # Unir con datos viejos y subir a Google
            df_actualizado = pd.concat([df_existente, nuevo_mov], ignore_index=True)
            conn.update(data=df_actualizado)
            st.success("✅ Guardado exitosamente en Google Sheets")
            st.rerun()
        else:
            st.error("Atencion: Por favor, rellene Producto y Cantidad.")

st.divider()

# --- 5. RESUMEN DE STOCK GENERAL ---
st.subheader("📦 Resumen de Stock General")
cat_filtro = st.selectbox("Filtrar Stock por Categoría:", ["Todas", 'Materia Prima Fresca', 'Materia Prima Seca', 'Envase', 'Empaque', 'Producto Terminado'])

if not df_existente.empty:
    resumen = df_existente.copy()
    if cat_filtro != "Todas":
        resumen = resumen[resumen['Categoría'] == cat_filtro]
    
    if not resumen.empty:
        # Agrupación inteligente para mostrar Entradas, Salidas y Total
        stk_table = resumen.groupby(['Producto', 'Código', 'Unidad']).agg(
            Entradas=('Neto', lambda x: x[x > 0].sum()),
            Salidas=('Neto', lambda x: abs(x[x < 0].sum())),
            Stock_Total=('Neto', 'sum')
        ).reset_index()
        st.table(stk_table)
    else:
        st.info("No hay datos registrados en esta categoría.")

st.divider()

# --- 6. HISTORIAL DETALLADO ---
st.subheader("📋 Historial Detallado")
busqueda = st.text_input("🔍 Buscar por Nombre, Código o Lote:")

if not df_existente.empty:
    df_hist = df_existente.copy()
    if busqueda:
        # Filtro de búsqueda universal
        mask = df_hist.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)
        df_hist = df_hist[mask]
    

    st.dataframe(df_hist[['Fecha', 'Producto', 'Código', 'Lote', 'Tipo', 'Cant', 'Unidad']], use_container_width=True)
