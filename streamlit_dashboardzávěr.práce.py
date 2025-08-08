
import pandas as pd
import plotly.express as px
import streamlit as st

# Load and prepare data directly within the script
soubor = 'Absolventi_vysokých_škol_8931697613286264347závěr.práce.csv'
try:
    df = pd.read_csv(soubor)
except FileNotFoundError:
    st.error(f"Soubor '{soubor}' nebyl nalezen. Ujistěte se, že je soubor nahrán do stejného adresáře jako skript.")
    st.stop()


df_maly = df[[
    'Název vysoké školy',
    'Název fakulty nebo pracoviště',
    'Název studijního programu',
    'Počet absolventů v rámci Královéhradeckého kraje za rok 2022',
    'Název vyššího územního samosprávného celku',
    'Zeměpisná šířka v souřadnicovém systému WGS84',
    'Zeměpisná délka v souřadnicovém systému WGS84',
    'Název okresu',
    'Název obce'
]].copy() # Use .copy() to avoid SettingWithCopyWarning

df_maly.columns = ['skola', 'fakulta', 'program', 'absolventi', 'kraj', 'lat', 'lon', 'okres', 'obec']

# Handle potential non-numeric values and convert to numeric
df_maly['absolventi'] = pd.to_numeric(df_maly['absolventi'], errors='coerce').fillna(0).astype(int)


st.title("Interaktivní dashboard absolventů VŠ v Královéhradeckém kraji")
st.write("Tento dashboard vizualizuje data o počtu absolventů vysokých škol v Královéhradeckém kraji za rok 2022. Data zahrnují informace o školách, fakultách, studijních programech a geografickém rozložení absolventů.")
st.subheader("Počet absolventů podle kritérií")

# Add interactive elements
st.sidebar.header("Filtry")

# Get unique values safely, handling potential NaNs
available_skoly = df_maly['skola'].dropna().unique()
vybrana_skola = st.sidebar.selectbox(
    'Vyberte vysokou školu:',
    available_skoly
)

# Filter faculties based on selected school for the multiselect options
available_fakulty = df_maly[df_maly['skola'] == vybrana_skola]['fakulta'].dropna().unique()
vybrane_fakulty = st.sidebar.multiselect(
    'Vyberte fakulty:',
    available_fakulty,
    default=list(available_fakulty) # Default to selecting all available faculties for the selected school
)

# Slider for filtering the number of graduates
min_absolventi = st.sidebar.slider(
    'Minimální počet absolventů:',
    min_value=0,
    max_value=int(df_maly['absolventi'].max() if not df_maly['absolventi'].empty else 0),
    value=0
)

# Filter the dataframe based on selected criteria
df_filtered = df_maly[
    (df_maly['skola'] == vybrana_skola) &
    (df_maly['fakulta'].isin(vybrane_fakulty)) &
    (df_maly['absolventi'] >= min_absolventi)
].copy()

# Display a warning if no data is available after filtering
if df_filtered.empty:
    st.warning("Pro vybrané filtry nejsou k dispozici žádná data.")
else:
    # Plotting based on filtered data

    # 1. Bar chart by faculty
    absolventi_podle_fakulty_filtered = df_filtered.groupby('fakulta')['absolventi'].sum().reset_index()
    fig_fakulty = px.bar(
        absolventi_podle_fakulty_filtered,
        x='fakulta',
        y='absolventi',
        title='POČET ABSOLVENTŮ PODLE FAKULT',
        labels={'fakulta': 'Fakulta', 'absolventi': 'Počet absolventů'},
        color='fakulta'
    )
    fig_fakulty.update_layout(title={'text': 'POČET ABSOLVENTŮ PODLE FAKULT', 'font': {'size': 18, 'color': 'black', 'family': 'Arial', 'weight': 'bold'}})
    st.plotly_chart(fig_fakulty)

    # 2. Horizontal Bar chart by program
    absolventi_podle_programu_filtered = df_filtered.groupby('program')['absolventi'].sum().reset_index()
    fig_programy_bar = px.bar(
        absolventi_podle_programu_filtered,
        x='absolventi',
        y='program',
        title='POČET ABSOLVENTŮ PODLE STUDIJNÍHO PROGRAMU (SLOUPCOVÝ GRAF)',
        labels={'program': 'Studijní program', 'absolventi': 'Počet absolventů'},
        orientation='h',
        height=max(400, 30 * len(absolventi_podle_programu_filtered)), # Adjust height based on number of programs
        color='program'
    )
    fig_programy_bar.update_layout(title={'text': 'POČET ABSOLVENTŮ PODLE STUDIJNÍHO PROGRAMU (SLOUPCOVÝ GRAF)', 'font': {'size': 18, 'color': 'black', 'family': 'Arial', 'weight': 'bold'}})
    st.plotly_chart(fig_programy_bar)

    # 3. Treemap by program
    fig_programy_treemap = px.treemap(
        df_filtered,
        path=['program'],
        values='absolventi',
        title='POČET ABSOLVENTŮ PODLE STUDIJNÍHO PROGRAMU (TREEMAP)',
        labels={'program': 'Studijní program', 'absolventi': 'Počet absolventů'}
    )
    fig_programy_treemap.update_layout(title={'text': 'POČET ABSOLVENTŮ PODLE STUDIJNÍHO PROGRAMU (TREEMAP)', 'font': {'size': 18, 'color': 'black', 'family': 'Arial', 'weight': 'bold'}})
    st.plotly_chart(fig_programy_treemap)

    # 4. Density heatmap by school and faculty
    df_2dhist_filtered = df_filtered.groupby(['skola', 'fakulta'])['absolventi'].sum().reset_index()
    fig_heatmap = px.density_heatmap(
        df_2dhist_filtered,
        x='skola',
        y='fakulta',
        z='absolventi',
        title='POČET ABSOLVENTŮ PODLE ŠKOLY A FAKULTY (HEATMAP)',
        labels={'skola': 'Vysoká škola', 'fakulta': 'Fakulta', 'absolventi': 'Počet absolventů'},
        color_continuous_scale='Hot'
    )
    fig_heatmap.update_layout(title={'text': 'POČET ABSOLVENTŮ PODLE ŠKOLY A FAKULTY (HEATMAP)', 'font': {'size': 18, 'color': 'black', 'family': 'Arial', 'weight': 'bold'}})
    st.plotly_chart(fig_heatmap)

    # 5. Scatter mapbox for spatial distribution
    st.subheader("Geografické rozložení")
    fig_map = px.scatter_mapbox(
        df_filtered.dropna(subset=['lat', 'lon']), # Drop rows with missing lat/lon for map
        lat='lat',
        lon='lon',
        size='absolventi',
        color='absolventi',
        hover_name='skola',
        size_max=15,
        zoom=10, # Adjusted zoom level for potentially wider distribution
        height=500,
        title='PROSTOROVÉ ROZLOŽENÍ ABSOLVENTŮ'
    )
    fig_map.update_layout(mapbox_style='open-street-map')
    fig_map.update_layout(margin={'r':0,'t':40,'l':0,'b':0},
        title={'text': 'PROSTOROVÉ ROZLOŽENÍ ABSOLVENTŮ', 'font': {'size': 18, 'color': 'black', 'family': 'Arial', 'weight': 'bold'}}
    )
    st.plotly_chart(fig_map)

