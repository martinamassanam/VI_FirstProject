import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data

# for County choropleths 
import geopandas as gpd
from shapely.geometry import Point
from shapely.geometry import Polygon, MultiPolygon



############# QUESTION 1 #############
def first_question(mass_shootings):   
    """Bar chart displaying the quantity of mass shootings by state, with emphasis on the top 10 states."""# Q1: What are the states with large number of mass shootings per citizen?
    
        #--------------- DATA PREPARATION ---------------#

    state_shootings = {state: [0, 0] for state in set(mass_shootings['State'])}
                            # ['Shootings', 'Population']
    
    # data for states not appearing in the original dataset
    state_shootings['Montana'] = [0, 1122878]
    state_shootings['Wyoming'] = [0, 584057]
    state_shootings['Vermont'] = [0, 643077]

    for _, row in mass_shootings.iterrows():
        current_state = row['State']
        current_population = row['Population']

        state_shootings[current_state][0] += 1 # occurrence count
        state_shootings[current_state][1] = current_population

    state_shootings = pd.DataFrame.from_dict(state_shootings, orient='index',
                                             columns=['Total Shootings', 'Population'])
    state_shootings = state_shootings.reset_index().rename(columns={'index': 'State'})
    state_shootings.groupby(['State']).sum()
    state_shootings['Shootings per 1M Habitants'] = state_shootings['Total Shootings'] / state_shootings['Population'] * 10**6

    # sort state values in descending order
    state_shootings = state_shootings.sort_values(by = 'Shootings per 1M Habitants', ascending = False).reset_index(drop = True)
    state_shootings['Top_10'] = state_shootings.index < 10


    #--------------- BARCHART PLOTTING ---------------#

    shootings_bars = alt.Chart(state_shootings).mark_bar().encode(
        alt.X('Shootings per 1M Habitants:Q', axis = alt.Axis(titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)),
        alt.Y('State:N', sort='-x', axis = alt.Axis(titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)),
        color = alt.condition(
            alt.datum.Top_10,      
            alt.value('#1f78b4'),  # color for top 10
            alt.value('#b2b2b2')   # color for the rest
        ),
        order = alt.Order('Shootings per 1M Habitants', sort = 'descending'),  
        tooltip = ['State', 'Shootings per 1M Habitants']
    ).properties(title= alt.TitleParams(
            text = 'Mass shootings per million citizens by State',
            fontSize = 24,
            color = 'black')
    )
   
    shootings_text = alt.Chart(state_shootings).mark_text(
        align = 'left', baseline = 'middle', dx = 3, color = 'black', fontSize = 12    
    ).encode(
        alt.X('Shootings per 1M Habitants:Q'),  
        alt.Y('State:N', sort='-x'),  
        alt.Text('Shootings per 1M Habitants:Q', format='.2f')
    )
    
    shootings_barchart = shootings_bars + shootings_text
    st.altair_chart(shootings_barchart)



