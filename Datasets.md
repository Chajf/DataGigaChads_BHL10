# Used Datasets

**Possible Missions Dataset**
1. Spkid *[Int]*: Unique identifier (Small-Body Perturbation Kernel ID) for the asteroid.
2. Surname *[String]*: Catalogue name of the asteroid.
3. Name *[String]*: Common name of the asteroid (optional).
4. OCC *[Int]*: Orbit Condition Code (0 = well-determined; 9 = highly uncertain).
5. Diameter *[Float]*: Mean asteroid diameter (km).
6. TOF *[Float]*: Estimated time of flight to the asteroid (days).
7. Launch_date *[Date]*: Mission launch date.
8. Min_dv *[Float]*: Minimum required delta velocity (km/s).
9. Duration *[Int]*: Total mission duration (days).
10. Stay *[Int]*: Duration for mining operations at the asteroid (days).

Source: [researchgate.net/publication/359645905_ECOCEL_database_An_online_tool_for_asteroid_mission_planning](https://www.researchgate.net/publication/359645905_ECOCEL_database_An_online_tool_for_asteroid_mission_planning)

**Sets of multiple Spacecraft and Rockets**
1. Spacecraft *[String]*: Set of spacecraft IDs involved in the mission.
2. Rocket *[String]*: Identifier for the rocket used in the mission.
3. Total_Mass *[Float]*: Combined mass of the spacecraft and rocket (tons).
4. Storage_Capacity *[Float]*: Storage volume for extracted minerals (cubic meters).
5. Rocket_Lift_Price *[Float]*: Cost of launching the rocket from Earth ($M).
6. DeltaV_Cost *[Float]*: Cost per km/s of delta velocity ($M).

Source: *Generated with GPT-4o*