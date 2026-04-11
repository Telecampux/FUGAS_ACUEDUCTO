def inyectar_pwa():
    """Lee el manifest.json manejando de forma segura la codificación de caracteres."""
    manifest_path = Path("static/manifest.json")
    if manifest_path.exists():
        # 1. Intentar decodificación estándar web (Linux/Mac)
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_json = json.load(f)
        # 2. Mecanismo de contingencia para archivos generados en Windows
        except UnicodeDecodeError:
            with open(manifest_path, "r", encoding="latin-1") as f:
                manifest_json = json.load(f)
        except json.JSONDecodeError:
            st.error("Error: El archivo manifest.json tiene un formato inválido.")
            return

        # Inyección de metadatos en el DOM
        st.markdown(
            f"""
            <link rel="manifest" href="data:application/json;base64,{json.dumps(manifest_json).encode().hex()}">
            <meta name="theme-color" content="{manifest_json.get('theme_color', '#000000')}">
            """,
            unsafe_allow_html=True
        )
