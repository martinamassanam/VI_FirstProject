import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data



############# QUESTION 1 #############
def main_plot_1(merged_df):

    bars = alt.Chart(merged_df).mark_bar().encode(
        alt.X("Relation:Q", title="Relation (shootings/State population)*10e-6", axis = alt.Axis(titleColor='black', labelColor='black', titleFontSize = 20, labelFontSize=12)),
        alt.Y("State:N", sort='-x', title="State", axis = alt.Axis(titleColor='black', labelColor='black', titleFontSize = 20, labelFontSize=12)),
        color=alt.condition(
            alt.datum.Top_10,  #looks if it accomplish the boolean condition
            alt.value('#1f78b4'),  # Color for top 10
            alt.value('#b2b2b2')   # Color for the rest
        ),
        order = alt.Order('Relation', sort = 'descending'),  
        tooltip=['State', 'Relation']
    ).properties(title= "Mass shootings per Citizen by State (Scaled)")
   
    text = alt.Chart(merged_df).mark_text(
    align='left', baseline='middle', dx=3, color='black', fontSize=12    
).encode(
    alt.X("Relation:Q"),  
    alt.Y("State:N", sort='-x'),  
    text=alt.Text('Relation:Q', format='.2f')
)
    chart = bars+ text

    st.altair_chart(chart)


def first_question(mass_shootings, state_pop):   
    # Q1: What are the states with large number of mass shootings per citizen?
    # Barchart vertical (marcant TOP10) + Gràfic extra per la resta de variables 
    

    total_count = {}
    suspects_killed = {}
    suspects_injured = {}

    for i in range (len(mass_shootings)):
        state = mass_shootings['State'][i]

        if state not in total_count:
            total_count[state] = 1
            suspects_injured[state] = 0
            suspects_killed[state] = 0
        else:
            total_count[state] += 1
            
        if mass_shootings["Suspects Killed"][i] != 0:
            suspects_killed[state] += 1

        if mass_shootings["Suspects Injured"][i] != 0:
            suspects_injured[state] += 1


    shootings_df = pd.DataFrame(list(total_count.items()), columns=['State', 'Mass_Shootings'])

    merged_df = pd.merge(shootings_df, state_pop, on='State', how='inner') #only looking for states presents in both data
    
    scaling_factor = 10**6
    merged_df["Relation"] = (merged_df["Mass_Shootings"] / merged_df["Population"]) * scaling_factor
    merged_df = merged_df.sort_values(by='Relation', ascending=False).reset_index(drop = True)
    
    
    merged_df['Top_10'] = merged_df.index < 10

    main_plot_1(merged_df)


    