############# QUESTION 2 #############
def second_question(mass_shootings, county_population, counties_gdf):   
    # Q2: How is the number of mass shootings per citizen distributed accross the different counties in the US?
    #     And accross states?
    
    ############# SHOOTINGS PER STATES #############

    #--------------- DATA PREPARATION ---------------#

    state_shootings = {state: [0, 0, 0, 0, 0, 0] for state in set(mass_shootings['State'])}
                            # ['FIPS', 'Shootings', 'Population', 'Suspects Injured', 'Suspects Killed', 'Total Suspects']

    # data for states not appearing in the original dataset
    state_shootings['Montana'] = [30, 0, 1122878, 0, 0, 0]
    state_shootings['Wyoming'] = [56, 0, 584057, 0, 0, 0]
    state_shootings['Vermont'] = [50, 0, 643077, 0, 0, 0]
    
    for _, row in mass_shootings.iterrows():
        current_state = row['State']
        current_FIPS = row['FIPS']
        current_population = row['Population']
        suspects_injured = row['Suspects Injured']
        suspects_killed = row['Suspects Killed']
        suspects_arrested = int(row['Suspects Arrested'])

        state_shootings[current_state][0] = current_FIPS
        state_shootings[current_state][1] += 1 # occurrence count
        state_shootings[current_state][2] = current_population
        state_shootings[current_state][3] += suspects_injured
        state_shootings[current_state][4] += suspects_killed
        state_shootings[current_state][5] += suspects_injured + suspects_killed + suspects_arrested 

    state_shootings = pd.DataFrame.from_dict(state_shootings, orient='index',
                                             columns=['FIPS', 'Total Shootings', 'Population', 'Suspects Injured', 'Suspects Killed', 'Suspects'])
    state_shootings = state_shootings.reset_index().rename(columns={'index': 'State'})
    state_shootings['Shootings per 1M Habitants'] = state_shootings['Total Shootings'] / state_shootings['Population'] * 10**6 # 10**6 is a scaling factor
    state_shootings['% of Suspects Injured'] = state_shootings['Suspects Injured'] / state_shootings['Suspects'] * 100
    state_shootings['% of Suspects Killed'] = state_shootings['Suspects Killed'] / state_shootings['Suspects'] * 100
    
    # there's three states where Total Shootings = 0, for them, we have computed 0 / 0 when creating the last two columns
    state_shootings.fillna(0, inplace=True)

    # eliminating Columbia to expand color range, we will represent Columbia alternatively
    shootings_notcolumbia = state_shootings[state_shootings['FIPS'] != 11] 



    #--------------- CHOROPLETH PLOTTING ---------------#

    USA_states = alt.topo_feature(data.us_10m.url, 'states') 

    state_shootings_map = alt.Chart(USA_states
    ).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(shootings_notcolumbia, 'FIPS', list(shootings_notcolumbia.columns)) 
    ).mark_geoshape(stroke='darkgray'
    ).encode(
        color = alt.Color('Shootings per 1M Habitants:Q', legend=alt.Legend(title="Shootings per 1M Habitants", titleColor = "black", labelColor="black", labelFontSize=12)
        ),
        tooltip = ['State:N', 'Shootings per 1M Habitants:Q']
    ).properties(
        title = alt.TitleParams(
            text = 'Distribution of shootings per million habitants, by state',
            fontSize = 24,
            color = 'black'),
        width = 600,
        height = 400
    ).project(
        type = 'albersUsa'
    )


    # to highlight the District of Columbia in the map
    columbia_data = pd.DataFrame({
        'Latitude': [38.89511],     
        'Longitude': [-77.03637],   
        'State': ['District of Columbia'],
        'Shootings per 1M Habitants': [state_shootings[state_shootings['FIPS'] == 11]['Shootings per 1M Habitants'].iloc[0]]
    })

    columbia_zoom = alt.Chart(columbia_data).mark_circle(
        size = 50,           
        opacity = 0.7
    ).encode(
        color = alt.Color('State:N', scale=alt.Scale(scheme = 'reds'), legend=alt.Legend(labelColor='black', titleColor='black')),
        longitude = 'Longitude:Q',
        latitude = 'Latitude:Q',
        tooltip = ['State:N', 'Shootings per 1M Habitants:Q']
    ).properties(
        width = 600,
        height = 400
    )
    
    state_shootings_complete = state_shootings_map + columbia_zoom



    ############# SHOOTINGS PER COUNTIES #############

    #--------------- DATA PREPARATION ---------------#

    # to perform spatial join and intersect shooting coordinates with actual counties
    geometry = [Point(lon_lat) for lon_lat in zip(mass_shootings['Longitude'], mass_shootings['Latitude'])]
    mass_shootings_gdf = gpd.GeoDataFrame(mass_shootings[['State', 'FIPS']], geometry=geometry)

    counties_gdf = counties_gdf[['STATEFP', 'GEOID', 'NAME', 'geometry']] # reducing dimensionality

    # swapping coordinates
    def swap_coordinates(geometry):
        if isinstance(geometry, Polygon): 
            return Polygon([(lon, lat) for lat, lon in geometry.exterior.coords])
        elif isinstance(geometry, MultiPolygon): 
            return  MultiPolygon([Polygon([(lat, lon) for (lat, lon) in polygon.exterior.coords]) for polygon in geometry.geoms])

    counties_gdf['geometry'] = counties_gdf['geometry'].apply(swap_coordinates) # swapping each row of the geometry column

    # setting and ensuring the use of the same coordinate system 
    mass_shootings_gdf.set_crs(epsg=4326, inplace=True)
    counties_gdf = counties_gdf.to_crs(mass_shootings_gdf.crs)

    # dropping Puerto Rico, because it is outside of the North America region
    counties_gdf = counties_gdf[counties_gdf['STATEFP'] != '72'] 

    coordinates_w_counties = mass_shootings_gdf.sjoin(counties_gdf, how='right', predicate='within')
    # 'how=right' to ensure we keep all counties and their FIPS, even if there's no coordinate data for them in the mass_shootings dataframe
    coordinates_w_counties = coordinates_w_counties[['GEOID', 'FIPS']]
    coordinates_w_counties = coordinates_w_counties.set_axis(['FIPS', 'STATEFIPS'], axis=1)
    coordinates_w_counties['FIPS'] = coordinates_w_counties['FIPS'].astype(int)

    county_population = county_population[['FIPStxt', 'Area_Name', 'State', 'POP_ESTIMATE_2023']]
    # to take into account same County names in different States
    county_population['County'] = county_population['Area_Name'] + ', ' + county_population['State']
    county_population = county_population[['FIPStxt', 'County', 'POP_ESTIMATE_2023']]
    county_population = county_population.set_axis(['FIPS', 'COUNTYNAME', 'COUNTYPOPULATION'], axis=1)
    
    coordinates_w_counties = coordinates_w_counties.merge(county_population, on='FIPS')

    county_shootings = {county: [0, 0, 0] for county in set(coordinates_w_counties['COUNTYNAME'])}
                              # ['County FIPS', 'Shootings', 'County Population']
    for _, row in coordinates_w_counties.iterrows():
        current_county = row['COUNTYNAME']
        current_county_FIPS = row['FIPS']
        current_county_population = row['COUNTYPOPULATION']
        if current_county_population is None:
            current_county_population = 0
        elif current_county_population is not None and type(current_county_population) == str: 
            current_county_population = int(row['COUNTYPOPULATION'].replace(',', ''))
        
        county_shootings[current_county][0] = current_county_FIPS 
        
        # we only want to sum occurrences if we have shooting data for it
        if pd.notna(row['STATEFIPS']):
            county_shootings[current_county][1] += 1 # occurrence count
        # if there's no data for this county in the original dataset, we keep the 'count' at 0

        county_shootings[current_county][2] = current_county_population

    county_shootings = pd.DataFrame.from_dict(county_shootings, orient='index',
                                              columns=['County FIPS', 'Total Shootings', 'County Population'])

    county_shootings['Shootings per 100K habitants'] = county_shootings['Total Shootings'] * 1 / county_shootings['County Population'] * 10**5 # 10**5 is a scaling factor
    county_shootings.fillna(0, inplace=True)

    full_FIPS_list = data.unemployment() # contains all FIPS inside the USA area in the column 'id', plottable in Altair
    # adding the remaining rows of 'unemployment_df['id']' to have all plotable county FIPS
    for f in full_FIPS_list['id']:
        if f not in set(county_shootings['County FIPS']):  
            num_of_rows = county_shootings.shape[0] 
            county_shootings.loc[num_of_rows] = [f, 0, 0, 0]

    # only keeping County FIPS
    county_shootings = county_shootings[county_shootings['County FIPS'].isin(set(full_FIPS_list['id']))]
    
    county_shootings = county_shootings.reset_index().rename(columns={'index': 'County'})


    #--------------- CHOROPLETH PLOTTING ---------------#

    USA_counties = alt.topo_feature(data.us_10m.url, 'counties')
    
    county_shootings_map = alt.Chart(USA_counties
    ).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(county_shootings, 'County FIPS', list(county_shootings.columns)) 
    ).mark_geoshape().encode(
        color = alt.Color('Shootings per 100K habitants:Q', legend=alt.Legend(
                title="Shootings per 100K habitants",
                titleColor='black', 
                labelColor='black')),
        tooltip = ['County:N', 'Shootings per 100K habitants:Q']
    ).properties(
        title = alt.TitleParams(
            text = 'Distribution of shootings per 100k habitants, by country',
            fontSize = 24,
            color = 'black'),
        width = 600,
        height = 400
    ).project(
        type = 'albersUsa'
    )

    state_shape_overlay = alt.Chart(USA_states
    ).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(state_shootings, 'FIPS', list(state_shootings.columns)) 
    ).mark_geoshape(
        stroke = 'gray',
        fill = 'transparent'
    ).properties(
        width = 600,
        height = 400
    ).project(
        type = 'albersUsa'
    )

    county_shootings_overlay = alt.Chart(USA_counties
    ).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(county_shootings, 'County FIPS', list(county_shootings.columns)) 
    ).mark_geoshape(
        stroke='lightgray',
        fill = 'transparent'
    ).encode(
        color = alt.Color(
            'Shootings per 100K habitants:Q', 
            legend=alt.Legend(
                title="Shootings per 100K habitants",
                titleColor='black', 
                labelColor='black')
        ),
        tooltip = ['County:N', 'Shootings per 100K habitants:Q'],
    ).properties(
        title = alt.TitleParams(
            text = 'Distribution of shootings per 100k habitants, by county',
            fontSize = 24,
            color = 'black'),
        width = 600,
        height = 400
    ).project(
        type = 'albersUsa'
    )

    county_shootings_choropleth = county_shootings_map + state_shape_overlay + county_shootings_overlay

    # plotting by State and County side by side 
    state_plot, county_plot = st.columns(2)
    with state_plot: 
        st.altair_chart(state_shootings_complete)
    with county_plot:
        st.altair_chart(county_shootings_choropleth)

    


    ############# SUSPECTS KILLED/INJURED PER STATES #############

    #--------------- CHOROPLETH PLOTTING ---------------#

    suspects_injured_map = alt.Chart(USA_states
    ).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(state_shootings, 'FIPS', list(state_shootings.columns)) 
    ).mark_geoshape(stroke='darkgray'
    ).encode(
        color = alt.Color('% of Suspects Injured:Q', legend=alt.Legend(
                title="Shootings per 100K habitants",
                titleColor='black', 
                labelColor='black')).scale(scheme = 'lighttealblue'),
        tooltip = ['State:N', '% of Suspects Injured:Q']
    ).properties(
        title = alt.TitleParams(
            text = 'Percentage of Suspects Injured per shooting, by state',
            fontSize = 24,
            color = 'black'),
        width = 600,
        height = 400
    ).project(
        type = 'albersUsa'
    )


    suspects_killed_map = alt.Chart(USA_states
    ).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(state_shootings, 'FIPS', list(state_shootings.columns)) 
    ).mark_geoshape(stroke='darkgray'
    ).encode(
        color = alt.Color('% of Suspects Killed:Q', legend=alt.Legend(
                title="Shootings per 100K habitants",
                titleColor='black', 
                labelColor='black')).scale(scheme = 'lighttealblue'),
        tooltip = ['State:N', '% of Suspects Killed:Q']
    ).properties(
        title = alt.TitleParams(
            text = 'Percentage of suspects killed per shooting, by state',
            fontSize = 24,
            color = 'black'),
        width = 600,
        height = 400
    ).project(
        type = 'albersUsa'
    )

    injured_plot, killed_plot = st.columns(2)
    with injured_plot: 
        st.altair_chart(suspects_injured_map)
    with killed_plot:
        st.altair_chart(suspects_killed_map)


