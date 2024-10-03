import streamlit as st
import numpy as np
import pandas as pd

from IPython.display import display

st.title("Fonciers 2020-2023 Maxwell")
st.sidebar.title("Sommaire")
pages=["Tables des ventes", "Adresses des biens concernés", "Modélisation"]
page=st.sidebar.radio("Aller vers", pages)

@st.cache_data
def import_dataset():
  df = pd.read_csv('data_20-23_preprocessed_v2.csv', index_col=0, dtype={'Code postal':'str','Valeur':'str',
                                                                      'CP':'str'})
  df['Date mutation'] = pd.to_datetime(df['Date mutation'])
  df = df.reset_index(drop=True)
  return df

# Dernière modifications du dataset importé
df = import_dataset()
df = df.loc[df['Valeur fonciere'] > 250000]
ordre = ['0 - 250k', '250k - 500k', '500k - 1M', '1M - 1M500', '1M500 - 3M', '3M+']
df['Valeur'] = pd.Categorical(df['Valeur'], categories=ordre, ordered=True)
df['Valeur'] = df['Valeur'].cat.remove_categories(['0 - 250k'])
df['Year'] = df['Date mutation'].dt.year.astype(str)

# PAGE1
if page == pages[0]:
  # Présentation du DataFrame global
  df_ventes = df.groupby('Valeur').size().reset_index(name='Nombre de transactions depuis 2020')
  st.dataframe(df_ventes)
  
  # Choix des dates et codes postaux pour affichage dynamique
  choix_dep = [x for x in np.unique(df.CP)]
  option_dep = st.selectbox("Choix du département à analyser", choix_dep)
  st.session_state['option_dep'] = option_dep

  choix_date = [x for x in np.unique(df.Year)]
  option_date = st.selectbox("Choix de l'année à analyser", choix_date)

  st.write("Données pour le département :", option_dep)
  
  st.session_state['option_date'] = option_date
  
  # Affichage du tableau depuis 2020
  df_ventes_dep = df.loc[df.CP == option_dep].groupby('Valeur').size().reset_index(name='Nombre de transactions depuis 2020')
  st.dataframe(df_ventes_dep)
  
  # Affichage du tableau de l'année choisie
  st.write("Données pour l'année :", option_date)
  df_ventes_dep_23= df.loc[(df.CP == option_dep) & (df.Year == str(option_date))].groupby('Valeur').size().reset_index(name='Nombre de transactions en {}'.format(option_date))
  st.dataframe(df_ventes_dep_23)

# PAGE 2
elif page == pages[1]:
  st.title("Adresses des biens vendus")

  # Vérifie si l'option a été sélectionnée dans Page 1
  if 'option_date' in st.session_state:
      st.write(f"Vous avez sélectionné l'année {st.session_state['option_date']} et le département {st.session_state['option_dep']}")
      option_date = st.session_state['option_date']
      option_dep = st.session_state['option_dep']
      
      # Transformation du dataframe pour affichage des transactions
      df_adresses = df.loc[(df.CP == option_dep) & (df.Year == option_date)].sort_values(by = 'Valeur fonciere', ascending = False)
      info_utiles = ['Valeur fonciere', 'Code postal', 'No voie', 'Voie', 'Commune']
      df_adresses['Valeur fonciere'] = np.round(df_adresses['Valeur fonciere'])

      # Affichage du dataframe
      st.dataframe(df_adresses[info_utiles].head(150))

  else:
      st.write("Aucune option sélectionnée sur la Page 1.")