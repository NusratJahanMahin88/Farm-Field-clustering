# Streamlit app: exploratory field clusters for Ringkøbing-Skjern (2024)
# Run in the terminal:  streamlit run app.py
# It reads the files made by the last task of the notebook (thesis-fyp.ipynb).

import json
import os
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import streamlit as st

st.set_page_config(page_title="Danish Field Clusters", layout="wide")

FIELDS_FILE = "data/processed/app_fields.parquet"
PROFILES_FILE = "data/processed/cluster_profiles.csv"
SUMMARY_FILE = "results/step5_summary.csv"
SELECTED_FILE = "results/step5_selected.json"

ALGORITHMS = {"kmeans": "K-means", "bisecting_kmeans": "Bisecting K-means"}
COLOUR_MODES = ["Cluster", "Pesticide benchmark", "Moisture stress"]
LABEL_COLOURS = {"low": [69, 117, 180], "medium": [254, 224, 144], "high": [215, 48, 39]}
CLUSTER_COLOURS = [[31, 119, 180], [255, 127, 14], [44, 160, 44], [214, 39, 40], [148, 103, 189], [140, 86, 75]]
CLUSTER_NAMES = ["blue", "orange", "green", "red", "purple", "brown"]
METRICS = {"silhouette": "Silhouette (higher is better)",
           "davies_bouldin": "Davies–Bouldin index (lower is better)",
           "stability_ari": "Stability across seeds, ARI (higher is better)",
           "min_cluster_share": "Smallest cluster share",
           "nmi_crop_group": "NMI with crop group (interpretation only)",
           "cost": "Within-cluster sum of squares"}


# ---------------------------------------------------------------- load the results (only once, then cached)
missing = [f for f in [FIELDS_FILE, PROFILES_FILE, SUMMARY_FILE, SELECTED_FILE] if not os.path.exists(f)]
if missing:
    st.error("These result files are missing: " + ", ".join(missing) +
             ". Copy the results/ and data/processed/ folders from the Kaggle output next to app.py.")
    st.stop()


@st.cache_data
def load_results():
    fields = gpd.read_parquet(FIELDS_FILE)
    profiles = pd.read_csv(PROFILES_FILE, encoding="utf-8-sig")
    summary = pd.read_csv(SUMMARY_FILE)
    with open(SELECTED_FILE) as file:
        chosen = json.load(file)["full"]
    return fields, profiles, summary, chosen


@st.cache_data
def map_geojson(algorithm, colour_by):
    """Field shapes with the colour and tooltip text for one algorithm and colour mode."""
    fields = load_results()[0]
    data = fields[["field_id", "crop_name", "area_ha", "geometry"]].copy()
    data["cluster"] = fields["cluster_" + algorithm].astype(int)
    data["pesticide"] = fields["pesticide_label_" + algorithm]
    data["moisture"] = fields["moisture_stress_label_" + algorithm]
    data["area_ha"] = data["area_ha"].round(1)
    if colour_by == "Cluster":
        data["colour"] = data["cluster"].apply(lambda c: CLUSTER_COLOURS[c % 6] + [170])
    elif colour_by == "Pesticide benchmark":
        data["colour"] = data["pesticide"].apply(lambda label: LABEL_COLOURS[label] + [170])
    else:
        data["colour"] = data["moisture"].apply(lambda label: LABEL_COLOURS[label] + [170])
    return json.loads(data.to_json())


fields, profiles, summary, chosen = load_results()

# ---------------------------------------------------------------- page header
st.title("Exploratory clustering of Danish farm fields")
st.caption("Ringkøbing-Skjern · growing season 2024 · Marker + Sentinel-2 + Miljøstyrelsen pesticide statistics")
st.warning("**Exploratory results only.** The labels come from proxy indicators (satellite NDVI/NDWI and national "
           "crop-group pesticide averages), not from measurements on each field. They are **not** farming advice.")