############# QUESTION 3 #############
def third_question(mass_shootings, school_incidents):
    """Scatter plot for the quantity of mass_shootings and school incidents per state"""
    
    #--------------- DATA PREPARATION ---------------#
    mass_shootings['Incident Date'] = pd.to_datetime(mass_shootings['Incident Date'])
    mass_shootings_reduced = mass_shootings[mass_shootings['Incident Date'] > '2022-11-01']


    shootings_count = mass_shootings_reduced.groupby('State').size().reset_index(name="Shootings_count")
    school_count = school_incidents.groupby('State').size().reset_index(name="School_count")
    total_count = pd.merge(shootings_count, school_count, on='State', how='outer')
    total_count = total_count.fillna(0)

    total_count = total_count.merge(mass_shootings[['State','Population']], on = "State", how = "left")
    total_count.loc[total_count['State'] == "Wyoming", 'Population'] = 584057.0
    total_count.loc[total_count['State'] == "Montana", 'Population'] = 1122878.0
    total_count.loc[total_count['State'] == "Vermont", 'Population'] = 643077.0

    total_count['Ratio_shootings'] = (total_count['Shootings_count']/total_count['Population'])*10**6
    total_count['Ratio_schools'] = (total_count['School_count']/total_count['Population'])*10**6
    

    #--------------- SCATTER PLOT PLOTTING ---------------#
    scatter_plot = alt.Chart(total_count).mark_circle(color='#1f78b4').encode(
        alt.X('Ratio_shootings:Q', title = "Mass Shootings per million inhabitants", axis = alt.Axis(titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)),
        alt.Y('Ratio_schools:Q', title = "School Incidents per million inhabitants", axis = alt.Axis(titleColor = 'black', labelColor = 'black', titleFontSize = 14, labelFontSize = 12)),
        tooltip=['State', 'Ratio_shootings', 'Ratio_schools']
    ).properties(
        title = alt.TitleParams(
            text = 'Relationship Between Mass Shootings and School Incidents',
            fontSize = 24,
            color = 'black'),
        width=600,
        height=400
    )
    
    linear_regression = scatter_plot.transform_regression( 
        'Ratio_shootings', 
        'Ratio_schools' 
    ).mark_line(color ='#a6cee3')

    return scatter_plot + linear_regression