############# QUESTION 2 #############
def second_question(mass_shootings):   
    # Q2: How is the number of mass shootings per citizen distributed accross the different counties in the US?
    #     And accross states?
    
    ############# SHOOTINGS PER STATES #############

    #--------------- DATA PREPARATION ---------------#

    state_shootings = {state: [0, 0, 0, 0, 0] for state in mass_shootings['State']}
                            # ['FIPS', 'Shootings', 'Population', 'Suspects Injured', 'Suspects Killed']

    # FIPS for states not appearing in the original dataset
    state_shootings['Montana'] = [30, 0, 1122878, 0, 0]
    state_shootings['Wyoming'] = [56, 0, 584057, 0, 0]
    state_shootings['Vermont'] = [50, 0, 643077, 0, 0]
    
    for _, row in mass_shootings.iterrows():
        current_state = row['State']
        current_FIPS = row['FIPS']
        current_population = row['Population']
        suspects_injured = row['Suspects Injured']
        suspects_killed = row['Suspects Killed']

        state_shootings[current_state][0] = current_FIPS
        state_shootings[current_state][1] += 1 # occurrence count
        state_shootings[current_state][2] = current_population
        state_shootings[current_state][3] += suspects_injured
        state_shootings[current_state][4] += suspects_killed

    state_shootings = pd.DataFrame.from_dict(state_shootings, orient='index',
                                             columns=['FIPS', 'Total Shootings', 'Population', 'Suspects Injured', 'Suspects Killed'])
    state_shootings['Shootings per 100K Habitants'] = state_shootings['Total Shootings'] / state_shootings['Population'] * 10**5 # 10**5 is a scaling factor
    state_shootings['Suspects Injured per Shooting'] = state_shootings['Suspects Injured'] / state_shootings['Total Shootings']  
    state_shootings['Suspects Killed per Shooting'] = state_shootings['Suspects Killed'] / state_shootings['Total Shootings']  
    
    # there's three states where Total Shootings = 0, for them, we have computed 0 / 0 when creating the last two columns
    state_shootings.fillna(0, inplace=True)


    #--------------- CHOROPLETH PLOTTING ---------------#

    USA_states = alt.topo_feature(data.us_10m.url, 'states') 

    state_shootings_map = alt.Chart(USA_states
    ).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(state_shootings, 'FIPS', list(state_shootings.columns)) 
    ).mark_geoshape(
    ).encode(
        color = 'Shootings per 100K Habitants:Q'
    ).properties(
        title = 'Distribution of shootings per 100K habitants, per state',
        width = 900,
        height = 700
    ).project(
        type = 'albersUsa'
    )

    st.altair_chart(state_shootings_map)



    ############# SHOOTINGS PER COUNTIES #############

    #--------------- DATA PREPARATION ---------------#

    import geopandas as gpd
    from shapely.geometry import Point

    # to perform spatial join and intersect shooting coordinates with actual counties
    geometry = [Point(lon_lat) for lon_lat in zip(mass_shootings['Longitude'], mass_shootings['Latitude'])]
    mass_shootings_gdf = gpd.GeoDataFrame(mass_shootings[['State', 'FIPS']], geometry=geometry)

    counties_gdf = gpd.read_file('counties.geojson')
    counties_gdf = counties_gdf[['STATEFP', 'GEOID', 'NAME', 'geometry']] # reducing dimensionality

    # swapping coordinates
    from shapely.geometry import Polygon, MultiPolygon

    def swap_coordinates(geometry):
        if isinstance(geometry, Polygon): 
            return Polygon([(lon, lat) for lat, lon in geometry.exterior.coords])
        elif isinstance(geometry, MultiPolygon): 
            return  MultiPolygon([Polygon([(lat, lon) for (lat, lon) in polygon.exterior.coords]) for polygon in geometry.geoms])

    counties_gdf['geometry'] = counties_gdf['geometry'].apply(swap_coordinates) # swapping each row of the geometry column

    # setting and ensuring the use of the same coordinate system 
    mass_shootings_gdf.set_crs(epsg=4326, inplace=True)
    counties_gdf = counties_gdf.to_crs(mass_shootings_gdf.crs)

    # dropping Puerto Rico
    counties_gdf = counties_gdf[counties_gdf['STATEFP'] != '72'] 

    coordinates_w_counties = mass_shootings_gdf.sjoin(counties_gdf, how='right', predicate='within')
    # 'how=right' to ensure we keep all counties and their FIPS, even if there's no coordinate data for them in the mass_shootings dataframe
    coordinates_w_counties = coordinates_w_counties[['GEOID', 'NAME', 'STATEFP', 'FIPS']]
    
    ######## to compute average populations for counties in each state
    county_counts = {fips: 0 for fips in counties_gdf['STATEFP']}
        
    # counting how many counties there are for each state
    for _, row in counties_gdf.iterrows():
        current_state_FIPS = row['STATEFP']
        county_counts[current_state_FIPS] += 1

    # grouping mass shootings per county
    state_populations = {f: p for f,p in zip(state_shootings['FIPS'], state_shootings['Population'])}

    county_shootings = {row['NAME']: [0, 0, 0, 0] for _, row in coordinates_w_counties.iterrows()}
                                   # ['County FIPS', 'State FIPS', 'Shootings', 'State Population']
    for _, row in coordinates_w_counties.iterrows():
        current_county = row['NAME']
        current_state_FIPS = row['STATEFP']
        current_county_FIPS = row['GEOID']
        current_state_population = state_populations[int(current_state_FIPS)]
        
        county_shootings[current_county][0] = current_county_FIPS 
        county_shootings[current_county][1] = current_state_FIPS
        
        # we only want to sum occurrences if we have shooting data for it
        if pd.notna(row['FIPS']):
            county_shootings[current_county][2] += 1 # occurrence count
        # if there's no data for this county in the original dataset, we keep the 'count' at 0

        county_shootings[current_county][3] = current_state_population

    county_shootings = pd.DataFrame.from_dict(county_shootings, orient='index',
                                              columns=['County FIPS', 'State FIPS', 'Total Shootings', 'State Population'])

    # computing an average population for each county based on their state_population/amount_of_counties
    def compute_county_population(row):
        current_state_FIPS = row['State FIPS']
        return row['State Population'] / county_counts[current_state_FIPS]
    
    county_shootings['County Population'] = county_shootings.apply(compute_county_population, axis='columns')

    county_shootings['Shootings per 10K habitants'] = county_shootings['Total Shootings'] * 1 / county_shootings['County Population'] * 10**4 # 10**4 is a scaling factor
    county_shootings['County FIPS'] = county_shootings['County FIPS'].astype(int)

    unemployment_df = data.unemployment() # contains the FIPS inside the USA area in the column 'id'
    FIPS_intersection = set(county_shootings['County FIPS']).intersection(set(unemployment_df['id']))
    print(*unemployment_df['id'])

    # keeping only the counties with FIPS inside the USA area
    county_shootings = county_shootings[county_shootings['County FIPS'].isin(FIPS_intersection)]

    # adding the remaining rows of 'unemployment_df['id']' to have all plotable county FIPS
    for f in unemployment_df['id']:
        if f not in FIPS_intersection:  
            num_of_rows = county_shootings.shape[0] 
            county_shootings.loc[num_of_rows] = [f, 0, 0, 0, 0, 0]


    #--------------- CHOROPLETH PLOTTING ---------------#

    USA_counties = alt.topo_feature(data.us_10m.url, 'counties')
    
    county_shootings_map = alt.Chart(USA_counties
    ).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(county_shootings, 'County FIPS', list(county_shootings.columns)) 
    ).mark_geoshape(
    ).encode(
        color = 'Shootings per 10K habitants:Q'
    ).properties(
        title = 'Distribution of shootings per 10K habitants, per county',
        width = 900,
        height = 700
    ).project(
        type = 'albersUsa'
    )
    
    st.altair_chart(county_shootings_map)



    ############# SUSPECTS KILLED/INJURED PER STATES #############

    #--------------- CHOROPLETH PLOTTING ---------------#

    variable_list = ['Suspects Injured per Shooting', 'Suspects Killed per Shooting']

    suspects_harmed_map = alt.Chart(USA_states
    ).transform_lookup(
        lookup = 'id',
        from_ = alt.LookupData(state_shootings, 'FIPS', variable_list) 
    ).mark_geoshape(
    ).encode(
        alt.Color(alt.repeat('row'), type='quantitative').scale(scheme='lighttealblue')
    ).properties(
        width = 900,
        height = 700
    ).project(
        type = 'albersUsa'
    ).repeat(
        row = variable_list
    ).resolve_scale(
        color = 'independent'
    )

    st.markdown('### Suspects harmed per shooting, per state')
    st.altair_chart(suspects_harmed_map)




