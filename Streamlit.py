import streamlit as st
import numpy as np
import pandas as pd

# Variable pour activer/désactiver l'authentification
AUTH_ENABLED = False  # Change cette valeur pour activer ou désactiver

PASSWORD = "ZaZa"

def authenticate():
    password = st.text_input("Entrez le mot de passe :", type="password")
    if password == PASSWORD:
        return True
    else:
        st.error("Mot de passe incorrect. Veuillez réessayer.")
        return False

if AUTH_ENABLED:
    if not authenticate():
        st.stop()

# Vérifiez l'authentification
st.title("Fonciers 2020-2023 Maxwell")
st.sidebar.title("Sommaire")
pages = ["Tables des ventes", "Adresses des biens concernés", "Modélisation"]
page = st.sidebar.radio("Aller vers", pages)

# Chargement du DataFrame
@st.cache_data
def import_dataset():
    df = pd.read_csv('data_20-23_preprocessed_v2.csv', index_col=0, dtype={'Code postal': 'str', 'Valeur': 'str', 'CP': 'str'})
    df['Date mutation'] = pd.to_datetime(df['Date mutation'])
    df = df.reset_index(drop=True)
    return df

# Importation et traitement des données
df = import_dataset()
df = df.loc[df['Valeur fonciere'] > 250000]
ordre = ['0 - 250k', '250k - 500k', '500k - 1M', '1M - 1M500', '1M500 - 3M', '3M+']
df['Valeur'] = pd.Categorical(df['Valeur'], categories=ordre, ordered=True)
df['Valeur'] = df['Valeur'].cat.remove_categories(['0 - 250k'])
df['Year'] = df['Date mutation'].dt.year.astype(str)

# Initialisation des options
choix_date = list(np.unique(df.Year))
choix_dep = list(np.unique(df.CP))

# Fonction pour calculer les ventes par valeur
def calculate_sales_by_value(df):
    return df.groupby('Valeur').size().reset_index(name='Nombre de transactions depuis 2020')

# Fonction pour filtrer et grouper les transactions
def get_transactions_by_group(df, option_dep, option_year, group_by_col):
    return df.loc[(df.CP == option_dep) & (df.Year == str(option_year))].groupby(group_by_col).size().reset_index(name=f'Nombre de transactions en {option_year}')

# PAGE 1
if page == pages[0]:
    # Initialisation des options de session si elles n'existent pas
    if 'option_dep' not in st.session_state:
        st.session_state['option_dep'] = choix_dep[0]  # Valeur par défaut
    if 'option_date' not in st.session_state:
        st.session_state['option_date'] = choix_date[0]  # Valeur par défaut

    # Présentation du DataFrame global
    df_ventes = calculate_sales_by_value(df)
    st.dataframe(df_ventes)

    # Choix des dates et codes postaux pour affichage dynamique
    option_dep = st.selectbox("Choix du département à analyser", choix_dep, index=choix_dep.index(st.session_state['option_dep']))
    st.session_state['option_dep'] = option_dep

    option_date = st.selectbox("Choix de l'année à analyser", choix_date, index=choix_date.index(st.session_state['option_date']))
    st.session_state['option_date'] = option_date

    # Affichage des données depuis 2020
    st.write("Données pour le département :", option_dep, "depuis 2020.")
    df_ventes_dep = get_transactions_by_group(df, option_dep, '2020', 'Valeur')
    st.dataframe(df_ventes_dep)

    # Affichage du tableau de l'année choisie
    st.write("Transactions pour l'année :", option_date, "par valeurs.")
    df_ventes_dep_23 = get_transactions_by_group(df, option_dep, option_date, 'Valeur')
    st.dataframe(df_ventes_dep_23)

    # Affichage des transactions par commune
    st.write("Transactions pour l'année :", option_date, "par communes.")
    df_transac_communes = get_transactions_by_group(df, option_dep, option_date, 'Commune')
    df_transac_communes = df_transac_communes.sort_values(by=f'Nombre de transactions en {option_date}', ascending=False)
    st.dataframe(df_transac_communes)

    # Affichage de la progression
    if int(option_date) > 2020:  # Vérifie si l'année est supérieure à 2020
        st.write("Progression pour l'année :", option_date, "par communes.")

        # Groupement pour l'année sélectionnée
        df_year = get_transactions_by_group(df, option_dep, option_date, 'Commune')

        # Groupement pour l'année précédente
        previous_year = int(option_date) - 1
        df_year_minus = get_transactions_by_group(df, option_dep, previous_year, 'Commune')

        # Merge des DataFrames pour obtenir les transactions des deux années
        df_prog = df_year.merge(df_year_minus, on='Commune', how='inner', suffixes=('_current', '_previous'))

        # Renommer les colonnes pour plus de clarté
        df_prog.columns = ['Commune', f'Nombre de transactions en {option_date}', f'Nombre de transactions en {previous_year}']

        # Calcul de la progression
        df_prog['Progression en %'] = np.where(
            df_prog[f'Nombre de transactions en {previous_year}'] != 0,
            ((df_prog[f'Nombre de transactions en {option_date}'] - df_prog[f'Nombre de transactions en {previous_year}']) / 
             df_prog[f'Nombre de transactions en {previous_year}']) * 100,
            0  # Ou une autre valeur par défaut
        )

        df_prog['Progression en %'] = np.round(df_prog['Progression en %'], 0)
        df_prog = df_prog.loc[(df_prog[f'Nombre de transactions en {previous_year}'] >= 10) & (df_prog[f'Nombre de transactions en {option_date}'] >= 10)].sort_values(by='Progression en %')
        df_prog = df_prog.rename(columns={f'Nombre de transactions en {previous_year}': f'Nb transactions en {previous_year}',
                                  f'Nombre de transactions en {option_date}': f'Nb transactions en {option_date}'})
        df_prog = df_prog.sort_values(by='Progression en %', ascending=False)
        
        # Affichage du DataFrame avec progression
        st.dataframe(df_prog)



# PAGE 2
elif page == pages[1]:
    st.title("Adresses des biens vendus")

    # Vérifie si l'option a été sélectionnée dans Page 1
    if 'option_date' in st.session_state and 'option_dep' in st.session_state:
        st.write(f"Vous avez sélectionné l'année {st.session_state['option_date']} et le département {st.session_state['option_dep']}")
        option_date = st.session_state['option_date']
        option_dep = st.session_state['option_dep']

        # Transformation du dataframe pour affichage des transactions
        df_adresses = df.loc[(df.CP == option_dep) & (df.Year == option_date)].sort_values(by='Valeur fonciere', ascending=True)
        info_utiles = ['Valeur fonciere', 'Code postal', 'No voie', 'Voie', 'Commune']
        df_adresses['Valeur fonciere'] = np.round(df_adresses['Valeur fonciere'])

        # Affichage du dataframe
        st.dataframe(df_adresses[info_utiles].head(150))
    else:
        st.write("Aucune option sélectionnée sur la Page 1.")