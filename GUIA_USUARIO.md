# Guía de usuario — Generador de gráficas T-MEDNet

> **Para quién es esta guía:** cualquier persona que quiera generar las gráficas y bases de datos de temperatura de las estaciones T-MEDNet, sin necesidad de conocimientos de programación.

---

## ¿Qué hace este sistema?

Con estos scripts de Python puedes generar, para cada estación de la red T-MEDNet:

- 📈 **Ciclo anual de temperatura** — evolución por profundidad vs. climatología histórica
- 🌡️ **Anomalía de temperatura** — diferencia respecto a la media histórica
- 🎨 **Estratificación térmica** — diagrama de contornos profundidad × tiempo (Hovmöller)
- 📊 **Días sobre umbral** — número de días que se supera 23 °C, 24 °C, 25 °C, 26 °C y 27 °C en verano
- 💾 **Base de datos actualizada** — nuevo `Database_T_[site].zip` con todos los datos históricos + los nuevos
- 📋 **Informe estadístico** — `Stat_Report_[site].xlsx` con estadísticas anuales por profundidad

---

## Paso 1 — Instalar Python (solo la primera vez)

### ¿Tienes Python instalado?

Abre una ventana del **Símbolo del sistema** (busca "cmd" en el menú inicio) y escribe:

```
python --version
```

Si ves algo como `Python 3.11.4`, ya lo tienes. Si da error, instálalo:

