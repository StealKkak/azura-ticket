from services.dbService import *

from utils.arrayUtil import *

class TicketType:
    def __init__(self, guild, name: str, description: str, userClose: bool, dupTicket: bool, role: list, survey1: str = None, survey2: str = None, survey3: str = None, ticketCategory: str=None, closedTicketCategory: str=None, id=None, body: str=None, embed: str=None):
        self.__guild = guild
        self.__name = name
        self.__description = description
        self.__survey1 = survey1
        self.__survey2 = survey2
        self.__survey3 = survey3
        self.__role = arrayToString(role)
        self.__userClose = 1 if userClose else 0
        self.__dupTicket = 1 if dupTicket else 0
        self.__ticketCategory = ticketCategory
        self.__closedTicketCategory = closedTicketCategory
        self.body = body
        self.embed = embed
        self.__id = id

    @property
    def id(self):
        return self.__id

    @property
    def guild(self):
        return self.__guild
    
    @property
    def name(self):
        return self.__name
    
    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def description(self):
        return self.__description
    
    @description.setter
    def description(self, value):
        self.__description = value

    @property
    def survey1(self):
        return self.__survey1

    @property
    def survey2(self):
        return self.__survey2
    
    @property
    def survey3(self):
        return self.__survey3
    
    @survey1.setter
    def survey1(self, value):
        self.__survey1 = value

    @survey2.setter
    def survey2(self, value):
        self.__survey2 = value

    @survey3.setter
    def survey3(self, value):
        self.__survey3 = value

    @property
    def dupTicket(self):
        return bool(self.__dupTicket)
    
    @dupTicket.setter
    def dupTicket(self, value: bool):
        self.__dupTicket = 1 if value else 0

    @property
    def role(self):
        array = stringToArray(self.__role)
        newArr = []
        for item in array:
            newArr.append(int(item))
        return newArr
    
    @role.setter
    def role(self, value: list=None):
        self.__role = arrayToString(value)

    @property
    def userClose(self):
        return bool(self.__userClose)
    
    @userClose.setter
    def userClose(self, value: bool):
        self.__userClose = 1 if value else 0

    @property
    def ticketCategory(self):
        return self.__ticketCategory
    
    @ticketCategory.setter
    def ticketCategory(self, value):
        self.__ticketCategory = value

    @property
    def closedTicketCategory(self):
        return self.__closedTicketCategory
    
    @closedTicketCategory.setter
    def closedTicketCategory(self, value):
        self.__closedTicketCategory = value

    async def save(self):
        if not self.__name:
            raise NameError("name is required!")
        
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE guild = ? AND name = ? AND id != ?", (self.__guild, self.__name, self.__id))
        exists = await cur.fetchone()
        
        if exists:
            await closeDB(con, cur)
            raise ValueError("A record with the same guild and name already exists.")
        
        await cur.execute("UPDATE ticket_settings SET name = ?, description = ?, survey1 = ?, survey2 = ?, survey3 = ?, role = ?, user_close = ?, dup_ticket = ?, ticket_category = ?, closed_ticket_category = ?, body = ?, embed = ? WHERE id = ?", (self.__name, self.__description, self.__survey1, self.__survey2, self.__survey3, self.__role, self.__userClose, self.__dupTicket, self.__ticketCategory, self.__closedTicketCategory, self.body, self.embed, self.__id,))
        await con.commit()
        await closeDB(con, cur)

    async def delete(self):
        con, cur = await loadDB()
        await cur.execute("DELETE FROM ticket_settings WHERE guild = ? AND name = ?", (self.__guild, self.__name))
        await con.commit()
        await closeDB(con, cur)

    @staticmethod
    async def createInstance(guild, name: str, description: str, userClose: bool, dupTicket: bool, role: list, survey1: str = None, survey2: str = None, survey3: str = None, ticketCategory:str = None, closedTicketCategory:str = None, body:str = None, embed:str = None):
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE guild = ? AND name = ?", (guild, name))
        exists = await cur.fetchone()
        if exists:
            await closeDB(con, cur)
            raise ValueError("A record with the same guild and name already exists.")
        
        await cur.execute("INSERT INTO ticket_settings (guild, name, description, survey1, survey2, survey3, role, user_close, dup_ticket, ticket_category, closed_ticket_category, body, embed) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (guild, name, description, survey1, survey2, survey3, arrayToString(role), 1 if userClose else 0, 1 if dupTicket else 0, ticketCategory, closedTicketCategory, body, embed))
        await con.commit()
        id = cur.lastrowid
        await closeDB(con, cur)
        return TicketType(guild, name, description, userClose, dupTicket, role, survey1, survey2, survey3, ticketCategory, closedTicketCategory, id)

    @staticmethod
    async def findByGuildIdAndName(guildId, name) -> "TicketType":
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE guild = ? AND name = ?", (guildId, name))
        row = await cur.fetchone()
        await closeDB(con, cur)

        if not row:
            return None
        
        return TicketType(row["guild"], row["name"], row["description"], bool(row["user_close"]), row["dup_ticket"], stringToArray(row["role"]), row["survey1"], row["survey2"], row["survey3"], row["ticket_category"], row["closed_ticket_category"], row["id"], row["body"], row["embed"])
    
    @staticmethod
    async def findByGuildId(guildId) -> list["TicketType"]:
        result = []

        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE guild = ?", (guildId,))
        rows = await cur.fetchall()
        await closeDB(con, cur)
        
        for row in rows:
            result.append(TicketType(row["guild"], row["name"], row["description"], bool(row["user_close"]), row["dup_ticket"], stringToArray(row["role"]), row["survey1"], row["survey2"], row["survey3"], row["ticket_category"], row["closed_ticket_category"], row["id"], row["body"], row["embed"]))
        
        return result
    
    @staticmethod
    async def findById(id) -> "TicketType":
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE id = ?", (id,))
        row = await cur.fetchone()
        await closeDB(con, cur)

        return TicketType(row["guild"], row["name"], row["description"], bool(row["user_close"]), row["dup_ticket"], stringToArray(row["role"]), row["survey1"], row["survey2"], row["survey3"], row["ticket_category"], row["closed_ticket_category"], row["id"], row["body"], row["embed"]) if row else None