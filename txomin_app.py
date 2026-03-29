# --- TAB 2: MAPA (BERRESKURATUTA: NEURKETA TRESNAK) ---
with tab2:
    st.subheader("🗺️ Mutrikuko IHM Plotterra")
    
    # Mapa oinarria
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    
    # Geruza desberdinak (Hondoa eta IHM)
    folium.TileLayer(
        tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', 
        attr='Esri',
        name='Topografikoa'
    ).add_to(m)
    
    # IHM Geruza (WMS) - Sakonera eta isobatak
    folium.WmsTileLayer(
        url='https://ideihm.covam.es/wms/cartografia_espanola?',
        layers='relieve,isobatas',
        name='IHM Sakonera',
        fmt='image/png',
        transparent=True,
        overlay=True
    ).add_to(m)
    
    # 🛠️ HEMEN DAUDE BERRIRO TRESNAK:
    # 1. Neurketa tresna (Regla)
    plugins.MeasureControl(position='topright', primary_length_unit='meters', secondary_length_unit='miles', primary_area_unit='sqmeters').add_to(m)
    
    # 2. Marrazketa tresnak (Dibujo)
    plugins.Draw(position='topleft', draw_options={'polyline':{'shapeOptions':{'color':'#FBBF24'}}, 'circle':False, 'rectangle':False, 'marker':True}).add_to(m)
    
    # Pantailaratu mapa
    st_folium(m, width="100%", height=600, key="mapa_txomin_full")
