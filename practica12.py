"""Práctica 12 — Tu API: análisis de mercados de criptomonedas con CoinGecko.

El token se lee desde COINGECKO_API_KEY o token.txt. Las respuestas JSON se
guardan en cache/ y las gráficas y el reporte se generan en resultados/.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib

# Genera PNG sin depender de una interfaz gráfica o de Tcl/Tk.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import truststore

# Usa las autoridades certificadoras del sistema operativo (Windows/macOS/Linux)
# y conserva la verificación HTTPS; esto evita depender de un bundle incompleto.
truststore.inject_into_ssl()

import requests


BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "resultados"
TOKEN_FILE = BASE_DIR / "token.txt"
API_ROOT = "https://api.coingecko.com/api/v3"
MIN_REGISTROS = 200
MONEDAS_SOLICITADAS = 250
DIAS_HISTORICOS = 365

# Paleta del curso: azul principal, azul claro y acentos cálidos.
AZUL = "#1C4C9A"
AZUL_CLARO = "#4A9BD8"
TURQUESA = "#27A99A"
NARANJA = "#F2A541"
ROJO = "#D95D5D"
GRIS = "#59636E"
FONDO = "#F5F7FA"

NUMERICAS = [
    "precio_usd",
    "capitalizacion_usd",
    "volumen_24h_usd",
    "cambio_24h_pct",
    "ranking_capitalizacion",
]


def cargar_token() -> str:
    """Lee y valida el token sin imprimirlo ni incluirlo en URLs/logs."""
    token = os.getenv("COINGECKO_API_KEY", "").strip()
    origen = "variable de entorno COINGECKO_API_KEY"
    if not token:
        try:
            # utf-8-sig admite token.txt guardado con BOM por algunos editores Windows.
            token = TOKEN_FILE.read_text(encoding="utf-8-sig").strip()
            origen = "token.txt"
        except FileNotFoundError:
            token = ""
    if not token:
        print(
            "ERROR: No se encontró un token. Colócalo en token.txt o define "
            "la variable de entorno COINGECKO_API_KEY."
        )
        raise SystemExit(1)
    if token.lower() in {"tu_token_aqui", "your_api_key", "your_token_here", "<token>"}:
        print(f"ERROR: El valor de {origen} sigue siendo un texto de ejemplo.")
        raise SystemExit(1)
    if len(token) < 12:
        print(f"ERROR: El valor de {origen} parece incompleto; revisa que hayas pegado la clave completa.")
        raise SystemExit(1)
    print(f"Token leído correctamente desde {origen}; su valor no se mostrará.")
    return token


def mensaje_http(respuesta: requests.Response) -> None:
    """Explica errores comunes sin imprimir la URL ni el token."""
    if respuesta.status_code == 401:
        print("ERROR 401: CoinGecko rechazó el token. Revisa que sea válido y esté activo.")
    elif respuesta.status_code == 400:
        print("ERROR 400: CoinGecko rechazó los parámetros de la petición; revisa endpoint y parámetros.")
    elif respuesta.status_code == 429:
        print("ERROR 429: Se alcanzó el límite de peticiones. Espera y vuelve a ejecutar más tarde.")
    elif respuesta.status_code == 403:
        print("ERROR 403: El token no tiene acceso a este endpoint o la solicitud fue bloqueada.")
    elif respuesta.status_code >= 500:
        print(f"ERROR {respuesta.status_code}: CoinGecko no está disponible temporalmente.")
    else:
        print(f"ERROR HTTP {respuesta.status_code}: no se pudo completar la petición.")


def obtener_json(nombre: str, endpoint: str, token: str, params: dict[str, Any]) -> Any:
    """Usa caché primero; consulta API solo si aún no hay respuesta guardada."""
    CACHE_DIR.mkdir(exist_ok=True)
    ruta_cache = CACHE_DIR / f"{nombre}.json"
    if ruta_cache.exists():
        try:
            payload = json.loads(ruta_cache.read_text(encoding="utf-8"))
            print(f"Caché reutilizada: {ruta_cache.relative_to(BASE_DIR)}")
            return payload
        except (json.JSONDecodeError, OSError) as exc:
            print(f"La caché {ruta_cache.name} no se pudo leer ({exc}); se consultará la API.")

    headers = {"x-cg-demo-api-key": token, "accept": "application/json"}
    try:
        respuesta = requests.get(
            f"{API_ROOT}{endpoint}", headers=headers, params=params, timeout=30
        )
    except requests.RequestException as exc:
        print(f"ERROR de conexión al consultar CoinGecko: {exc}")
        print("No hay una respuesta en caché utilizable para esta consulta.")
        raise SystemExit(1)

    if respuesta.status_code != 200:
        mensaje_http(respuesta)
        raise SystemExit(1)
    content_type = respuesta.headers.get("Content-Type") or ""
    if "json" not in content_type.lower():
        print("ERROR: La respuesta HTTP 200 no tiene tipo JSON. Inicio de la respuesta:")
        print(respuesta.text[:300])
        raise SystemExit(1)
    try:
        payload = respuesta.json()
    except requests.JSONDecodeError:
        print("ERROR: El servidor indicó JSON, pero el contenido no se pudo interpretar.")
        raise SystemExit(1)
    ruta_cache.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"Respuesta guardada en {ruta_cache.relative_to(BASE_DIR)}")
    # Mantiene las peticiones espaciadas, incluso al ampliar el script.
    time.sleep(0.25)
    return payload


def resumir_limpieza(df: pd.DataFrame, nombre: str) -> pd.DataFrame:
    print(f"\nTipos de dato al cargar ({nombre}):")
    print(df.dtypes.to_string())
    print(f"\nFaltantes por columna ({nombre}):")
    print(df.isna().sum().to_string())
    antes = len(df)
    conversiones_perdidas: dict[str, int] = {}
    for columna in NUMERICAS:
        original_no_nulo = df[columna].notna()
        convertido = pd.to_numeric(df[columna], errors="coerce")
        conversiones_perdidas[columna] = int((original_no_nulo & convertido.isna()).sum())
        df[columna] = convertido
    df["nombre"] = df["nombre"].fillna("").astype(str).str.strip()
    df["simbolo"] = df["simbolo"].fillna("").astype(str).str.upper().str.strip()
    print("\nValores no numéricos perdidos durante la conversión:")
    print(pd.Series(conversiones_perdidas).to_string())

    df = df.replace([float("inf"), float("-inf")], pd.NA)
    df = df.dropna(subset=NUMERICAS + ["nombre", "simbolo"])
    df = df[(df["precio_usd"] > 0) & (df["capitalizacion_usd"] > 0)]
    df = df.drop_duplicates(subset="id").copy()
    print(f"Registros recibidos: {antes}; utilizables tras limpiar: {len(df)}.")
    if len(df) < MIN_REGISTROS:
        print(
            f"ERROR: quedaron {len(df)} registros; se requieren al menos "
            f"{MIN_REGISTROS}. Revisa la caché o vuelve a consultar más tarde."
        )
        raise SystemExit(1)
    return df


def cargar_datos(token: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    mercados = obtener_json(
        "coingecko_mercados_250",
        "/coins/markets",
        token,
        {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": MONEDAS_SOLICITADAS,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h",
        },
    )
    if not isinstance(mercados, list) or not mercados:
        print("ERROR: El endpoint de mercados no devolvió una lista JSON con registros.")
        raise SystemExit(1)
    base = pd.DataFrame(mercados).rename(
        columns={
            "current_price": "precio_usd",
            "market_cap": "capitalizacion_usd",
            "total_volume": "volumen_24h_usd",
            "price_change_percentage_24h": "cambio_24h_pct",
            "market_cap_rank": "ranking_capitalizacion",
        }
    )
    requeridas = ["id", "name", "symbol"] + NUMERICAS
    faltan = [col for col in requeridas if col not in base.columns]
    if faltan:
        print(f"ERROR: faltan campos esperados en el JSON de mercados: {faltan}")
        raise SystemExit(1)
    base = base[requeridas].rename(columns={"name": "nombre", "symbol": "simbolo"})
    base = resumir_limpieza(base, "mercados")

    historico = obtener_json(
        "coingecko_bitcoin_365d",
        "/coins/bitcoin/market_chart",
        token,
        {"vs_currency": "usd", "days": DIAS_HISTORICOS},
    )
    if not isinstance(historico, dict) or not isinstance(historico.get("prices"), list):
        print("ERROR: el JSON histórico no contiene la lista 'prices' esperada.")
        raise SystemExit(1)
    historial = pd.DataFrame(historico["prices"], columns=["timestamp_ms", "precio_usd"])
    cantidad_original = len(historial)
    historial["fecha_utc"] = pd.to_datetime(historial["timestamp_ms"], unit="ms", utc=True)
    historial["precio_usd"] = pd.to_numeric(historial["precio_usd"], errors="coerce")
    perdidos = int(historial["precio_usd"].isna().sum())
    print("\nTipos de dato al cargar (histórico Bitcoin):")
    print(historial.dtypes.to_string())
    print("\nFaltantes por columna (histórico Bitcoin):")
    print(historial.isna().sum().to_string())
    print(f"Valores de precio no numéricos perdidos: {perdidos}.")
    historial = historial.dropna(subset=["fecha_utc", "precio_usd"]).drop_duplicates("fecha_utc")
    print(f"Puntos históricos recibidos: {cantidad_original}; utilizables: {len(historial)}.")
    if len(historial) < 200:
        print("ERROR: el histórico de Bitcoin tiene menos de 200 puntos utilizables.")
        raise SystemExit(1)
    return base, historial.sort_values("fecha_utc")


def asignar_segmento(df: pd.DataFrame) -> pd.DataFrame:
    """Construye cinco categorías ordenadas a partir del ranking de mercado."""
    cortes = [0, 10, 50, 100, 150, 250]
    etiquetas = ["1–10", "11–50", "51–100", "101–150", "151–250"]
    df = df.copy()
    df["segmento_ranking"] = pd.cut(
        df["ranking_capitalizacion"], bins=cortes, labels=etiquetas, include_lowest=True
    )
    return df.dropna(subset=["segmento_ranking"])


def preparar_estilo() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": FONDO,
            "axes.facecolor": "white",
            "axes.edgecolor": "#D8DEE8",
            "axes.labelcolor": GRIS,
            "text.color": "#223044",
            "xtick.color": GRIS,
            "ytick.color": GRIS,
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "grid.color": "#E7EBF1",
            "grid.linewidth": 0.8,
        }
    )


def guardar_graficas(df: pd.DataFrame, historial: pd.DataFrame) -> dict[str, Any]:
    OUTPUT_DIR.mkdir(exist_ok=True)
    preparar_estilo()
    resumen: dict[str, Any] = {}

    # 1. Distribución: escala logarítmica para hacer visibles las diferencias.
    fig, ax = plt.subplots(figsize=(9, 5.4))
    ax.hist(df["capitalizacion_usd"], bins=30, color=AZUL, edgecolor="white", log=True)
    ax.set_xscale("log")
    ax.set_title("La capitalización se concentra en pocas criptomonedas")
    ax.set_xlabel("Capitalización de mercado (USD, escala logarítmica)")
    ax.set_ylabel("Número de criptomonedas (escala logarítmica)")
    ax.grid(axis="y", alpha=0.8)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "01_distribucion_capitalizacion.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    mediana = df["capitalizacion_usd"].median()
    p90 = df["capitalizacion_usd"].quantile(0.9)
    resumen["distribucion"] = {"mediana": mediana, "p90": p90}

    # 2. Comparación: retorno porcentual por segmento de ranking.
    fig, ax = plt.subplots(figsize=(9, 5.4))
    grupos = [
        df.loc[df["segmento_ranking"] == segmento, "cambio_24h_pct"].dropna()
        for segmento in df["segmento_ranking"].cat.categories
    ]
    nombres = [str(s) for s in df["segmento_ranking"].cat.categories]
    box = ax.boxplot(grupos, patch_artist=True, showfliers=False)
    ax.set_xticks(range(1, len(nombres) + 1), labels=nombres)
    for parche, color in zip(box["boxes"], [AZUL, AZUL_CLARO, TURQUESA, NARANJA, ROJO]):
        parche.set_facecolor(color)
        parche.set_alpha(0.85)
        parche.set_edgecolor("white")
    ax.axhline(0, color=GRIS, linewidth=1, linestyle="--")
    ax.set_title("El cambio diario varía entre grupos de capitalización")
    ax.set_xlabel("Rango de capitalización (posición)")
    ax.set_ylabel("Cambio del precio en 24 horas (%)")
    ax.grid(axis="y", alpha=0.8)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "02_comparacion_cambio_24h.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    medianas = df.groupby("segmento_ranking", observed=False)["cambio_24h_pct"].median().dropna()
    resumen["comparacion"] = {"medianas": medianas.to_dict()}

    # 3. Relación: puntos con mayor volumen y capitalización.
    fig, ax = plt.subplots(figsize=(9, 5.4))
    puntos = ax.scatter(
        df["capitalizacion_usd"], df["volumen_24h_usd"], c=df["cambio_24h_pct"],
        cmap="RdYlBu_r", alpha=0.78, s=35, edgecolors="white", linewidths=0.35,
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title("Mayor capitalización suele acompañarse de más volumen")
    ax.set_xlabel("Capitalización de mercado (USD, escala logarítmica)")
    ax.set_ylabel("Volumen de negociación en 24 h (USD, escala logarítmica)")
    cb = fig.colorbar(puntos, ax=ax)
    cb.set_label("Cambio del precio en 24 h (%)")
    ax.grid(alpha=0.65)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "03_relacion_capitalizacion_volumen.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    correlacion = df[["capitalizacion_usd", "volumen_24h_usd"]].corr(method="spearman").iloc[0, 1]
    resumen["relacion"] = {"correlacion_spearman": correlacion}

    # 4. Evolución temporal: serie diaria reciente de Bitcoin.
    hist = historial.copy()
    hist["media_movil_30d"] = hist["precio_usd"].rolling(30, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.plot(hist["fecha_utc"], hist["precio_usd"], color=AZUL_CLARO, alpha=0.45, linewidth=1.1, label="Precio diario")
    ax.plot(hist["fecha_utc"], hist["media_movil_30d"], color=AZUL, linewidth=2.4, label="Media móvil de 30 días")
    ax.set_title("Bitcoin muestra una trayectoria anual con cambios de tendencia")
    ax.set_xlabel("Fecha (UTC)")
    ax.set_ylabel("Precio de Bitcoin (USD)")
    ax.legend(frameon=False)
    ax.grid(alpha=0.75)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "04_evolucion_bitcoin_365d.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    inicio, fin = hist["precio_usd"].iloc[0], hist["precio_usd"].iloc[-1]
    resumen["evolucion"] = {
        "fecha_inicio": hist["fecha_utc"].iloc[0], "fecha_fin": hist["fecha_utc"].iloc[-1],
        "precio_inicio": inicio, "precio_fin": fin,
        "cambio_pct": (fin / inicio - 1) * 100 if inicio else float("nan"),
    }
    return resumen


def escribir_reporte(df: pd.DataFrame, historial: pd.DataFrame, resumen: dict[str, Any]) -> None:
    df.to_csv(OUTPUT_DIR / "mercados_limpios.csv", index=False, encoding="utf-8-sig")
    historial.to_csv(OUTPUT_DIR / "bitcoin_historico_limpio.csv", index=False, encoding="utf-8-sig")
    mediana = resumen["distribucion"]["mediana"]
    p90 = resumen["distribucion"]["p90"]
    ratio = p90 / mediana if mediana else float("nan")
    corr = resumen["relacion"]["correlacion_spearman"]
    evolucion = resumen["evolucion"]
    segmento_med = resumen["comparacion"]["medianas"]
    if segmento_med:
        mejor = max(segmento_med, key=segmento_med.get)
        peor = min(segmento_med, key=segmento_med.get)
        comparacion_txt = (
            f"La mediana del cambio de 24 h fue mayor en el segmento **{mejor}** "
            f"({segmento_med[mejor]:.2f} %) y menor en **{peor}** ({segmento_med[peor]:.2f} %). "
            "Las medianas resumen el centro de cada grupo; la altura de las cajas muestra su dispersión."
        )
    else:
        comparacion_txt = "No hubo suficientes datos de cambio porcentual para comparar segmentos."
    reporte = f"""# Reporte de resultados — Práctica 12: Tu API

