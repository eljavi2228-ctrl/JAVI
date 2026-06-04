# Manual de Usuario

## Objetivo

Esta aplicacion permite registrar y analizar datos de Control Estadistico de Procesos en frutas y hortalizas. Incluye mediciones continuas, inspecciones por atributos, importacion cruda de archivos tabulares, trazabilidad por lote, analista y fecha, graficos de control, normalidad, capacidad de proceso, Pareto y exportacion a Excel.

## Configuracion Inicial

1. En Supabase, abre el SQL Editor.
2. Ejecuta el contenido de `schema_supabase.sql`.
3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Configura las credenciales. Puedes usar variables de entorno:

```bash
set SUPABASE_URL=https://tu-proyecto.supabase.co
set SUPABASE_KEY=tu_anon_o_service_key
```

Tambien puedes crear `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu_anon_o_service_key"
```

5. Ejecuta:

```bash
streamlit run app.py
```

## Flujo Recomendado

1. En `Catalogos`, registra productos.
2. Registra variables continuas como peso, pH, grados Brix, diametro o firmeza.
3. Registra atributos como golpeado, podrido, mancha, calibre no conforme o defecto critico.
4. En `Registro continuo`, crea subgrupos con trazabilidad y captura mediciones.
5. En `Registro atributos`, registra conformidad o no conformidad por unidad inspeccionada.
6. En `Subir datos`, guarda archivos tabulares reales como importaciones crudas cuando no tengan estructura CEP.
7. En `Graficos de control`, analiza cuando existan al menos 25 subgrupos.
8. En `Inspeccion y muestreo`, estima el tamano de muestra para inspeccion por muestreo.
9. En `Capacidad`, ingresa LIE y LSE para Cp, Cpk, Pp y Ppk, o calcula DPMO/Z para atributos.
10. Usa `Trazabilidad` para filtrar por analista, lote y fecha.
11. Exporta el resumen desde `Exportar`.

## Reglas Implementadas

- Los graficos requieren minimo 25 subgrupos.
- La prueba de normalidad usa Shapiro-Wilk.
- Los graficos X-R y X-S se calculan por variable continua.
- Los graficos p, np, c y u se calculan por atributo.
- Se aplican las 8 pruebas basicas de alarmas en graficos de control.
- Pareto ordena los defectos por frecuencia de no conformidad.
- La capacidad calcula Cp, Cpk, Pp y Ppk con limites de especificacion ingresados por el usuario.
- Para atributos se calcula rendimiento, DPMO y nivel Z.
- El modulo de inspeccion y muestreo estima tamano de muestra con correccion por poblacion finita.
- `Subir datos` guarda importaciones crudas sin inventar producto, variable, subgrupo ni mediciones.

## Interpretacion Basica

- `p < 0.05` en Shapiro-Wilk indica que los datos no siguen normalidad estadistica al 5%.
- Cp y Pp miden capacidad potencial.
- Cpk y Ppk consideran centrado del proceso.
- Valores mayores o iguales a 1.33 suelen considerarse aceptables en muchos contextos industriales, aunque depende del criterio del curso o empresa.
- Puntos fuera de limites en un grafico de control sugieren causas especiales que deben investigarse.
