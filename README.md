# Exploratory Clustering of Danish Farm Fields

Final-year project (Computer Science BSc, De Montfort University) – Nusrat Jahan Mahin.

K-means and Bisecting K-means (Spark MLlib) on 13,510 farm fields in Ringkøbing-Skjern, Denmark,
growing season 2024, using Sentinel-2 NDVI/NDWI and national crop-group pesticide benchmarks.
The results are shown in a Streamlit app.

## Folder contents
```
app.py                     Streamlit app (map, cluster profiles, algorithm comparison, field lookup, about)
thesis-fyp.ipynb           complete pipeline, final Kaggle run (all cells with their outputs)
requirements.txt           Python libraries
data/processed/            files the app reads (made by the notebook)
    app_fields.parquet       13,510 fields with features, clusters and labels
    cluster_profiles.csv     one row per cluster and algorithm
data/raw/                  small input files used by the notebook
    crop_mapping.csv         119 Marker crop codes -> crop groups (made in this project)
    pesticide_benchmarks.csv BI/ha and B/ha per crop group (Miljøstyrelsen 2026, Bilag 6)
    s2_features_FINAL.csv    satellite indicators per field (extracted once from Google Earth Engine)
results/                   evaluation tables made by the notebook
    step5_summary.csv        mean scores per algorithm and k (Table 5.1 in the thesis)
    step5_selected.json      selected k: K-means 4, Bisecting K-means 2
    all_runs.csv             all 30 runs (2 algorithms x k = 2-6 x seeds 11, 22, 33)
    cleaning_log.csv         fields remaining after each cleaning step
    outliers.csv             IQR outliers per feature
    bare_soil_check.csv      driest month per crop group (why NDWI at peak was used)
    figures/                 figures used in the thesis (see the table below)
```

| File in results/figures | Thesis figure |
|---|---|
| fig1_top_crops.png | Figure 4.1 |
| fig2_monthly_ndvi.png | Figure 4.2 |
| fig3_monthly_ndwi.png | Figure 4.3 |
| fig4_boxplots.png | Figure 4.4 |
| fig5_correlation.png | Figure 4.5 |
| fig6_algorithm_comparison.png | Figure 5.1 |
| fig7_cluster_ndvi.png | Figure 5.2 |

## 1. Run the Streamlit app (about 2 minutes)
Needs Python 3.10 or newer.
1. Open this folder in VS Code (File → Open Folder → My_FYP_Code_Final).
2. Open a terminal (Terminal → New Terminal). It must be in this folder, because the app reads
   `data/processed/` and `results/` from here.
3. Install the libraries the app needs (only the first time):
   ```
   python -m pip install streamlit pydeck geopandas pandas pyarrow
   ```
4. Start the app:
   ```
   python -m streamlit run app.py
   ```
5. The app opens in the browser at http://localhost:8501. Stop it with Ctrl + C in the terminal.

What you should see:
- 13,510 fields, 83,212 ha
- K-means k = 4 and Bisecting K-means k = 2 (rule: mean ARI ≥ 0.80 and smallest cluster ≥ 2%, then highest silhouette)
- Field lookup: try F000978 (a valid field) or F000000 (shows "not found")

Known limitation: the map tooltip is sometimes shown slightly above the mouse, so fields at the top of the map
may show no tooltip. Zoom or drag the map a little, or use the Field lookup tab.

## 2. Re-run the notebook (optional, Kaggle)
The notebook was run on Kaggle (Spark 3.5.3, Python 3.13.15, pandas 2.3.3, GeoPandas 1.1.4).
All outputs are already saved inside `thesis-fyp.ipynb`, so it can be read without running it.

To run it again:
1. Upload `thesis-fyp.ipynb` to Kaggle and turn **Internet on** (needed for the install cell).
2. Add the input files as Kaggle datasets: the three files in `data/raw/` plus the two large public files
   below (not included because of their size).
3. Update the file paths to your own Kaggle datasets in two places:
   - **Task 0.1 (cell 3): Settings** – `INPUT`, `MARKER_FILE`, `BOUNDARY_FILE`, `CROP_MAPPING_FILE`, `PESTICIDE_FILE`
     (the cell prints `True` four times when all paths are correct)
   - **Task 2.1 (cell 13)** – `SAVED_SATELLITE_FILE` (the path to `s2_features_FINAL.csv`)
4. Click Run All. If the satellite file is found, the notebook prints "Satellite file already exists -
   download is skipped", so no Google Earth Engine login is needed. Without that file, the notebook asks for
   a Google Earth Engine login and the download takes about 15 minutes.
5. The results are written to `results/` and `data/processed/` and packed into a zip in the last cell.

| Large input file | Source |
|---|---|
| Marker_2024 shapefile (field boundaries and crop codes) | Landbrugsstyrelsen, https://landbrugsgeodata.fvm.dk |
| Kommuneinddeling_DAGI.geojson (municipality boundary) | Klimadatastyrelsen, https://dataforsyningen.dk/data/3901 |

To install every library from `requirements.txt` instead (including PySpark for the notebook):
`python -m pip install -r requirements.txt`

## Important
The labels are exploratory. Pesticide values are national crop-group averages, not measurements on each
field, and NDWI is an indirect moisture indicator. Moisture-stress and vigour labels are relative to the
13,510 fields in this study. No farmer names or CVR numbers are stored.