1. Ve a [python.org/downloads](https://www.python.org/downloads/)
2. Descarga la versión más reciente (3.9 o superior)
3. Ejecuta el instalador → **importante:** marca la casilla "Add Python to PATH" antes de instalar
4. Comprueba que funciona volviendo a ejecutar `python --version`

---

## Paso 2 — Descargar el código (solo la primera vez)

El código está en GitHub. Tienes dos opciones:

**Opción A — Descarga directa (más fácil):**
1. Ve al repositorio en GitHub
2. Haz clic en el botón verde **Code → Download ZIP**
3. Descomprime la carpeta ZIP en algún lugar de tu ordenador (p.ej. `C:\tmednet-app\`)

**Opción B — Con Git (si sabes usarlo):**
```
git clone https://github.com/[usuario]/tmednet-app.git
```

---

## Paso 3 — Instalar las dependencias (solo la primera vez)

Abre el **Símbolo del sistema** en la carpeta donde descomprimiste el código:

1. Navega a la carpeta: `cd C:\tmednet-app` (o donde lo hayas puesto)
2. Ejecuta:

```
pip install -r requirements.txt
```

Espera a que termine (puede tardar 2-5 minutos la primera vez).

---

## Paso 4 — Cuenta de Copernicus Marine (solo la primera vez)

Para descargar las temperaturas superficiales del mar (SST) por satélite, necesitas una cuenta gratuita en Copernicus Marine Service:

1. Regístrate en [marine.copernicus.eu](https://marine.copernicus.eu/) (es gratis)
2. Una vez registrado, ejecuta en el símbolo del sistema:

```
copernicusmarine login
```

3. Introduce tu usuario y contraseña cuando te los pida
4. Las credenciales quedan guardadas en tu ordenador — solo tienes que hacerlo una vez

---

## Paso 5 — Descargar los archivos del servidor T-MEDNet

Los archivos `.hobo` que suben los investigadores de campo, así como las bases de datos y los Excels anteriores, están disponibles en el panel de administración de T-MEDNet:

> **URL:** `https://t-mednet.org/administrator/`  
> Necesitas usuario y contraseña de administrador T-MEDNet para acceder.

### 5.1 — La lista de proyectos

Al entrar verás la lista de todas las estaciones de la red. Fíjate en la columna **Files**:

- 🟢 **Punto verde** — no hay archivos nuevos pendientes de procesar
- 🔴 **Punto rojo** — hay archivos nuevos subidos por el equipo de campo (hay que procesarlos)

Cuando veas un punto rojo en una estación, es la señal de que hay datos nuevos para generar las gráficas.

### 5.2 — Entrar al explorador de archivos

Haz clic en **View files** (en la misma fila de la estación) para ver todos los archivos de esa estación.

Dentro del explorador verás tres tipos de carpetas (`Directory`):

| Directorio | Contenido |
|------------|-----------|
| `uploads` | Archivos `.hobo` subidos por el equipo de campo ← **los que necesitas descargar** |
| `t-outputs` | Base de datos histórica (`Database_T_*.zip`) e informes Excel (`Stat_Report_*.xlsx`) ← **también los necesitas** |
| `public` | Gráficas ya generadas y publicadas (PNGs) |

### 5.3 — Descargar los archivos más recientes

1. **Ordena por fecha** haciendo clic en la cabecera **Date created** — los más recientes aparecerán arriba
2. Descarga **todos los archivos `.hobo`** del directorio `uploads` con fecha posterior a la última vez que generaste las gráficas
3. Descarga también el **`Database_T_*.zip` más reciente** del directorio `t-outputs` (es la base de datos histórica que necesitarás en el Paso 7)
4. Opcionalmente, descarga el **`Stat_Report_*.xlsx` más reciente** como referencia

> **Tip:** si hay varios archivos `.hobo` para la misma estación (una por cada profundidad de sensor), descárgalos todos — cada uno corresponde a un sensor a una profundidad diferente.

---

## Paso 6 — Qué archivos necesitas para cada estación

Para generar las gráficas de una estación necesitas **dos tipos de archivos**:

### A) Los datos HOBO (.txt)

Son los archivos exportados por **HOBOware Pro** de los sensores de temperatura. Cada archivo corresponde a un sensor a una profundidad concreta.

El nombre del archivo sigue el formato:
```
[código_sitio]_[fecha_inicio]-[hora]_[fecha_fin]-[hora]_[profundidad]m.txt

Ejemplo:  6_20251027-10_20260525-10_05.txt
          └─ Medes, sitio 6, de oct 2025 a may 2026, sensor de 5 m
```

#### Cómo exportar los archivos .hobo a .txt con HOBOware Pro

Si recibes los archivos `.hobo` directamente del equipo de campo, tienes que convertirlos a `.txt` antes de poder usarlos. Sigue estos pasos:

**1. Abre HOBOware Pro** y ve al menú:
> **Herramientas → Exportación masiva de datos** *(en inglés: Tools → Bulk Export)*

**2. Añade los archivos .hobo** que quieres exportar (usa "Agregar archivos" o "Agregar carpeta").

**3. Configura las opciones de exportación** — esto es fundamental para que el script los lea correctamente:

| Opción | Valor correcto |
|--------|---------------|
| Formato de salida | **Texto (separado por tabulaciones)** |
| Separador | **Tabulación** (no comas ni punto y coma) |
| Formato de fecha | **MM/dd/yy** (mes/día/año de 2 dígitos) |
| Formato de hora | **HH:mm:ss** (24 horas) |
| Unidades de temperatura | **°C** (Celsius, no Fahrenheit) |
| Incluir cabecera | **Sí** |
| Separador decimal | **Punto** (`.`), no coma |

> ⚠️ **Importante:** si el formato de fecha es incorrecto (por ejemplo `dd/MM/yy` en vez de `MM/dd/yy`) los datos de temperatura aparecerán desplazados en el tiempo. Comprueba siempre este ajuste.

**4. Selecciona la carpeta de salida** — usa la carpeta que corresponde a la estación (ver tabla en el Paso 7).

**5. Haz clic en "Exportar"** — HOBOware creará un archivo `.txt` por cada archivo `.hobo`.

**6. Renombra los archivos exportados** siguiendo el formato estándar T-MEDNet:
```
[código_sitio]_[YYYYMMDD-HH inicio]_[YYYYMMDD-HH fin]_[profundidad con ceros]m.txt

Ejemplo:  6_20251027-10_20260525-10_05.txt
```
El nombre del archivo es importante porque el script extrae de él la profundidad y las fechas del sensor.

### B) La base de datos histórica (.zip)

Es el archivo `Database_T_[codigo]_[sitio]_[fechas].zip` de la campaña anterior. Lo recibirás de tu coordinador de datos o lo tendrás de la última vez que generaste los gráficos.

> **Importante:** si es la primera vez que generas datos para una estación y no tienes el zip histórico, contacta con el equipo T-MEDNet para obtenerlo.

---

## Paso 7 — Dónde poner los archivos

Cada estación tiene su propia carpeta esperada. Crea las carpetas que correspondan dentro de tu carpeta `Descargas` y copia los archivos allí.

> **¿Cómo encontrar tu carpeta Descargas?** Normalmente es `C:\Users\TU_NOMBRE\Downloads\`  
> Para saber tu nombre de usuario de Windows: abre el símbolo del sistema y escribe `echo %USERNAME%`

| Estación | Carpeta para los .txt de HOBO | Nombre del .zip histórico |
|----------|-------------------------------|---------------------------|
| Illes Medes (#6) | `Downloads\Medes\` | `Database_T_06_Medes_*.zip` |
| Cap de Creus Nord (#7) | `Downloads\Cap de creus portalo\` | `Database_T_07_Cap de Creus-N_*.zip` |
| Marseille-Riou (#13) | `Downloads\Marseille\` | `Database_T_13_Marseille-Riou_*.zip` |
| Cap Sicié — Toulon (#38) | `Downloads\Toulon\` | `Database_T_38_Cap Sicié_*.zip` |
| Ullastres (#150) | `Downloads\Ullastres datos\` | `Database_T_150_Ullastres_*.zip` |
| Capo Caccia (#205) | `Downloads\Capo Caccia\` | `Database_T_205_Capo Caccia_*.rar` |
| Capraia (#252) | `Downloads\Capraia\` | *(sin histórico — solo HOBO)* |
| Cap de Creus Sud (#5) | `Downloads\Cap de creus sud\` | `Database_T_5_Cap de Creus-S_*.zip` |

El archivo `.zip` histórico va directamente en `Downloads\`, **no** dentro de la subcarpeta.

**Ejemplo de estructura correcta para Medes:**
```
C:\Users\TU_NOMBRE\
└── Downloads\
    ├── Database_T_06_Medes_200207-202510_2025-11-04.zip   ← zip histórico
    └── Medes\                                              ← carpeta HOBO
        ├── 6_20251027-10_20260525-10_05.txt
        ├── 6_20251027-10_20260525-10_10.txt
        ├── 6_20251027-10_20260525-10_15.txt
        └── ...
```

---

## Paso 8 — Adaptar las rutas del script a tu ordenador

Los scripts tienen las rutas configuradas para el ordenador original. Si tu nombre de usuario de Windows es distinto de `jahan`, tienes que cambiarlas.

### Cómo encontrar las rutas a cambiar

1. Abre el script de la estación que quieres ejecutar (p.ej. `generate_medes_plots.py`) con cualquier editor de texto (el Bloc de notas funciona)
2. Busca la sección de **Configuración** al principio del archivo — verás algo así:

```python
# ── Config ────────────────────────────────────────────────────────────────────
SITE_NAME   = "Medes"
SITE_CODE   = 6
HIST_ZIP    = r"C:\Users\jahan\Downloads\Database_T_06_Medes_200207-202510_2025-11-04.zip"
HOBO_DIR    = r"C:\Users\jahan\Downloads\Medes"
SST_CSV     = r"C:\Users\jahan\Downloads\Medes\medes_sst_copernicus.csv"
OUTPUT_BASE = os.path.join(os.path.expanduser("~"), "Desktop", "temperatures t-mednet", SITE_NAME)
```

3. Cambia `jahan` por **tu nombre de usuario de Windows** en `HIST_ZIP`, `HOBO_DIR` y `SST_CSV`
4. Cambia el nombre del archivo `.zip` en `HIST_ZIP` para que coincida con el archivo que tienes (la fecha puede ser diferente)

**Ejemplo:** si tu usuario de Windows es `maria` y tu zip se llama `Database_T_06_Medes_200207-202601_2026-01-15.zip`:

```python
HIST_ZIP = r"C:\Users\maria\Downloads\Database_T_06_Medes_200207-202601_2026-01-15.zip"
HOBO_DIR = r"C:\Users\maria\Downloads\Medes"
SST_CSV  = r"C:\Users\maria\Downloads\Medes\medes_sst_copernicus.csv"
```

> **Nota:** `OUTPUT_BASE` no hace falta cambiarlo — detecta automáticamente la carpeta de tu escritorio.

---

## Paso 9 — Ejecutar el script

1. Abre el **Símbolo del sistema**
2. Navega a la carpeta del código:
   ```
   cd C:\tmednet-app
   ```
3. Ejecuta el script de la estación que quieras (ejemplos):

| Estación | Comando |
|----------|---------|
| Illes Medes | `python generate_medes_plots.py` |
| Cap de Creus Nord | `python generate_cap_creus_n_plots.py` |
| Marseille-Riou | `python generate_marseille_plots.py` |
| Cap Sicié — Toulon | `python generate_toulon_plots.py` |
| Ullastres | `python generate_ullastres_plots.py` |
| Capo Caccia | `python generate_capo_caccia_plots.py` |
| Capraia | `python generate_capraia_plots.py` |
| Cualquier estación (genérico) | `python generate_tmednet_plots.py` |

Verás mensajes de progreso en la pantalla. El script puede tardar **entre 1 y 5 minutos** dependiendo de la cantidad de datos y de si tiene que descargar SST de Copernicus.

**Primera ejecución:** si es la primera vez para esa estación, el script descargará los datos SST de Copernicus automáticamente (puede tardar unos minutos extra y requiere conexión a internet). Las siguientes ejecuciones serán más rápidas porque los guarda en un archivo CSV local.

---

## Paso 10 — Resultados

Cuando el script termine, encontrarás todos los resultados en tu **Escritorio**, dentro de `temperatures t-mednet\[Nombre de la estación]\`:

```
Desktop\
└── temperatures t-mednet\
    └── Medes\
        ├── 2025\
        │   ├── medes_6_annual_T_cycle_20250101_20251231.png    ← Ciclo anual
        │   ├── medes_6_anomaly_20250101_20251231.png           ← Anomalía
        │   ├── medes_6_stratification_20250101_20251231.png    ← Estratificación
        │   ├── medes_6_thresholds_23C_20250101_20251231.png    ← Días >23°C
        │   ├── medes_6_thresholds_24C_20250101_20251231.png
        │   ├── medes_6_thresholds_25C_20250101_20251231.png
        │   ├── medes_6_thresholds_26C_20250101_20251231.png
        │   └── medes_6_thresholds_27C_20250101_20251231.png
        ├── 2026\
        │   ├── medes_6_annual_T_cycle_20260101_20260525.png
        │   ├── medes_6_anomaly_20260101_20260525.png
        │   └── medes_6_stratification_20260101_20260525.png    ← (sin umbrales: verano incompleto)
        ├── Database_T_6_Medes_200207-202605_2026-06-28.zip     ← Base de datos actualizada
        └── 6_Stat_Report_Medes_200207-202605_2026-06-28.xlsx   ← Informe estadístico
```

> Los gráficos de **umbrales de temperatura** (días sobre 23–27 °C) solo se generan para años donde existen datos completos del período julio–agosto–septiembre. Para el año en curso (que todavía no ha terminado el verano) no se generan.

---

## Paso 11 — Subir los resultados al servidor T-MEDNet

Una vez generadas las gráficas y la base de datos actualizada, hay que subirlas al servidor para que estén disponibles en la web de T-MEDNet.

### 11.1 — Acceder al explorador de archivos

Vuelve al panel de administración de T-MEDNet:

> `https://t-mednet.org/administrator/` → **Projects** → clic en **View files** de la estación correspondiente

### 11.2 — Usar el botón Upload

En la parte superior del explorador de archivos verás el botón **Upload**. Al hacer clic se abre un formulario donde puedes:

1. **Seleccionar el archivo** desde tu ordenador
2. **Escribir el nombre** con el que quedará guardado en el servidor
3. **Elegir la carpeta de destino** (`public` o `t-outputs`)
4. Confirmar la subida

### 11.3 — Qué subir a cada carpeta

#### Carpeta `public` — Gráficas PNG

Sube todas las imágenes `.png` generadas. El nombre que debes usar en el servidor sigue este formato:

```
[código]_[tipo]_[año]_[nombre_sitio]_[fecha_generación].png
```

Los tipos de gráfica son:

| Nº | Tipo de gráfica | Archivo generado por el script |
|----|-----------------|-------------------------------|
| `1` | Ciclo anual de temperatura | `*_annual_T_cycle_*.png` |
| `2` | Anomalía | `*_anomaly_*.png` |
| `3` | Estratificación | `*_stratification_*.png` |
| `3_23` | Umbral 23 °C | `*_thresholds_23C_*.png` |
| `3_24` | Umbral 24 °C | `*_thresholds_24C_*.png` |
| `3_25` | Umbral 25 °C | `*_thresholds_25C_*.png` |
| `3_26` | Umbral 26 °C | `*_thresholds_26C_*.png` |
| `3_27` | Umbral 27 °C | `*_thresholds_27C_*.png` |

**Ejemplo** (Medes, ciclo anual 2025, generado el 28 de junio de 2026):
```
06_1_2025_Medes_2026-06-28.png
```

> **Tip:** consulta los archivos que ya hay en la carpeta `public` de esa estación para ver el formato exacto que se ha usado en subidas anteriores y replicarlo.

#### Carpeta `t-outputs` — Base de datos y Excel

Sube los dos archivos de datos generados:

| Archivo a subir | Nombre en el servidor |
|-----------------|-----------------------|
| `Database_T_[código]_[sitio]_[fechas]_[hoy].zip` | Mantén el mismo nombre del archivo generado |
| `[código]_Stat_Report_[sitio]_[fechas]_[hoy].xlsx` | Mantén el mismo nombre del archivo generado |

Estos archivos reemplazan a los anteriores — son la versión actualizada de la base de datos de la estación.

---

## Errores frecuentes y cómo solucionarlos

### ❌ `FileNotFoundError: ... Database_T_... .zip`

**Causa:** el archivo `.zip` histórico no existe o tiene un nombre diferente al que está en el script.

**Solución:**
1. Abre la carpeta `Downloads` y anota el nombre exacto del zip que tienes
2. Abre el script y cambia la línea `HIST_ZIP = ...` con el nombre correcto

---

### ❌ `FileNotFoundError: ... [HOBO_DIR]`

**Causa:** la carpeta de archivos HOBO no existe o está en otro lugar.

**Solución:**
1. Comprueba que la carpeta existe y que el nombre es exacto (incluidas mayúsculas/minúsculas)
2. Actualiza `HOBO_DIR = ...` en el script

---

### ❌ `No se encontraron archivos .txt en ...`

**Causa:** la carpeta HOBO existe pero está vacía o los archivos no tienen extensión `.txt`.

**Solución:**
- Asegúrate de haber exportado los archivos `.hobo` a `.txt` con HOBOware Pro
- Los archivos deben tener extensión `.txt` (no `.csv` ni otros formatos)

---

### ❌ `copernicusmarine login` da error

**Causa:** credenciales incorrectas o no se ha hecho el login.

**Solución:**
1. Ejecuta `copernicusmarine login` en el símbolo de sistema
2. Introduce el usuario y contraseña de tu cuenta en [marine.copernicus.eu](https://marine.copernicus.eu/)
3. Si no tienes cuenta, regístrate (es gratuito)

---

### ❌ `ModuleNotFoundError: No module named 'pandas'` (u otro módulo)

**Causa:** las dependencias no están instaladas.

**Solución:** ejecuta de nuevo:
```
pip install -r requirements.txt
```

---

### ❌ La gráfica de estratificación no tiene datos de 0 m

**Causa:** el punto de la estación cae sobre tierra en la máscara del producto Copernicus (ocurre en algunas estaciones cercanas a la costa, como Cap Sicié en Toulon).

**Solución:** el script lo gestiona automáticamente — usa el sensor más superficial (normalmente 5 m) como proxy de la temperatura de superficie. No es necesario hacer nada.

---

## Referencia rápida — Scripts y estaciones

| Estación | Código | Script | Carpeta HOBO | Nota |
|----------|--------|--------|--------------|------|
| Cap de Creus Sud | 5 | `generate_tmednet_plots.py` | configurable | script genérico |
| Illes Medes | 6 | `generate_medes_plots.py` | `Downloads\Medes\` | |
| Cap de Creus Nord | 7 | `generate_cap_creus_n_plots.py` | `Downloads\Cap de creus portalo\` | |
| Marseille-Riou | 13 | `generate_marseille_plots.py` | `Downloads\Marseille\` | |
| Cap Sicié — Toulon | 38 | `generate_toulon_plots.py` | `Downloads\Toulon\` | sin SST nativa |
| Ullastres | 150 | `generate_ullastres_plots.py` | `Downloads\Ullastres datos\` | |
| Capo Caccia | 205 | `generate_capo_caccia_plots.py` | `Downloads\Capo Caccia\` | histórico en `.rar` |
| Capraia | 252 | `generate_capraia_plots.py` | `Downloads\Capraia\` | sin histórico |

---

## ¿Qué pasa si tengo una estación nueva que no está en la lista?

Usa el script genérico `generate_tmednet_plots.py`. Abre el archivo con el Bloc de notas y edita la sección de configuración al principio:

```python
SITE_NAME = "Nombre de la estación"   # Nombre que aparecerá en los gráficos
SITE_CODE = 99                         # Código numérico de la estación en T-MEDNet
TXT_DIR   = r"C:\Users\TU_NOMBRE\Downloads\NombreCarpetaHOBO"  # Carpeta con los .txt
```

Guarda el archivo y ejecútalo con `python generate_tmednet_plots.py`.

---

*T-MEDNet Desktop v1.0 — ICM-CSIC, 2026*
