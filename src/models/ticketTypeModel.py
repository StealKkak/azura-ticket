from services.dbService import *

from utils.arrayUtil import *

class TicketType:
    def __init__(self, guild, name: str, userClose: bool, maxTicket: int, role: list=None, survey1: str = None, survey2: str = None, survey3: str = None):
        self.__guild = guild
        self.__name = name
        self.__survey1 = survey1
        self.__survey2 = survey2
        self.__survey3 = survey3
        self.__role = arrayToString(role) if role else None
        self.__userClose = 1 if userClose else 0
        self.__maxTicket = maxTicket

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
        if self.__role is None:
            return None
        return stringToArray(self.__role)
    
    @role.setter
    def role(self, value: list=None):
        if value is None:
            self.__role = None
        self.__role = arrayToString(value)

    @property
    def userClose(self):
        return bool(self.__userClose)
    
    @userClose.setter
    def userClose(self, value: bool):
        self.__userClose = 1 if value else None

    async def save(self):
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE guild = ? AND name = ?", (self.__guild, self.__name))
        exists = await cur.fetchone()
        
        if exists:
            await closeDB(con, cur)
            raise ValueError("A record with the same guild and name already exists.")
        
        await cur.execute("UPDATE ticket_settings SET name = ?, survay1 = ?, survay2 = ?, survay3 = ?, role = ?, user_close = ?, mat_ticket = ?", (self.__name, self.__survey1, self.__survey2, self.__survey3, self.__role, self.__userClose, self.__maxTicket))
        await con.commit()
        await closeDB(con, cur)

    @staticmethod
    async def findTicketTypeByGuildIdAndName(guildId, name):
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM ticket_settings WHERE guild = ? AND name = ?", (guildId, name))
        row = await cur.fetchone()
        await closeDB()

        if not row:
            return None
        
        return TicketType(row["guild"], row["name"], bool(row["user_close"]), row["max_ticket"], stringToArray(row["role"]) if row["role"] else None, row["survay1"], row["survay2"], row["survay3"])