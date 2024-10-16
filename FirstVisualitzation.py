import streamlit as st
import pandas as pd
import altair as alt



def first_plot(mass_shootings, state_pop):   
    # Q1: What are the states with large number of mass shootings per citizen?
    # Barchart vertical (marcant TOP10) + Gràfic extra per la resta de variables 

    total_count = {}

    for i in range (len(mass_shootings)):
        if mass_shootings['State'][i] not in total_count.keys():
            total_count[mass_shootings["State"][i]] = 1
        else:
            total_count[mass_shootings["State"][i]] += 1

    shootings_df = pd.DataFrame(list(total_count.items()), columns=['State', 'Mass_Shootings'])

    merged_df = pd.merge(shootings_df, state_pop, on='State', how='inner') #only looking for states presents in both data
    
    scaling_factor = 10**6
    merged_df["Relation"] = (merged_df["Mass_Shootings"] / merged_df["Population"]) * scaling_factor
    merged_df = merged_df.sort_values(by='Relation', ascending=False)
    
    """
    relation_10th = merged_df["Relation"][9]
    relation_10th_df = pd.DataFrame({'y': [relation_10th]})"""

    bars = alt.Chart(merged_df).mark_bar(color='#a6cee3').encode(
        alt.X("Relation:Q", title="Reltaion (shootings/State population)*10e-6", axis = alt.Axis(titleColor='black', labelColor='black')),
        alt.Y("State:N", sort='-x', title="State", axis = alt.Axis(titleColor='black', labelColor='black')),
        order = alt.Order('Relation', sort = 'descending'),  
        tooltip=['State', 'Relation']
    ).properties(title= "Mass shootings per Citizen by State (Scaled)")
   

    chart = bars 

    st.altair_chart(chart)

    

def main():
    mass_shootings = pd.read_csv('Mass_shooting.csv')
    state_pop = pd.read_csv("state-pop-clean.csv")

    st.title('States with large number of mass shootings per citizen')
    first_plot(mass_shootings, state_pop)

if __name__ =="__main__":
    main()
    




# Muestra las primeras filas del dataframe

# Q2: Mapa per states (coropleth, gradient) i per counties 

# Q3: Mapa de correlacions (semblant al de les diapos de múltiples mapes de US)

# Q4: Serie (linechart)