# ---------------------------------------------------------------- sidebar
st.sidebar.header("Settings")
algorithm = st.sidebar.radio("Clustering algorithm", list(ALGORITHMS.keys()), format_func=lambda a: ALGORITHMS[a])
colour_by = st.sidebar.radio("Colour the fields by", COLOUR_MODES)
st.sidebar.info("k = " + str(chosen[algorithm]["k"]) + " (chosen by the rule: " + chosen[algorithm]["rule"] + ")")

cluster_column = "cluster_" + algorithm
algorithm_profiles = profiles[profiles["algorithm"] == algorithm]

tab_map, tab_profiles, tab_compare, tab_field, tab_about = st.tabs(
    ["Map", "Cluster profiles", "Algorithm comparison", "Field lookup", "About"])

# ---------------------------------------------------------------- tab 1: map
with tab_map:
    col1, col2, col3 = st.columns(3)
    col1.metric("Fields", f"{len(fields):,}")
    col2.metric("Area", f"{fields['area_ha'].sum():,.0f} ha")
    col3.metric("Clusters (k)", fields[cluster_column].nunique())

    layer = pdk.Layer("GeoJsonLayer", map_geojson(algorithm, colour_by),
                      pickable=True, filled=True, get_fill_color="properties.colour")
    view = pdk.ViewState(latitude=56.0, longitude=8.45, zoom=9)
    tooltip = {"html": "<b>{field_id}</b> · {crop_name}<br/>Cluster {cluster} · {area_ha} ha<br/>"
                       "Pesticide benchmark: {pesticide} · Moisture stress: {moisture}"}
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, map_style="light", tooltip=tooltip))

    if colour_by == "Cluster":
        n_clusters = fields[cluster_column].nunique()
        st.caption(" · ".join(f"{CLUSTER_NAMES[c]} = Cluster {c}" for c in range(n_clusters)))
    else:
        st.caption("Blue = low · Yellow = medium · Red = high (relative labels, see the About tab)")
    st.caption("Tip: move the mouse over a field to see its ID. If no tooltip appears near the top of the map, "
               "zoom or drag the map a little, or use the Field lookup tab.")

# ---------------------------------------------------------------- tab 2: cluster profiles
with tab_profiles:
    st.subheader(ALGORITHMS[algorithm] + ": cluster profiles")
    table = algorithm_profiles[["cluster", "n_fields", "area_ha", "pesticide_label", "moisture_stress_label",
                                "vigour_label", "bi_per_ha", "ndvi_peak", "ndwi_at_peak", "top_crop_groups"]].copy()
    table = table.rename(columns={"cluster": "Cluster", "n_fields": "Fields", "area_ha": "Area (ha)",
                                  "pesticide_label": "Pesticide benchmark", "moisture_stress_label": "Moisture stress",
                                  "vigour_label": "Vegetation vigour", "bi_per_ha": "Mean BI/ha",
                                  "ndvi_peak": "Peak NDVI", "ndwi_at_peak": "NDWI at peak",
                                  "top_crop_groups": "Main crop groups"})
    table["Area (ha)"] = table["Area (ha)"].round(0).astype(int)
    table["Main crop groups"] = table["Main crop groups"].str.replace("_", " ")
    st.dataframe(table.round(3), hide_index=True)
    st.caption("Pesticide benchmark: cluster mean BI/ha compared with the national average of 3.99 "
               "(low below half, high above 1.5 times). Moisture stress and vegetation vigour: compared with the "
               "33.3rd and 66.7th percentiles of all 13,510 fields (lower NDWI at peak = higher moisture stress).")

    st.subheader("Average NDVI per month for each cluster")
    month_columns = [c for c in fields.columns if c.startswith("ndvi_2024")]
    monthly = fields.groupby(cluster_column)[month_columns].mean().T
    monthly.index = [c.replace("ndvi_", "").replace("_", "-") for c in month_columns]
    cluster_ids = list(monthly.columns)
    monthly.columns = ["Cluster " + str(c) for c in cluster_ids]
    # same colours as the map (blue = Cluster 0, orange = Cluster 1, ...)
    line_colours = ["#%02x%02x%02x" % tuple(CLUSTER_COLOURS[int(c) % 6]) for c in cluster_ids]
    st.line_chart(monthly, color=line_colours)

