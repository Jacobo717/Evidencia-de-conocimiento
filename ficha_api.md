# Ficha técnica de API — Práctica 12: Tu API

## Identificación

- **API:** CoinGecko API, plan Demo gratuito.
- **Portal:** [coingecko.com/en/api](https://www.coingecko.com/en/api)
- **Documentación:** [Coins List with Market Data](https://docs.coingecko.com/reference/coins-markets) y [Coin Historical Chart Data by ID](https://docs.coingecko.com/reference/coins-id-market-chart).
- **Tema:** cotizaciones y datos de mercado de criptomonedas.

## Requisitos de la actividad

| Requisito | Evidencia |
|---|---|
| Token o API Key | CoinGecko Demo entrega una API key después de crear una cuenta y generar la clave en Developer Dashboard. |
| Plan gratuito | El plan Demo cuesta $0. |
| JSON | Ambos endpoints seleccionados responden `application/json`. |
| 200 registros tras limpiar | Se solicitan hasta 250 monedas en `/coins/markets`; el programa verifica que queden al menos 200 después de limpiar. La cifra final válida se imprime en la ejecución y se anota en el reporte, pues los datos son dinámicos. También se solicitan hasta 365 días diarios para Bitcoin. |
| Dos columnas numéricas | Precio USD, capitalización USD, volumen 24 h USD, cambio 24 h %, ranking de capitalización; el histórico aporta precio y fecha. |
| Fecha o categoría con 3–12 grupos | `segmento_ranking`, categoría derivada con cinco grupos: 1–10, 11–50, 51–100, 101–150 y 151–250. El histórico también tiene `fecha_utc`. |
| Documentación pública | Referencias oficiales enlazadas arriba. |
| Sin tarjeta ni aprobación manual | La página del plan Demo indica que es gratuito y no requiere tarjeta de crédito. |

La elección cumple además las exclusiones: no usa Banxico, Open-Meteo, scraping ni datos personales.

## Datos y acceso

- **Qué datos proporciona:** cotización actual, capitalización, volumen de negociación, variación del precio y ranking de las monedas. El endpoint histórico aporta pares de fecha Unix y precio para Bitcoin.
- **Cómo obtener el token:** en una cuenta CoinGecko, abrir Developer Dashboard, pestaña API Keys y crear una llave para Demo. El token se coloca localmente en `token.txt` o en la variable `COINGECKO_API_KEY`; esta entrega no contiene una clave real.
- **Autenticación Demo:** encabezado exacto `x-cg-demo-api-key: <TOKEN_PRIVADO>`. Se usa el host `https://api.coingecko.com`.
- **Límite publicado para Demo:** 100 llamadas por minuto y 10,000 llamadas al mes. Esta práctica hace dos llamadas cuando aún no existe caché y después reutiliza los JSON guardados.
- **Endpoint de mercado (sin token):** `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false&price_change_percentage=24h`
- **Endpoint histórico (sin token):** `https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=365`
- La llave viaja en el encabezado, por lo que no se muestra en las URL ni se incorpora a los archivos de caché.

## Estructura JSON

`/coins/markets` devuelve una lista JSON. Cada elemento representa una moneda con campos como `id`, `name`, `symbol`, `current_price`, `market_cap`, `total_volume`, `price_change_percentage_24h` y `market_cap_rank`. La tabla está en la raíz de la respuesta; en Python: `payload` (lista de objetos).

`/coins/bitcoin/market_chart` devuelve un objeto JSON con listas `prices`, `market_caps` y `total_volumes`. Cada elemento de `prices` es `[timestamp_en_milisegundos, precio]`. Se convierte `prices` a una tabla con `fecha_utc` y `precio_usd`.

## Columnas analizadas

| Columna de análisis | Campo de origen | Tipo | Unidad / significado |
|---|---|---|---|
| `id` | `id` | texto | Identificador único de CoinGecko |
| `nombre` | `name` | texto | Nombre de la criptomoneda |
| `simbolo` | `symbol` | texto | Símbolo en mayúsculas |
| `precio_usd` | `current_price` | numérico | USD por unidad de moneda |
| `capitalizacion_usd` | `market_cap` | numérico | USD |
| `volumen_24h_usd` | `total_volume` | numérico | USD negociados en 24 h |
| `cambio_24h_pct` | `price_change_percentage_24h` | numérico | Porcentaje de cambio en 24 h |
| `ranking_capitalizacion` | `market_cap_rank` | entero | Posición por capitalización |
| `segmento_ranking` | derivada del ranking | categórica ordenada | Cinco grupos de posiciones |
| `fecha_utc` | timestamp de `prices` | fecha-hora UTC | Momento de la observación histórica |
| `precio_usd` (histórico) | segundo valor de `prices` | numérico | USD por BTC |

**Cantidad observada en esta ejecución:** 250 registros de mercado recibidos, 247 monedas utilizables después de limpiar y 366 observaciones históricas utilizables de Bitcoin. Se supera el mínimo de 200 en ambas tablas. El programa verifica estos mínimos y vuelve a imprimir los conteos con cada consulta; los valores pueden cambiar porque la API se actualiza.

## Cuatro preguntas de las gráficas

1. **Distribución:** ¿Cómo se distribuye la capitalización de mercado entre las criptomonedas de mayor rango?
2. **Comparación:** ¿Cómo cambia el rendimiento porcentual de 24 horas entre cinco segmentos de capitalización?
3. **Relación:** ¿Qué relación existe entre la capitalización de mercado y el volumen de negociación diario?
4. **Evolución:** ¿Cómo evolucionó el precio de Bitcoin durante los últimos 365 días y qué tendencias suavizadas se observan?

## Tratamiento de datos

El script imprime los tipos de dato iniciales, faltantes por columna, conversiones numéricas fallidas y conteo antes y después de limpiar. Retira monedas con datos analíticos faltantes, valores no finitos, precio o capitalización no positivos, e identificadores duplicados. No se inventan datos faltantes. La serie histórica quita puntos con fecha o precio inválido y duplicados de fecha. Se genera el CSV limpio para inspección.