## Datos y limpieza

Se obtuvieron {len(df)} criptomonedas utilizables de CoinGecko y {len(historial)} observaciones históricas diarias de Bitcoin. Se convirtieron a número las cinco variables cuantitativas seleccionadas, se retiraron filas con faltantes en campos analíticos, valores infinitos, precio o capitalización no positivos y duplicados por identificador. El programa imprimió tipos, faltantes y conversiones fallidas para que la limpieza sea auditable. El segmento de ranking es una variable derivada con cinco grupos: 1–10, 11–50, 51–100, 101–150 y 151–250.

## Hallazgos por gráfica

1. **Distribución de capitalización.** La mediana fue ${mediana:,.2f} USD y el percentil 90 fue ${p90:,.2f} USD (unas {ratio:,.1f} veces la mediana). La gran distancia entre ambos valores indica que la distribución está sesgada hacia unas pocas monedas con capitalizaciones muy altas; por eso se usó escala logarítmica.

2. **Comparación por segmento.** {comparacion_txt} La comparación describe esta consulta puntual y no implica que el rango cause el rendimiento observado.

3. **Relación entre capitalización y volumen.** La correlación de rangos de Spearman fue {corr:.3f}. Un valor positivo indica que, en general, monedas con más capitalización también tienden a registrar más volumen; la asociación no implica causalidad. El color agrega el cambio porcentual de 24 horas.