# ---------------------------------------------------------------- tab 3: algorithm comparison
with tab_compare:
    metric = st.selectbox("Metric", list(METRICS.keys()), format_func=lambda m: METRICS[m])
    chart = summary.pivot(index="k", columns="algorithm", values=metric).rename(columns=ALGORITHMS)
    st.line_chart(chart)
    st.caption("Values are means across the three random seeds (11, 22 and 33). Selected: K-means k = "
               + str(chosen["kmeans"]["k"]) + ", Bisecting K-means k = " + str(chosen["bisecting_kmeans"]["k"]) + ".")
    shown = summary[["algorithm", "k", "silhouette", "davies_bouldin", "stability_ari", "min_cluster_share",
                     "nmi_crop_group"]].copy()
    shown["algorithm"] = shown["algorithm"].map(ALGORITHMS)
    st.dataframe(shown.round(3), hide_index=True)

# ---------------------------------------------------------------- tab 4: one field
with tab_field:
    field_id = st.text_input("Field ID (for example F000978)").strip().upper()
    if field_id != "":
        one_field = fields[fields["field_id"] == field_id]
        if len(one_field) == 0:
            st.error("Field ID not found. You can find IDs by moving the mouse over the map.")
        else:
            row = one_field.iloc[0]
            st.markdown("### " + field_id + " · " + row["crop_name"])
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Cluster", int(row[cluster_column]))
            col2.metric("Pesticide benchmark", row["pesticide_label_" + algorithm])
            col3.metric("Moisture stress", row["moisture_stress_label_" + algorithm])
            col4.metric("Vegetation vigour", row["vigour_label_" + algorithm])
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Area", f"{row['area_ha']:.1f} ha")
            col2.metric("Crop-group BI/ha", f"{row['bi_per_ha']:.2f}")
            col3.metric("NDWI at peak", f"{row['ndwi_at_peak']:.3f}")
            col4.metric("Peak NDVI", f"{row['ndvi_peak']:.3f}")
            st.caption("Crop group: " + str(row["crop_group"]).replace("_", " ") + ". The labels are those of the "
                       "field's cluster. The BI/ha value is the national average for this crop group, not a "
                       "measurement from this field.")

# ---------------------------------------------------------------- tab 5: about
with tab_about:
    st.markdown("""
**Data:** Marker 2024 fields (Landbrugsstyrelsen) · municipality border DAGI (Klimadatastyrelsen) ·
Sentinel-2 April–September 2024 (NDVI and Gao's NDWI) · pesticide treatment frequency per crop group
(Miljøstyrelsen 2026, Bekæmpelsesmiddelstatistik 2024, Bilag 6).

**Method:** K-means and Bisecting K-means in Spark MLlib, k = 2–6, 3 random seeds, compared with silhouette,
Davies–Bouldin, stability across seeds and cluster sizes. The k was chosen by a fixed rule:
mean ARI ≥ 0.80 and smallest cluster ≥ 2% of fields, then the highest silhouette.

**Labels:** the pesticide benchmark label compares the cluster's mean treatment frequency with the national
average of 3.99 BI/ha (low below half of it, high above 1.5 times it). The low, medium and high moisture-stress
and vegetation-vigour labels are **relative to the 13,510 fields in this study** (33.3rd and 66.7th percentiles);
they are not agronomic thresholds and do not show verified field conditions.

**Limitations:** every field of the same crop group has the same pesticide value, so the label describes the crop
group, not the farmer; moisture is measured as NDWI in each field's greenest month, and NDWI is an indirect
indicator, not a direct measure of water stress; one municipality and one season.
No farmer names or CVR numbers are stored.
""")
