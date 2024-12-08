# Asteroid Miner

*Asteroids mining expeditions planer*

___

<div style="text-align: right"> Autorzy: Data GigaChads </div>

## Opis projektu

Celem projektu było przygotowanie systemu planowania misji kosmicznych mających na celu pozyskiwanie surowców z asteroid. Nieodłącznym elementem systemu było stworzenie modelu klasyfikacyjnego do rozpoznawania typów asteroid, co pozwalałoby na określenie które asteroidy są bogatsze w metale.

## Dane

Do projektu wykorzystano dane pochodzące z 3 źródeł:

1. [JPL Small-Body Database]() - zbiór asteoroidów i ich cech fizycznych.
2. [ECOCEL (Exploitation des Ressources des Corps Célestes)](https://www.researchgate.net/publication/359645905_ECOCEL_database_An_online_tool_for_asteroid_mission_planning) - zbiór zawierający dane na temat okien czasowych potencjalnych misji oraz wymaganych delta V dla każdej misji.
3. Syntetyczny zbiór wygenerowany przy pomocy GPT-4o z danmi dostępnych stataków i pjazdów kosmicznych.

## Modele predykcyjne

Do przygotowania modelu uczenia maszynowego przewidującego klasę asteroidy przeprowadzono screening następujących modeli:
 - Random Forest
 - Decision Tree
 - XGBoost
 - LightGBM
 - KNN
 - SVM
 - NB

Modele klasyfikują asteroidy na 2 klasy – typ M, bogaty w wartościowe surowce, a w drugiej klasie znajduje się reszta typów asteroid. 
Z powodu niezbilansowania klas wynikowych przeprowadzono upsampling metodą SMOTE do wyrównania liczebności obu klas.
Dodatkowo wykonano standaryzację.

Najlepszym modelem pod względem accuracy i recall okazał się XGBoost. Wykonano fine tuning metodą randomized search.

## System wieloagentowy

System wieloagentowy wykonany został w frameworku LangGraph z użyciem narzędzia LangChain do integracji dużych modeli językowych firm trzecich (w tym przypadku OpenAI model GPT-4o-mini).

System ten wykorzystuje koncepcję agentowości oddając znaczną część kontroli na temat wnioskowania agentom, a kwestia modelowania przenosi na specjalistyczne modele predykcyjne.

W centrum systemu znajduje koordynator planowania misji mający do dyspozycji 4 ekspertów dziedzinowych z kategorii: asteroid, zarządzania flotą, zarządzania czasem, zarządzania budżetem. Końcowym węzłem jest agent mający za zadanie przeprowadzenia wnioskowania na podstawie zebranych informacji z wywiadów i na tej podstawie opracowanie raportu.

System wzbogacony jest o podstawowe elementy RAG opierające się na pozyskiwaniu informacji z baz danych i wzbogacaniu nimi promptów dla bogatszego kontekstu.

Zaimplikowana została także mechanika pamięci w podstawowej formie polegającej na historii wiadomości pomiędzy agentami.

![](/images/agent_graph.png)

Pojedyncze wywołanie systemu (wykorzystując model GPT-4o-mini) wykorzystuje od 30k do 100k tokenów i w przeliczeniu kosztuje ~0.03$.

## Interfejs wizualny

Interfejs wizualny został zaprojektowany przy użyciu frameworku Streamlit, co zapewnia responsywność działania i przejrzystość.

Interfejs daje użytkownikowi możliwość skierowania zapytania do wspomnianego systemu wieloagentowego i do samodzielnego przeszukiwania bazy.

![](/images/chatbot_ui.png)

## Plany rozwoju

1. Rozwój modelu klasyfikacyjnego:

 - Rozszerzenie zbioru danych o nowe źródła (Gaia, LSST) i przyszłe misje kosmiczne.

 - Dodanie predykcji przyszłego składu asteroid przy użyciu modeli geochemicznych.

2. Udoskonalenie systemu wieloagentowego:

 - Rozbudowa funkcjonalności ekspertów (np. analiza ryzyk, optymalizacja trajektorii).

 - Zastosowanie pamięci długoterminowej i bardziej zaawansowanych mechanizmów RAG.

3. Ulepszenie interfejsu użytkownika:

 - Dodanie dynamicznych wizualizacji (mapy trajektorii, modele 3D asteroid).

 - Możliwość generowania raportów w popularnych formatach.

4. Komercjalizacja:

 - Współpraca z agencjami kosmicznymi i firmami prywatnymi.

 - Tworzenie modułów dedykowanych dla klientów komercyjnych.