############# QUESTION 4 #############
def process_shootings_data(df):
    """Count all the shootings or incidents from the same month"""

    df["Incident Date"] = pd.to_datetime(df['Incident Date'], errors='coerce')
    df['year_month'] = df["Incident Date"].dt.to_period('M')
    grouped_df = df.groupby('year_month').size().reset_index(name="count")
    grouped_df['year_month'] = grouped_df['year_month'].dt.to_timestamp()
    grouped_df = grouped_df[1:-1] #deleting the first and last month that are incomplete

    
    return grouped_df


def fourth_question(mass_shootings, school_incidents):
    """" Line chart to show the mass shootings envolved the last years in the USA"""
    
    shootings_count = process_shootings_data(mass_shootings)

    max_value = shootings_count['count'].max()
    min_value = shootings_count['count'].min()
    mean_value = shootings_count['count'].mean().round(decimals = 2)

    max_point = shootings_count[shootings_count['count'] == max_value]
    min_point = shootings_count[shootings_count['count'] == min_value]
        
    line_chart = alt.Chart(shootings_count).mark_line().encode(
        alt.X('year_month:T', title = "Year - Month", axis=alt.Axis(labelColor ="black", labelAngle=45, format = "%b-%Y", titleColor = "black", titleFontSize = 20, labelFontSize=16)),
        alt.Y('count:Q', title = "Number of mass shootings", axis = alt.Axis(labelColor = "black", titleColor = "black", titleFontSize = 20, labelFontSize=16)),
    ).properties(
        title = alt.TitleParams(
            text = "Mass shootings during the last years in USA",
            fontSize = 28,
            anchor = "middle",
            color = "black"),
            width=700,
            height=500
    )
    
    max_point_chart = alt.Chart(max_point).mark_point(
        size=170, color='#d95f02', filled = True
    ).encode(
        alt.X('year_month:T'),
        alt.Y('count:Q')
    )

    min_point_chart = alt.Chart(min_point).mark_point(
        size=170, color='#1b9e77', filled = True
    ).encode(
        alt.X('year_month:T'),
        alt.Y('count:Q')
    )

    min_text = alt.Chart(min_point).mark_text(
        align = 'left', dx = 12, dy = 15, fontSize = 14, color = '#1b9e77'
    ).encode (
        alt.X('year_month:T'),
        alt.Y('count:Q'),
        alt.Text('count:Q')
    )

    max_text = alt.Chart(max_point).mark_text(
        align = 'left', dx = 7, dy = -10, fontSize = 14, color = '#d95f02'
    ).encode (
        alt.X('year_month:T'),
        alt.Y('count:Q'),
        alt.Text('count:Q')
    )

    mean_line = alt.Chart(shootings_count).mark_rule(
        color = '#a6cee3'
    ).encode(
        alt.Y('mean_value:Q')
    ).transform_calculate(mean_value=str(mean_value))

    mean_text = alt.Chart(shootings_count).mark_text(
        align = "left", dx = 250, dy = -10, color = '#a6cee3', size = 18
    ).encode(
        alt.Y('mean_value:Q'),
        text = alt.value(f'Mean: {mean_value:.2f}')
    ).transform_calculate(
        mean_value = str(mean_value)
    )

    total_chart = line_chart + max_point_chart + min_point_chart + mean_line + mean_text + max_text + min_text

    st.altair_chart(total_chart)




    

def main():
    mass_shootings = pd.read_csv('Mass_shooting.csv')
    state_pop = pd.read_csv("state-pop-clean.csv")
    school_incidents = pd.read_csv("School-incidents.csv")

    st.title('Mass shootings analysis')
    st.markdown('## First Question')
    first_question(mass_shootings, state_pop)

    st.markdown('---')
    st.markdown('## Second Question')
    second_question(mass_shootings)

    st.markdown('---')
    st.markdown('## Third Question')

    st.markdown('---')
    st.markdown('## Fourth Question')
    fourth_question(mass_shootings, school_incidents)

if __name__ =="__main__":
    main()
    

# Q3: Mapa de correlacions (semblant al de les diapos de múltiples mapes de US)
