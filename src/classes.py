class Location:
    def __init__(self, name, health, maxHealth):
        self.name = name
        self.health = health
        self.maxHealth = maxHealth
        
    async def currentHealth(self):
        return round(self.health / self.maxHealth, 4)
    
class Stats:
    def __init__(self, success, failed, terminid, automaton, illuminate, fired, hit, deaths, accidentals, players):
        self.success = success
        self.failed = failed
        self.terminid = terminid
        self.automaton = automaton
        self.illuminate = illuminate
        self.fired = fired 
        self.hit = hit
        self.deaths = deaths
        self.accidentals = accidentals
        self.players = players
        
    def __repr__(self):
        return f"Stats({self.success}, {self.failed}, {self.terminid}, {self.automaton}, {self.illuminate}, {self.fired}, {self.hit}, {self.deaths}, {self.accidentals}, {self.players})"
        
    async def killsCombined(self):
        return self.terminid + self.automaton + self.illuminate
    
class Region(Location):
    async def __init__(self, name, description, health, maxHealth, size, players):
        super().__init__(name, health, maxHealth)
        self.description = description
        self.size = size
        self.players = players
        
    def __repr__(self):
        return f"Region({self.name}, {self.description}, {self.health}, {self.maxHealth}, {self.size}, {self.players})"
        
class Planet(Location):
    async def __init__(self, name, sector, biome, hazards, waypoints, health, maxHealth, owner, stats, regions):
        super().__init__(name, health, maxHealth)
        self.sector = sector
        self.biome = biome
        self.hazards = hazards
        self.waypoints = waypoints
        self.owner = owner
        self.stats = await self.addStats(stats)
        self.regions = await self.createRegions(regions)
        
    def __str__(self):
        return f"Planet({self.name})"
    
    def __repr__(self):
        return f"Planet({self.name}, {self.sector}, {self.biome}, {self.hazards}, {self.waypoints}, {self.health}, {self.maxHealth}, {self.owner}, {self.regions}, {self.stats})"
        
    async def createRegions(regions):
        return [Region(region["name"], region['description'], region['health'], region["maxHealth"], region["size"],region["players"]) for region in regions]
   
    async def addStats(stats):
        return Stats(stats["missionsWon"],
                     stats["missionsLost"],
                     stats["terminidKills"],
                     stats["automatonKills"],
                     stats["illuminateKills"],
                     stats["bulletsFired"],
                     stats["bulletsHit"],
                     stats["deaths"],
                     stats["friendlies"],
                     stats["playerCount"])