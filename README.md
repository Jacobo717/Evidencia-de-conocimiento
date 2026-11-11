# Práctica 12 — Tu API

Proyecto de análisis con CoinGecko Demo API. El script solicita 250 monedas de mercado y hasta 365 días de historia de Bitcoin, conserva las respuestas JSON en caché, documenta la limpieza y crea cuatro gráficas, dos archivos CSV y un reporte interpretativo.

## Preparación

1. Instala Python 3.10 o posterior.
2. Crea un entorno virtual e instala las dependencias en la terminal de VS Code:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Pega tu clave Demo en `token.txt` (una sola línea) o define `COINGECKO_API_KEY` en el entorno. No la pegues en `practica12.py`, en el reporte ni en capturas.
4. Ejecuta:

   ```powershell
   .\.venv\Scripts\python.exe practica12.py
   ```

La primera ejecución hace dos solicitudes y guarda las respuestas en `cache/`. Las siguientes reutilizan la caché para evitar llamadas repetidas. Para actualizar los datos, elimina manualmente los dos JSON de `cache/` y vuelve a correr. Si la API no está disponible y no existe caché, el programa explica el error.

## Entregables que genera

La ficha previa está en `ficha_api.md`. El programa crea en `resultados/` las cuatro gráficas PNG, los CSV limpios y `reporte_interpretacion.md`. Las gráficas se guardan con `savefig` antes de cerrar la figura; por eso no dependen de que se abra una ventana interactiva.
