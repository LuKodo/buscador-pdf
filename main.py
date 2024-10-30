import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from datetime import datetime
import io
import base64


def buscar_en_pdf(pdf_file, palabras):
    """
    Busca múltiples palabras en un archivo PDF

    Args:
        pdf_file: Archivo PDF cargado
        palabras (List[str]): Lista de palabras a buscar

    Returns:
        Dict: Diccionario con resultados por palabra
    """
    reader = PdfReader(pdf_file)
    resultados = {palabra: {} for palabra in palabras}

    # Iterar sobre todas las páginas
    for num_pagina in range(len(reader.pages)):
        # Obtener el texto de la página
        pagina = reader.pages[num_pagina]
        texto = pagina.extract_text().lower()
        palabras_pagina = texto.split()

        # Buscar cada palabra
        for palabra in palabras:
            palabra_lower = palabra.lower()
            if palabra_lower in texto:
                # Encontrar todas las ocurrencias
                for i, palabra_texto in enumerate(palabras_pagina):
                    if palabra_lower in palabra_texto.lower():
                        # Obtener contexto
                        inicio = max(0, i - 5)
                        fin = min(len(palabras_pagina), i + 6)
                        contexto = ' '.join(palabras_pagina[inicio:fin])

                        # Guardar resultado
                        if num_pagina + 1 not in resultados[palabra]:
                            resultados[palabra][num_pagina + 1] = []
                        resultados[palabra][num_pagina + 1].append(contexto)

    return resultados


def crear_dataframe_resultados(resultados, nombre_pdf):
    """Convierte los resultados en un DataFrame de pandas"""
    datos = []
    fecha_busqueda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for palabra, ocurrencias in resultados.items():
        encontrada = bool(ocurrencias)
        paginas = []
        total_ocurrencias = 0
        contextos = []

        if encontrada:
            paginas = list(ocurrencias.keys())
            total_ocurrencias = sum(len(contextos) for contextos in ocurrencias.values())
            # Tomar solo los primeros 3 contextos para no sobrecargar el DataFrame
            for pagina_contextos in ocurrencias.values():
                contextos.extend(pagina_contextos[:3])

        datos.append({
            'Palabra': palabra,
            'Encontrada': 'Sí' if encontrada else 'No',
            'PDF': nombre_pdf,
            'Fecha_Búsqueda': fecha_busqueda,
            'Páginas_Encontrada': ','.join(map(str, paginas)) if paginas else 'N/A',
            'Total_Ocurrencias': total_ocurrencias,
            'Ejemplos_Contexto': ' | '.join(contextos[:3]) if contextos else 'N/A'
        })

    return pd.DataFrame(datos)


def get_download_link(df):
    """Genera un link de descarga para el DataFrame"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="resultados_busqueda.csv">Descargar resultados como CSV</a>'
    return href


def main():
    st.title('Buscador de Palabras en PDF')

    # Sidebar para cargar archivos
    with st.sidebar:
        st.header('Cargar Archivos')
        pdf_file = st.file_uploader("Selecciona el archivo PDF", type=['pdf'])
        palabras_file = st.file_uploader("Selecciona el archivo de palabras (una por línea)", type=['txt'])

        # Opción para introducir palabras manualmente
        st.header('O introduce palabras manualmente')
        palabras_manual = st.text_area("Introduce palabras (una por línea)")

    if pdf_file is not None:
        # Obtener palabras ya sea del archivo o del texto manual
        palabras = []
        if palabras_file is not None:
            palabras = [linea.decode('utf-8').strip() for linea in palabras_file if linea.decode('utf-8').strip()]
        elif palabras_manual:
            palabras = [linea.strip() for linea in palabras_manual.split('\n') if linea.strip()]

        if palabras:
            if st.button('Buscar Palabras'):
                with st.spinner('Buscando palabras en el PDF...'):
                    # Realizar búsqueda
                    resultados = buscar_en_pdf(pdf_file, palabras)

                    # Crear DataFrame con resultados
                    df_resultados = crear_dataframe_resultados(resultados, pdf_file.name)

                    # Mostrar resumen
                    total_palabras = len(palabras)
                    palabras_encontradas = df_resultados[df_resultados['Encontrada'] == 'Sí'].shape[0]

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Palabras", total_palabras)
                    with col2:
                        st.metric("Encontradas", palabras_encontradas)
                    with col3:
                        st.metric("No Encontradas", total_palabras - palabras_encontradas)

                    # Mostrar resultados
                    st.subheader('Resultados de la búsqueda')
                    st.dataframe(df_resultados)

                    # Botón de descarga
                    st.markdown(get_download_link(df_resultados), unsafe_allow_html=True)
        else:
            st.warning('Por favor, carga un archivo de palabras o introduce palabras manualmente.')
    else:
        st.info('Por favor, carga un archivo PDF para comenzar.')


if __name__ == '__main__':
    main()