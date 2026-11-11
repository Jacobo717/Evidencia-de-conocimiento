# Reporte de resultados — Práctica 12: Tu API

## Datos y limpieza

Se obtuvieron 247 criptomonedas utilizables de CoinGecko y 366 observaciones históricas diarias de Bitcoin. Se convirtieron a número las cinco variables cuantitativas seleccionadas, se retiraron filas con faltantes en campos analíticos, valores infinitos, precio o capitalización no positivos y duplicados por identificador. El programa imprimió tipos, faltantes y conversiones fallidas para que la limpieza sea auditable. El segmento de ranking es una variable derivada con cinco grupos: 1–10, 11–50, 51–100, 101–150 y 151–250.

## Hallazgos por gráfica

1. **Distribución de capitalización.** La mediana fue $335,601,117.00 USD y el percentil 90 fue $3,827,992,493.20 USD (unas 11.4 veces la mediana). La gran distancia entre ambos valores indica que la distribución está sesgada hacia unas pocas monedas con capitalizaciones muy altas; por eso se usó escala logarítmica.

2. **Comparación por segmento.** La mediana del cambio de 24 h fue mayor en el segmento **51–100** (-0.20 %) y menor en **1–10** (-1.85 %). Las medianas resumen el centro de cada grupo; la altura de las cajas muestra su dispersión. La comparación describe esta consulta puntual y no implica que el rango cause el rendimiento observado.

3. **Relación entre capitalización y volumen.** La correlación de rangos de Spearman fue 0.612. Un valor positivo indica que, en general, monedas con más capitalización también tienden a registrar más volumen; la asociación no implica causalidad. El color agrega el cambio porcentual de 24 horas.

4. **Evolución de Bitcoin.** Entre 2025-11-12 y 2026-11-11, el precio pasó de $103,112.21 a $73,471.28 USD, un cambio de -28.75 %. La media móvil de 30 días suaviza variaciones diarias y ayuda a distinguir tramos de tendencia.

## Preguntas que responden las gráficas

1. ¿Cómo se distribuye la capitalización de mercado entre las 247 criptomonedas utilizables de mayor rango?
2. ¿Cómo cambia el rendimiento porcentual de 24 horas entre cinco segmentos de capitalización?
3. ¿Qué relación existe entre capitalización de mercado y volumen de negociación diario?
4. ¿Cómo evolucionó el precio de Bitcoin durante los últimos 365 días y qué tendencias suavizadas se observan?

## Archivos generados

- `01_distribucion_capitalizacion.png`
- `02_comparacion_cambio_24h.png`
- `03_relacion_capitalizacion_volumen.png`
- `04_evolucion_bitcoin_365d.png`
- `mercados_limpios.csv` y `bitcoin_historico_limpio.csv`
