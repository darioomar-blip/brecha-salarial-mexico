# Instrucciones para subir el repo a GitHub

Cowork bloqueó las operaciones sobre `.git/` por seguridad, así que estos pasos los ejecutas tú desde tu Terminal local. Toma 3 minutos.

## 1. Crear el repo vacío en GitHub

Entra a <https://github.com/new> y crea el repo con estos datos:

- **Owner:** `darioomar-blip`
- **Repository name:** `brecha-salarial-mexico`
- **Description:** *Análisis de la brecha salarial de género en México con descomposición Oaxaca-Blinder sobre microdatos ENOE 4T 2025*
- **Visibility:** Public
- **NO marques** "Add a README", "Add .gitignore" ni "Choose a license" — el repo ya los trae.

Click **Create repository**.

## 2. Limpiar el `.git` corrupto e inicializar de cero

Abre Terminal y corre:

```bash
cd "/Users/dario/Downloads/Analisis de datos/brecha-salarial-mexico"

# Borrar el .git/ que dejé a medias
rm -rf .git

# Inicializar de nuevo
git init -b main
git config user.email "darioomar@icloud.com"
git config user.name "Dario"
```

## 3. Tres commits temáticos (refleja la línea de trabajo)

```bash
# Commit 1: estructura inicial + módulo loader + notebook de descarga
git add .gitignore requirements.txt src/__init__.py src/enoe_loader.py \
        notebooks/01_descarga_y_limpieza.ipynb
git commit -m "Estructura inicial del proyecto y módulo ENOE loader

- requirements.txt con pandas, statsmodels, scipy, matplotlib
- src/enoe_loader.py: detección de archivos por patrón,
  construcción de variables Mincer, winsorización ponderada
- Notebook 01: 110,563 registros de la ENOE 4T 2025"

# Commit 2: EDA con el aha moment del cambio de encuadre
git add notebooks/02_eda.ipynb outputs/eda_*.png
git commit -m "EDA — hallazgo del cambio de encuadre

Brecha mensual = 23%, brecha por hora = 1.9%. Las mujeres trabajan
8.4 hrs menos por semana. El proyecto pivota a modelar log(ingreso
mensual) con horas como variable explicativa más.

Las mujeres ocupadas mexicanas tienen MÁS escolaridad (11.0 vs 10.3)
y MÁS subordinación formal (57.8% vs 55.1%) que los hombres."

# Commit 3: modelado (Mincer + Oaxaca-Blinder + Heckman) + entregables
git add notebooks/03_mincer.ipynb notebooks/04_oaxaca_blinder.ipynb \
        notebooks/05_heckman_robustez.ipynb notebooks/06_visualizaciones_finales.ipynb \
        src/oaxaca.py data/processed/ outputs/ \
        README.md post_linkedin.md
git commit -m "Análisis y entregables — Mincer, Oaxaca-Blinder, Heckman

- src/oaxaca.py: descomposición pooled (Neumark) + bootstrap
- Notebook 03: Mincer separado por sexo (WLS HC3)
- Notebook 04: Oaxaca-Blinder con bootstrap (240 réplicas)
  → 49% horas + 50% residual + 0.5% composición (IC: -2%, +3%)
- Notebook 05: Heckman, Mills no significativo (p=0.52), resultado robusto
- Notebook 06: visualizaciones finales unificadas
- README + post LinkedIn listos para publicar"
```

## 4. Conectar con GitHub y subir

```bash
git remote add origin https://github.com/darioomar-blip/brecha-salarial-mexico.git
git push -u origin main
```

Si te pide credenciales, te conviene usar un Personal Access Token (no la contraseña). Para crearlo: <https://github.com/settings/tokens/new>, dale scope `repo`, copialo, y úsalo como contraseña en el prompt.

## 5. Verificar

Abre <https://github.com/darioomar-blip/brecha-salarial-mexico> y deberías ver:

- README renderizado con el banner arriba
- Los seis notebooks bajo `notebooks/`
- Los outputs (PNGs y CSVs) bajo `outputs/`
- Tres commits en el historial

Si algo sale mal, copia el error y me lo pegas — lo desarmamos.

---

## Después del push

Cuando esté en GitHub, agrega al repo (en la página principal, botón **About** arriba a la derecha):

- **Description**: copiar la de arriba
- **Website**: tu LinkedIn o portafolio si tienes
- **Topics**: `data-analysis`, `python`, `enoe`, `mexico`, `oaxaca-blinder`, `gender-pay-gap`, `econometrics`

Esto mejora la indexación cuando un reclutador entra a tu perfil.