4. **Evolución de Bitcoin.** Entre {evolucion['fecha_inicio']:%Y-%m-%d} y {evolucion['fecha_fin']:%Y-%m-%d}, el precio pasó de ${evolucion['precio_inicio']:,.2f} a ${evolucion['precio_fin']:,.2f} USD, un cambio de {evolucion['cambio_pct']:.2f} %. La media móvil de 30 días suaviza variaciones diarias y ayuda a distinguir tramos de tendencia.

## Preguntas que responden las gráficas

1. ¿Cómo se distribuye la capitalización de mercado entre las {len(df)} criptomonedas utilizables de mayor rango?
2. ¿Cómo cambia el rendimiento porcentual de 24 horas entre cinco segmentos de capitalización?
3. ¿Qué relación existe entre capitalización de mercado y volumen de negociación diario?
4. ¿Cómo evolucionó el precio de Bitcoin durante los últimos 365 días y qué tendencias suavizadas se observan?

## Archivos generados

- `01_distribucion_capitalizacion.png`
- `02_comparacion_cambio_24h.png`
- `03_relacion_capitalizacion_volumen.png`
- `04_evolucion_bitcoin_365d.png`
- `mercados_limpios.csv` y `bitcoin_historico_limpio.csv`
"""
    (OUTPUT_DIR / "reporte_interpretacion.md").write_text(reporte, encoding="utf-8")
    print(f"\nGráficas, CSV y reporte guardados en: {OUTPUT_DIR}")


def main() -> None:
    print("Práctica 12 — Tu API | CoinGecko Demo API")
    token = cargar_token()
    mercados, historial = cargar_datos(token)
    mercados = asignar_segmento(mercados)
    resumen = guardar_graficas(mercados, historial)
    escribir_reporte(mercados, historial, resumen)
    print(f"Listo: {len(mercados)} criptomonedas limpias y {len(historial)} días de Bitcoin.")
    print("No se imprimió ni se guardó el token en los archivos de resultados.")


if __name__ == "__main__":
    main()
