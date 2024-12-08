import streamlit as st
from Config import Config
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
from datetime import date, timedelta
import pandas as pd
import sqlite3
import numpy as np
from agent_funs import invoke_graph

# Połączenie z bazą danych SQLite
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Pobieranie danych z tabel w bazie
query = "SELECT * FROM FLEET;"
FLEET = pd.read_sql_query(query, conn)
query = "SELECT * FROM ROCKETS;"
SPACECRAFTS = pd.read_sql_query(query, conn)
query = "SELECT * FROM SPACECRAFTS;"
ROCKETS = pd.read_sql_query(query, conn)
query = "SELECT * FROM ASTEROIDS;"
MISSIONS = pd.read_sql_query(query, conn)
MISSIONS["Launch_date"] = pd.to_datetime(MISSIONS["Launch_date"]).dt.date
# Ładowanie konfiguracji
load_dotenv()
openai_api_key = Config.OPENAI_API_KEY

# Ustawienie konfiguracji strony
st.set_page_config(page_title="Space Bot")

# Menu boczne
with st.sidebar:
    selected_option = option_menu("Main Menu", ["ChatBot", "Sliders"], default_index=0)

# Tytuł aplikacji
st.title("Asteroid Miner")

if selected_option == "ChatBot":
    # Inicjalizacja historii wiadomości
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Wyświetlanie historii wiadomości
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    import time  # Import the time module for sleep

    if prompt := st.chat_input(""):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Add "model is thinking" animation
        thinking_message = st.chat_message("assistant")
        thinking_placeholder = thinking_message.empty()

        animation_frames = ["💭", "💭.", "💭..", "💭..."]  # Define animation frames


        def animate_thinking(placeholder, duration=200):
            """Show animated 'thinking' for a given duration."""
            start_time = time.time()
            while time.time() - start_time < duration:
                for frame in animation_frames:
                    placeholder.markdown(f"_Model is thinking_ {frame} ")
                    time.sleep(0.3)  # Adjust speed of animation


        # Start the animation in a separate process (if needed, simulate delay here)
        animate_thinking(thinking_placeholder, duration=2)

        # Simulating streaming of response in chunks
        response_chunks = []  # Replace this with streaming from your model
        response = invoke_graph(prompt)  # Call your model or logic here
        response_text = response.get("messages")[-1]  # Extract full response text

        # Stream response in chunks
        for chunk in response_text.split(" "):  # Example: Split by words as chunks
            response_chunks.append(chunk)
            response_stream = " ".join(response_chunks)
            thinking_placeholder.markdown(response_stream)
            time.sleep(0.03)  # Add delay for realistic streaming effect

        # Once streaming is done, finalize response
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        thinking_placeholder.markdown(response_text)  # Replace placeholder with final response

