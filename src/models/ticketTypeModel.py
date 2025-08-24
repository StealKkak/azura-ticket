from services.dbService import *

from utils.arrayUtil import *

class TicketType:
    def __init__(self, guild, name: str, userClose: bool, maxTicket: int, role: list, survey1: str = None, survey2: str = None, survey3: str = None, ticketCategory: str=None, closedTicketCategory: str=None, id=None):
        self.__guild = guild
        self.__name = name
        self.__survey1 = survey1
        self.__survey2 = survey2
        self.__survey3 = survey3
        self.__role = arrayToString(role)
        self.__userClose = 1 if userClose else 0
        self.__maxTicket = maxTicket
        self.__ticketCategory = ticketCategory
        self.__closedTicketCategory = closedTicketCategory
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
        self.__name == value

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
    def maxTicket(self):
        return self.__maxTicket
    
    @maxTicket.setter
    def maxTicket(self, value: int):
        self.__maxTicket = value

    @property
    def role(self):
        return stringToArray(self.__role)
    
    @role.setter
    def role(self, value: list=None):
        self.__role = arrayToString(value)

    @property
    def userClose(self):
        return bool(self.__userClose)
    
    @userClose.setter
    def userClose(self, value: bool):
        self.__userClose = 1 if value else None

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
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE guild = ? AND name = ? AND id != ?", (self.__guild, self.__name, self.__id))
        exists = await cur.fetchone()
        
        if exists:
            await closeDB(con, cur)
            raise ValueError("A record with the same guild and name already exists.")
        
        await cur.execute("UPDATE ticket_settings SET name = ?, survey1 = ?, survey2 = ?, survey3 = ?, role = ?, user_close = ?, max_ticket = ?, ticket_category = ?, closed_ticket_category = ?", (self.__name, self.__survey1, self.__survey2, self.__survey3, self.__role, 1 if self.__userClose else 0, self.__maxTicket if self.__maxTicket else 0, self.__ticketCategory, self.__closedTicketCategory))
        await con.commit()
        await closeDB(con, cur)

    async def delete(self):
        con, cur = await loadDB()
        await cur.execute("DELETE FROM ticket_settings WHERE guild = ? AND name = ?", (self.__guild, self.__name))
        await con.commit()
        await closeDB(con, cur)

    @staticmethod
    async def createInstance(guild, name: str, userClose: bool, maxTicket: int, role: list, survey1: str = None, survey2: str = None, survey3: str = None, ticketCategory:str = None, closedTicketCategory:str = None):
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE guild = ? AND name = ?", (guild, name))
        exists = await cur.fetchone()
        if exists:
            await closeDB(con, cur)
            raise ValueError("A record with the same guild and name already exists.")
        
        await cur.execute("INSERT INTO ticket_settings (guild, name, survey1, survey2, survey3, role, user_close, max_ticket, ticket_category, closed_ticket_category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (guild, name, survey1, survey2, survey3, arrayToString(role), 1 if userClose else 0, maxTicket if maxTicket else 0, ticketCategory, closedTicketCategory))
        await con.commit()
        id = cur.lastrowid
        await closeDB(con, cur)
        return TicketType(guild, name, userClose, maxTicket, role, survey1, survey2, survey3, ticketCategory, closedTicketCategory, id)

    @staticmethod
    async def findByGuildIdAndName(guildId, name) -> "TicketType":
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE guild = ? AND name = ?", (guildId, name))
        row = await cur.fetchone()
        await closeDB(con, cur)

        if not row:
            return None
        
        return TicketType(row["guild"], row["name"], bool(row["user_close"]), row["max_ticket"], stringToArray(row["role"]), row["survey1"], row["survey2"], row["survey3"], row["ticket_category"], row["closed_ticket_category"], row["id"])
    
    @staticmethod
    async def findByGuildId(guildId)-> list["TicketType"]:
        result = []

        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE guild = ?", (guildId,))
        rows = await cur.fetchall()
        await closeDB(con, cur)
        
        for row in rows:
            result.append(TicketType(row["guild"], row["name"], bool(row["user_close"]), row["max_ticket"], stringToArray(row["role"]), row["survey1"], row["survey2"], row["survey3"], row["ticket_category"], row["closed_ticket_category"], row["id"]))
        
        return result
    
    @staticmethod
    async def findById(id) -> "TicketType":
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE id = ?", (id,))
        row = await cur.fetchone()
        await closeDB(con, cur)

        return TicketType(row["guild"], row["name"], bool(row["user_close"]), row["max_ticket"], stringToArray(row["role"]), row["survey1"], row["survey2"], row["survey3"], row["ticket_category"], row["closed_ticket_category"], row["id"]) if row else None