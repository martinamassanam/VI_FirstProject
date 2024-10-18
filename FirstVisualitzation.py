iimport streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data

def main_plot_1(merged_df):

    bars = alt.Chart(merged_df).mark_bar().encode(
        alt.X("Relation:Q", title="Relation (shootings/State population)*10e-6", axis = alt.Axis(titleColor='black', labelColor='black')),
        alt.Y("State:N", sort='-x', title="State", axis = alt.Axis(titleColor='black', labelColor='black')),
        color=alt.condition(
            alt.datum.Top_10,  #looks if it accomplish the boolean condition
            alt.value('#1f78b4'),  # Color for top 10
            alt.value('#b2b2b2')   # Color for the rest
        ),
        order = alt.Order('Relation', sort = 'descending'),  
        tooltip=['State', 'Relation']
    ).properties(title= "Mass shootings per Citizen by State (Scaled)")
   
    text = bars.mark_text(
        align='left',  
        baseline='middle',  
        dx=3,  
        color='black' 
    ).encode(
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

    """
    complete_df = pd.DataFrame({
        "State": list(total_count.keys()),
        "Total Incidents": list(total_count.values()),
        "Suspects Killed": list(suspects_killed.values()),
        "Suspects Injured": list(suspects_injured.values())
    })
    complete_df['Suspects Killed per Incident'] = complete_df['Suspects Killed'] / complete_df['Total Incidents']
    complete_df['Suspects Injured per Incident'] = complete_df['Suspects Injured'] / complete_df['Total Incidents']
    
    geom = alt.topo_feature(data.us_10m.url, 'states')
    
    slider = alt.binding_range(min=0, max=complete_df['Suspects Killed per Incident'].max(), step=0.01, name='Killed per Incident')
    
    selection = alt.selection_point(fields=['Suspects Killed per Incident'], bind=slider)

    map_chart = alt.Chart(geom).transform_filter(selection).transform_lookup(
        lookup = "id",
        from_ = alt.LookupData(complete_df, 'State', ['Total Incidents', 'Suspects Killed', 'Suspects Injured', 'Suspects Killed per Incident'])
    ).transform_calculate(
        geometry = "datum.geom.geometry",
        type = "datum.geom.type"
    ).mark_geoshape(
    ).encode(
        alt.Color("Suspects Killed per Incident:Q", scale = alt.Scale(scheme = "reds")),
    ).add_params(selection
    ).properties(
        title = "Suspects Killed per Incident by State"
    )

    st.altair_chart(map_chart)
    """
    

def process_shootings_data(df):
    """Count all the shootings or incidents from the same month"""

    df["Incident Date"] = pd.to_datetime(df['Incident Date'], errors='coerce')
    df['year_month'] = df["Incident Date"].dt.to_period('M')
    grouped_df = df.groupby('year_month').size().reset_index(name="count")
    grouped_df['year_month'] = grouped_df['year_month'].dt.to_timestamp()

    return grouped_df



def fourth_question(mass_shootings, school_incidents):
    """" Line chart to show the mass shootings envolved the last years in the USA"""
    
    shootings_count = process_shootings_data(mass_shootings)
    school_count = process_shootings_data(school_incidents)

    shootings_count["type"] = "Mass Shootings"
    school_count["type"] = "School Incidents"
    total_count = pd.concat([shootings_count, school_count])
        
    line_chart = alt.Chart(total_count).mark_line().encode(
        alt.X('year_month:T', title = "Year - Month"),
        alt.Y('count:Q', title = "Number of Incidents"),
        alt.Color("type:N", title = "Incident Type", 
                  scale = alt.Scale(
                      domain = ['Mass Shootings', 'School Incidents'],
                      range = ["#1f78b4", "#b2df8a"]
                  ))
    ).properties(
        title = "Mass shootings during the years",
        width=900,
        height=500
    )
    st.altair_chart(line_chart)



    

def main():
    mass_shootings = pd.read_csv('Mass_shooting.csv')
    state_pop = pd.read_csv("state-pop-clean.csv")
    school_incidents = pd.read_csv("School-incidents.csv")

    st.title("Mass shootings analysis")
    first_question(mass_shootings, state_pop)

    fourth_question(mass_shootings, school_incidents)

if __name__ =="__main__":
    main()
    



# Q2: Mapa per states (coropleth, gradient) i per counties 

# Q3: Mapa de correlacions (semblant al de les diapos de múltiples mapes de US)

