from typing import List, Literal, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, AnyMessage
from langgraph.graph.message import add_messages
import operator
from langchain_openai import ChatOpenAI
import os, getpass
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display
from langgraph.checkpoint.memory import MemorySaver


def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")
_set_env("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "BHL10"

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class MissionState(TypedDict):
    next_action: Literal["spacecraft_action","time_action","cost_action","asteroids_action","summary_action"] = Field(description="Next action to execute in mission planning phase")
    asteroids: Annotated[list, operator.add] = Field(description = "Potential destinations for mission")
    spacecraft: Annotated[list, operator.add] = Field(description = "List of potential spacecrafts for mission")
    time: Annotated[list, operator.add] = Field(description="List of insights for time perspectives of mission based on asteroids and spacecrafts data")
    cost: Annotated[list, operator.add] = Field(description="List of insights for costs and profits of mission based on asteroids and spacecrafts data")
    budget_analysis: str = Field(description="Analysis of budget")
    timeline_analysis: str = Field(description="Analysis of timeline")
    messages: Annotated[list, operator.add]
    table: str

class MissionState2(TypedDict):
    next_action: Literal["spacecraft_action","time_action","cost_action","asteroids_action","summary_action"] = Field(description="Next action to execute in mission planning phase")
    messages: str = Field(description="Your question to experts about specific informations")

class CostState(TypedDict):

    cost: list = Field(description="List of insights for costs and profits of mission based on asteroids and spacecrafts data")
    budget_analysis: str

class TimeState(TypedDict):
    time: list = Field(description="List of insights for time perspectives of mission based on asteroids and spacecrafts data")
    timeline_analysis: str

class text2sqlState(TypedDict):
    next_action: Literal["mission_planner","text2sql"] = Field(description="Next action to execute in mission planning phase")
    asteroids: list = Field(description = "Potential destinations for mission")
    spacecraft: list = Field(description = "List of potential spacecrafts for mission")
    time: list = Field(description="Time windows to start mission")
    messages: str
    table: str

import re
import sqlite3

text2sql_prompt_asteroid = """You are expert in writing sql queries for retrieving most well fited dataset to user query.

Use {table}. Limit answers to 5 rows.

{table} schema:

Spkid INTEGER NOT NULL -- Small-Body Perturbation Kernel Identifier.
Surname TEXT NOT NULL -- Catalogue Name of Asteroid.
Name TEXT -- Common Name of Asteroid (not everyone has it).
OCC INTEGER NOT NULL -- Orbit condition code, defines the asteroid’s orbit accuracy where 0 implies a well-determined orbit and 9 implies a very poorly-determined (highly uncertain) orbit.
Diameter REAL NOT NULL -- Mean Diameter in kilometers.
TOF REAL NOT NULL -- Time Of Flight to asteroid estimated for mission.
Launch_date DATE NOT NULL -- Date of Launch for mission.
Min_dv REAL NOT NULL -- Minimal requirement delta of Velocity.
Duration INTEGER NOT NULL -- Expected Duration of a whole mission.
Stay INTEGER NOT NULL -- How many days can mission stay for mining at asteroid.
spec_T TEXT NOT NULL -- Numeric/Text - Numeric values indicate probability of a most value asteroid type (M type), "Other" indicates high probability for a different type.

User message:
{message}

Extract Name, OCC, Diameter, TOF, Launch_date, Min_dv, Duration, Stay, Class"""

text2sql_prompt_spacecraft = """You are expert in writing sql queries for retrieving most well fited dataset to user query.

Use tables `fleet`, `rockets`, `spacecrafts`. Limit answers to 5 rows.

fleet schema:

Spacecraft TEXT NOT NULL -- Set of spacecraft IDs in mission.
Rocket TEXT NOT NULL -- Rocket ID.
Total_Mass REAL NOT NULL -- Mass of a whole set with rocket.
Storage_Capacity REAL NOT NULL -- Volume of storage for extracted minerals.
Rocket_Lift_Price REAL NOT NULL -- price of lifting rocket from Earth.
DeltaV_Cost REAL NOT NULL -- Cost per km/s delta velocity.
Mining_Capability -- How much volume can spacecraft extract per day.
On_Mission -- Are spacecraft currently on mission.

rockets schema:

Type -- Type of rocket.
Mass -- Mass of rocket.
Capacity -- Max weight possible to lift by rocket.
ID -- ID of rocket type.

spacecrafts schema:

Type -- Type of spacecraft.
Mass -- Mass of spacecraft.
Capacity -- Max volume possible to carry by spacecraft.
ID -- ID of spacecraft type.

User message:
{message}

Extract Spacecraft, Rocket, Total_Mass, Storage_Capacity, Rocket_Lift_Price, DeltaV_Cost, Mining_Capability, On_Mission"""

from datetime import datetime

planner_prompt = """Role Description:
You are an expert in planning asteroid mining missions. Your primary objective is to design the best possible mission scenarios that minimize risk of failure while maximizing profit through optimal time and cost management.

Capabilities and Actions:
You can perform the following actions:

1. Gather Information: Request and receive detailed input from domain experts in specific fields.
2. Create Mission Summary: Compile and synthesize the gathered information into comprehensive mission scenarios.

Resources at Your Disposal:
You have access to four domain experts, each specializing in a key area:

1. Spacecraft Manager: Provides details on spacecraft design, functionality, and limitations.
2. Cost Planner: Supplies insights into budget allocations, expenses, and cost-saving opportunities.
3. Time Planner: Offers strategies for scheduling and minimizing delays.
4. Asteroid Expert: Delivers critical data on asteroid type, trajectories, and mining potential.

Follow these guidelines:

- Always start from gathering information about asteroids and spacecraft fleet.
- You must gather information from all four experts to develop a complete mission summary.
- Once you determine you have sufficient details from one field, move on to the next expert until all necessary data is collected.
- DON'T ask one expert two times in a row. DON'T ask any expert more than two times.
- If you are asked by expert to provide more information, try to gather it from other experts if it is possible.
- Use this comprehensive knowledge to formulate mission scenarios that optimize risk, cost, and time considerations.

Current Asteroid Information:
{asteroids}

Current Spacecraft Infromation:
{spacecraft}
"""

def planner(state: MissionState):
    structured_llm = llm.with_structured_output(MissionState2)
    if len(state["asteroids"]) >=1:
        list_asteroids = "\n".join(state["asteroids"])
    else:
        list_asteroids = []
    if len(state["spacecraft"]) >=1:
        list_spacecraft = "\n".join(state["spacecraft"])
    else:
        list_spacecraft = []
    planner_complete = planner_prompt.format(asteroids=list_asteroids, spacecraft = list_spacecraft)
    action = structured_llm.invoke([SystemMessage(content=planner_complete)]+state["messages"])
    return {"next_action": action["next_action"],
            "messages":[action["messages"]],
            }


asteroids_prompt = """Role Description:
You are an expert in asteroid science and exploration. Your goal is to provide accurate, data-driven insights about specific asteroid objects using the information available in the database.

Instructions:

1. Query the Database:

- Query the database only once to retrieve information about the asteroid objects.
- Use the table named asteroids to perform the query.

2. Formulate Your Query:

- Craft a clear query specifying the types of asteroids or the information you want to extract.

3. Only if informations are gathered return to mission planner.
"""

def asteroids_expert(state: MissionState):
    structured_llm = llm.with_structured_output(text2sqlState)
    list_asteroids = "\n".join(state["asteroids"])
    asteroids_complete = asteroids_prompt.format(asteroids=list_asteroids)
    answer = structured_llm.invoke([SystemMessage(content=asteroids_complete)]+[state["messages"][-1]])
    if answer["next_action"]=="mission_planner":
        return {"next_action":answer["next_action"],"messages":[list_asteroids]}
    else:
        return {"next_action":answer["next_action"],"table":answer["table"],"messages":[answer["messages"]]}

def text2sql(state: text2sqlState):
    table = state["table"]
    message = state["messages"][-1]
    if table == "asteroids":
        text2sql_complete = text2sql_prompt_asteroid.format(table=table,message=message)
        code = llm.invoke(text2sql_complete)
        match = match = re.search(r"```.*?\n(.*?)\n```", code.content, re.DOTALL)
        sql_code = match.group(1)
        conn = sqlite3.connect("database2.db")
        cursor = conn.cursor()
        cursor.execute(sql_code)
        ans = cursor.fetchall()
        conn.close()

        formatted_data = []
        for row in ans:
            name, occ, diameter, tof, launch_date, min_dv, duration, stay, asteroid_class = row
            formatted_data.append(f"""- Name: {name if name else "Unknown"}
- Orbit Condition Code (OCC): {occ}
- Diameter: {diameter:.2f} km
- Time of Flight (TOF): {tof:.1f} days
- Launch Date: {datetime.strptime(launch_date, '%Y-%m-%d %H:%M:%S').date()}
- Minimal Delta-V (Min_dv): {min_dv:.2f} km/s
- Mission Duration: {duration} days
- Mining Stay: {stay} days
- Class: {asteroid_class}

""")
        return {"asteroids":formatted_data, "next_action":"asteroids_action", "messages":["\n".join(formatted_data)]}
    if table=="fleet":
        text2sql_complete = text2sql_prompt_spacecraft.format(message=message)
        code = llm.invoke(text2sql_complete)
        match = match = re.search(r"```.*?\n(.*?)\n```", code.content, re.DOTALL)
        sql_code = match.group(1)
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(sql_code)
        ans = cursor.fetchall()
        conn.close()

        formatted_data = []
        for row in ans:
            spacecraft, rocket, total_mass, sorage_capacity, rocket_lift_price, deltav_cost, mining_capability, on_mission = row
            formatted_data.append(f"""- Spacecraft: {spacecraft}
- Rocket: {rocket}
- Total Mass: {total_mass} t
- Storage Capacity: {sorage_capacity} dcm3
- Rocket Lift Price: {rocket_lift_price} $M
- Delta-V cost: {deltav_cost} $M
- Mining capability: {mining_capability} dcm3/day
- Space craft on mission: {on_mission}

""")
        return {"spacecraft":formatted_data, "next_action":"spacecraft_action", "messages":["\n".join(formatted_data)]}

spacecraft_prompt = """Role Description:
You are a management expert specializing in spacecraft fleet operations. Your goal is to provide insights on the most relevant spacecraft that can be utilized for asteroid mining missions, based on the available database information.

Instructions:

1. Query the Database:

- Query the database only once to retrieve information about the spacecraft.
- Use the table named fleet to perform the query.

2. Formulate Your Query:

- Create a specific and clear query about the spacecraft you wish to extract information on, considering the mission requirements.

3. Only if informations are gathered return to mission planner.

Asteroid List for Reference:
{asteroids}
"""

def spacecraft_manager(state: MissionState):
    structured_llm = llm.with_structured_output(text2sqlState)
    list_asteroids = "\n".join(state["asteroids"])
    list_spacecraft = "\n".join(state["spacecraft"])
    spacecraft_complete = spacecraft_prompt.format(asteroids=list_asteroids)
    answer = structured_llm.invoke([SystemMessage(content=spacecraft_complete)]+[state["messages"][-1]])
    if answer["next_action"]=="mission_planner":
        return {"next_action":answer["next_action"],"messages":[list_spacecraft]}
    else:
        return {"next_action":answer["next_action"],"table":answer["table"],"messages":[answer["messages"]]}

time_prompt = """Role Description:
You are an expert in time planning for asteroid mining missions. Your primary objective is to develop an optimized mission timeline based on the provided information about asteroids and spacecraft.

Instructions:

1. Analyze Provided Data:

- Use the given details about asteroids and spacecraft to construct a timeline for the mission.
- Consider factors such as travel time, mission phases, and operational constraints.

2. Develop the Timeline:

- Create a detailed, step-by-step timeline that aligns with mission objectives, ensuring time efficiency and minimizing delays.

Only use provided data:

Asteroids:
{asteroids}

Spacecraft:
{spacecrafts}
"""

def time_planner(state: MissionState):
    time_complete = time_prompt.format(asteroids=state["asteroids"], spacecrafts = state["spacecraft"])
    structured_llm = llm.with_structured_output(TimeState)
    answer = structured_llm.invoke([SystemMessage(content=time_complete)]+[state["messages"][-1]])
    return{"messages":[answer["timeline_analysis"]], "time":answer["time"], "timeline_analysis": answer["timeline_analysis"]}

cost_prompt = """Role Description:
You are an expert in financial planning for asteroid mining missions. Your primary goal is to evaluate the costs and potential revenues of the mission based on the provided information about asteroids and spacecraft.

Instructions:

1. Analyze Provided Data:

- Use the given details about asteroids and spacecraft to estimate mission costs and potential revenues.
- Consider factors such as operational expenses, transportation costs, resource extraction, and market value of mined materials.

2. Provide Financial Analysis:

- Break down the costs into categories such as spacecraft operation, mission duration, and asteroid processing.
- Estimate the revenues based on the value and marketability of the resources available on the asteroid.
- Present a clear summary of the financial viability of the mission.

Only use provided data:

Asteroids:
{asteroids}

Spacecraft:
{spacecrafts}
"""

def cost_planner(state: MissionState):
    cost_complete = cost_prompt.format(asteroids=state["asteroids"], spacecrafts = state["spacecraft"])
    structured_llm = llm.with_structured_output(CostState)
    answer = structured_llm.invoke([SystemMessage(content=cost_complete)]+[state["messages"][-1]])
    return{"messages":[answer["budget_analysis"]], "cost":[answer["cost"]], "budget_analysis":answer["budget_analysis"]}

summary_prompt = """Role Description:
You are a summarization expert tasked with creating a comprehensive mission overview for asteroid mining. Your goal is to synthesize all gathered information into a clear, concise summary.

Instructions:

1. Use Provided Data Only:
Base your summary solely on the information contained in the following state variables:

Asteroids: Potential destinations for the mission.

{asteroids}

Spacecraft: List of spacecraft options.

{spacecraft}

Time: Insights on the mission timeline.

{time}

Cost: Financial analysis including costs and profits.

{cost}

Budget Analysis: Overall budget evaluation.

{budget}

Timeline Analysis: Detailed review of the mission timeline.

{timeline}

2. Create a Detailed Summary:

Include the following key points:

- The chosen asteroid for the mission.
- The selected spacecraft to be used.
- A breakdown of the mission timeline based on the time insights and timeline analysis.
- A summary of costs and profits derived from the financial data and budget analysis.

3. Present the Summary:

Ensure the summary is clear, logical, and concise, providing a complete overview of the planned mission."""

def mission_summary(state: MissionState):
    summary_complete = summary_prompt.format(asteroids=state["asteroids"],
                                             spacecraft = state["spacecraft"],
                                             time = state["time"],
                                             cost = state["cost"],
                                             budget = state["budget_analysis"],
                                             timeline = state["timeline_analysis"])
    summary = llm.invoke([SystemMessage(content=summary_complete)]+[HumanMessage(content="Write a summary for my mission.")])
    return {"messages":[summary.content]}

def main_stage_condition(state: MissionState):
    action = state["next_action"]
    if action=="asteroids_action":
        return "asteroids_expert"
    if action=="spacecraft_action":
        return "spacecraft_manager"
    if action=="cost_action":
        return "cost_planner"
    if action=="time_action":
        return "time_planner"
    if action=="summary_action":
        return "mission_summary"
    
def text2sql_condition_return(state: MissionState):
    action = state["next_action"]
    if action=="asteroids_action":
        return "asteroids_expert"
    if action=="spacecraft_action":
        return "spacecraft_manager"
    
def text2sql_condition(state: MissionState):
    action = state["next_action"]
    if action=="text2sql":
        return "text2sql"
    else:
        return "mission_planner"
    
# def build_graph():
    # Graph
builder = StateGraph(MissionState)

# Define nodes: these do the work
builder.add_node("mission_planner",planner)
builder.add_node("spacecraft_manager",spacecraft_manager)
builder.add_node("time_planner",time_planner)
builder.add_node("cost_planner",cost_planner)
builder.add_node("text2sql",text2sql)
builder.add_node("asteroids_expert",asteroids_expert)
builder.add_node("mission_summary",mission_summary)

# Define edges: these determine how the control flow moves
builder.add_edge(START, "mission_planner")
builder.add_conditional_edges("mission_planner",main_stage_condition,["spacecraft_manager","time_planner","cost_planner","mission_summary","asteroids_expert"])
builder.add_conditional_edges("asteroids_expert",text2sql_condition,["text2sql","mission_planner"])
builder.add_conditional_edges("spacecraft_manager",text2sql_condition,["text2sql","mission_planner"])
builder.add_conditional_edges("text2sql",text2sql_condition_return,["asteroids_expert","spacecraft_manager"])
builder.add_edge("time_planner","mission_planner")
builder.add_edge("cost_planner","mission_planner")
builder.add_edge("mission_summary",END)

memory = MemorySaver()
react_graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "4"}}

def invoke_graph(message: str):
    x = react_graph.invoke({"messages":[message],"next_action":"","timeline_analysis":"","budget_analysis":""},config)
    return x
