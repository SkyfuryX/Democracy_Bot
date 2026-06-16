from typing import Optional
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
 
class HelldiversBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    ) 

#General Statistics   
class Stats(HelldiversBase):
    missions_won: int
    missions_lost: int
    mission_time: int
    terminid_kills: int
    automaton_kills: int
    illuminate_kills: int
    bullets_fired:int
    bullets_hit: int
    deaths: int
    friendlies: int
    mission_success_rate: int
    player_count: int 
        
    async def killsCombined(self):
        return self.terminid_kills + self.automaton_kills + self.illuminate_kills

#Planet Classes    
class Biome(HelldiversBase):
    name: str
    description: str

class Location(HelldiversBase):
    health: int
    max_health: int
        
    async def currentHealth(self):
        return round(self.health / self.max_health, 4)

class Event(Location):
    event_type: int
    faction: str
    start_time: str
    end_time: str
    campaign_id: int
    joint_operation_ids: Optional[list[int]] = None


class Position(HelldiversBase):
    x: float
    y: float

class Region(HelldiversBase):
    id: int
    hash: int
    name:str
    description: Optional[str] = None
    size: str
    regen_per_second: float
    availability_factor: float
    is_available: bool
    players: int
    
    def __str__(self):
        return f"Region({self.name})"

class Planet(Location):
    index: int
    name:str
    sector: str
    biome: Biome
    hazards: list[Biome]
    hash: int
    position: Position
    waypoints: list[int]
    disabled: bool
    initial_owner: str
    current_owner: str
    regen_per_second: float
    event: Optional[Event] = None
    statistics: Stats
    attacking: list[int]
    regions:  list[Region]
    id: str
        
    def __str__(self):
        return f"Planet({self.name})"
    
#Order classes   
class Reward(HelldiversBase):
    type: int
    amount: int

class Task(HelldiversBase):
    type: int
    values: list[int]
    value_types: list[int]

class Order(HelldiversBase):
    id: int
    progress: list[int]
    title: str
    briefing: str
    description: Optional[str] = None
    tasks:  list[Task]
    reward: Reward
    rewards: list[Reward]
    expiration: str
    flags: int