else:
    # Zakres daty
    start_date = date(2023, 1, 1)
    end_date = date(2024, 12, 31)

    # Opcje do wyboru
    options = ["Launch_date", "OCC", "Diameter", "TOF", "Min_dv", "Duration", "Stay", "Storage_Capacity", "DeltaV_Cost", "Rocket_Lift_Price"]

    # Wybór opcji do filtrowania
    selected_options = st.multiselect("Wybierz opcje:", options)

    # Dynamiczne generowanie suwaków dla wybranych opcji
    ranges = {}
    dataframes = [FLEET, ROCKETS, SPACECRAFTS, MISSIONS]
    dataframe_names = ["FLEET", "ROCKETS", "SPACECRAFTS", "MISSIONS"]
    filtered_dfs = {"FLEET": FLEET, "ROCKETS": ROCKETS, "SPACECRAFTS": SPACECRAFTS, "MISSIONS": MISSIONS}

    for option in selected_options:
        min_val = None
        max_val = None
        df_found = None  # Zmienna, która przechowa nazwę ramki, gdzie znajduje się kolumna

        # Sprawdzanie, w której ramce danych jest kolumna i obliczanie minimalnych i maksymalnych wartości
        for df, df_name in zip(dataframes, dataframe_names):
            if option in df.columns:
                df_found = df_name
                if pd.api.types.is_datetime64_any_dtype(df[option]):
                    # Jeżeli kolumna jest typu datetime, ustawiamy przedział dat
                    current_min = df[option].min()
                    current_max = df[option].max()
                    # Ustawiamy wartości na suwaku jako daty
                    if min_val is None or current_min < min_val:
                        min_val = current_min
                    if max_val is None or current_max > max_val:
                        max_val = current_max
                else:
                    # Dla innych kolumn, traktujemy je jako liczby
                    current_min = df[option].min()
                    current_max = df[option].max()
                    if min_val is None or current_min < min_val:
                        min_val = current_min
                    if max_val is None or current_max > max_val:
                        max_val = current_max

        if min_val is not None and max_val is not None:
            # Wyświetlenie informacji o tym, w której ramce danych znajduje się kolumna
            # st.write(f"Kolumna `{option}` znajduje się w ramce danych: {df_found}")
            
            # Generowanie suwaka dla kolumny
            if isinstance(min_val, date):  # Sprawdzamy, czy to kolumna z datami
                ranges[option] = st.slider(
                    f"Ustaw przedział dla {option}:",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val),  # Domyślny przedział
                    format="YYYY-MM-DD"
                )
            else:
                ranges[option] = st.slider(
                    f"Ustaw przedział dla {option}:",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val)  # Domyślny przedział
                )

            # Filtrowanie tylko ramki, w której kolumna istnieje
            for df_name in dataframe_names:
                if df_name == df_found:
                    filtered_df = filtered_dfs[df_name]
                    if pd.api.types.is_datetime64_any_dtype(filtered_df[option]):
                        filtered_df = filtered_df[(filtered_df[option] >= ranges[option][0]) & (filtered_df[option] <= ranges[option][1])]
                    else:
                        filtered_df = filtered_df[(filtered_df[option] >= ranges[option][0]) & (filtered_df[option] <= ranges[option][1])]
                    filtered_dfs[df_name] = filtered_df
                # else:
                #     # print(df_name)
                #     filtered_dfs[df_name] = df.copy()

    # Przycisk do generowania nowych ramek danych
    if st.button("Generuj ramki"):

        # # st.write()
        #
        # filtered_fleet = filtered_dfs['FLEET']
        # filtered_rockets = filtered_dfs['ROCKETS']
        # filtered_spacecraft = filtered_dfs['SPACECRAFTS']
        # filtered_asteroids = filtered_dfs['ASTEROIDS']
        #
        # st.dataframe(filtered_fleet)
        # st.dataframe(filtered_rockets)
        # st.dataframe(filtered_spacecraft)
        # st.dataframe(filtered_asteroids)
        # #
        # df1 = filtered_asteroids.copy()
        # sizes = []
        # for i in range(len(df1)):
        #     row = df1.iloc[i]
        #     size = 4/3 * np.pi * pow((row['Diameter']/2 * 10_000),3) * 0.035 #0.8 for M, 0.15 for S, 0.035 for C
        #     sizes.append(size)
        # #
        # st.write(np.max(sizes))
        # st.write(np.min(sizes))
        # df1.drop(columns=['Spkid', 'Min_dv', 'Diameter', 'TOF', 'Stay'], inplace=True)
        # st.dataframe(df1.iloc[0])

        # Wyświetlanie nowych ramek danych w pamięci
        for df_name, filtered_df in filtered_dfs.items():
            filtered_table_name = f"{df_name}_filtered"
            st.write(f"Przefiltrowana ramka danych {df_name}:")
            st.dataframe(filtered_df)

            # Potwierdzenie
            # st.success(f"Tabela `{filtered_table_name}` została utworzona w pamięci!")