############# QUESTION 4 #############
def fourth_question(mass_shootings, school_incidents, regression_plot):
    """" Line chart to show the mass shootings envolved the last years in the USA"""

    #--------------- DATA PREPARATION ---------------#

    mass_shootings['Incident Date'] = pd.to_datetime(mass_shootings['Incident Date'], errors= 'coerce')
    mass_shootings['Year_Month'] = mass_shootings['Incident Date'].dt.to_period('M')
    
    # to have monthly total shootings
    total_shootings = mass_shootings.groupby('Year_Month').size().reset_index(name = 'Count')
    total_shootings['Year_Month'] = total_shootings['Year_Month'].dt.to_timestamp()
    total_shootings = total_shootings[1 : -1] # deleting the first and last month that are incomplete


    max_value = total_shootings['Count'].max()
    min_value = total_shootings['Count'].min()
    mean_value = total_shootings['Count'].mean().round(decimals = 2)

    max_point = total_shootings[total_shootings['Count'] == max_value]
    min_point = total_shootings[total_shootings['Count'] == min_value]
        
    
    #--------------- LINE CHART PLOTTING ---------------#

    shootings_linechart = alt.Chart(total_shootings).mark_line().encode(
        alt.X('Year_Month:T', title = 'Month - Year', axis = alt.Axis(labelColor = 'black', labelAngle = 45, format = '%b-%Y', titleColor = 'black', titleFontSize = 14, labelFontSize = 12)),
        alt.Y('Count:Q', title = 'Mass shootings', axis = alt.Axis(labelColor = 'black', titleColor = 'black', titleFontSize = 14, labelFontSize = 12)),
    ).properties(
        title = alt.TitleParams(
            text = 'Mass shootings during the last four years in the USA',
            fontSize = 24,
            color = 'black'),
            width = 600,
            height = 400
    )
    
    max_point_chart = alt.Chart(max_point).mark_point(
        size = 170, color = '#d95f02', filled = True, shape = 'triangle-up'
    ).encode(
        alt.X('Year_Month:T'),
        alt.Y('Count:Q'),
    )

    min_point_chart = alt.Chart(min_point).mark_point(
        size = 170, color = '#1b9e77', filled = True, shape = 'triangle-down'
    ).encode(
        alt.X('Year_Month:T'),
        alt.Y('Count:Q'),
    )

    min_text = alt.Chart(min_point).mark_text(
        align = 'left', dx = 12, dy = 15, fontSize = 14, color = '#1b9e77'
    ).encode (
        alt.X('Year_Month:T'),
        alt.Y('Count:Q'),
        alt.Text('Count:Q')
    )

    max_text = alt.Chart(max_point).mark_text(
        align = 'left', dx = 7, dy = -10, fontSize = 14, color = '#d95f02'
    ).encode (
        alt.X('Year_Month:T'),
        alt.Y('Count:Q'),
        alt.Text('Count:Q')
    )

    mean_line = alt.Chart(total_shootings).mark_rule(
        color = '#a6cee3'
    ).encode(
        alt.Y('mean_value:Q')
    ).transform_calculate(mean_value=str(mean_value))

    mean_text = alt.Chart(total_shootings).mark_text(
        align = "left", dx = 200, dy = -10, color = '#a6cee3', size = 18
    ).encode(
        alt.Y('mean_value:Q'),
        text = alt.value(f'Mean: {mean_value:.2f}')
    ).transform_calculate(
        mean_value = str(mean_value)
    )

    complete_chart = shootings_linechart + max_point_chart + min_point_chart + mean_line + mean_text + max_text + min_text

    relation_plot, line_plot = st.columns(2)
    with relation_plot: 
        st.altair_chart(regression_plot)
    with line_plot:
        st.altair_chart(complete_chart)
    




def main():
    mass_shootings = pd.read_csv('MassShootings.csv')
    county_population = pd.read_csv('CountyPopulation.csv')
    counties_gdf = gpd.read_file('Counties.geojson')
    school_incidents = pd.read_csv('SchoolIncidents.csv')

    st.set_page_config(layout = 'wide')
    st.title('Analysis of Mass Shootings in the US')
    st.markdown('**Authors:** Raquel Jolis Carné and Martina Massana Massip')
    st.divider()

    first_question(mass_shootings)
    second_question(mass_shootings, county_population, counties_gdf)
    regression_plot = third_question(mass_shootings, school_incidents)
    fourth_question(mass_shootings, school_incidents, regression_plot)

if __name__ =="__main__":
    main()
