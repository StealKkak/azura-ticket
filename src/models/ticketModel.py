from datetime import *

from services.dbService import *

from utils.arrayUtil import *

class Ticket():
    def __init__(self, guild: int, user: int, channel: str, ticket_status: str, ticketType: int, open_time: datetime = None, close_time: datetime = None):
        self.__guild = guild
        self.__user = user
        self.__channel = channel
        self.__ticket_status = ticket_status
        self.__ticketType = ticketType
        self.__openTime = open_time.isoformat() if open_time else None
        self.__closeTime = close_time.isoformat() if close_time else None

    @property
    def guild(self):
        return int(self.__guild)
    
    @property
    def user(self):
        return int(self.__user)
    
    @property
    def channel(self):
        return int(self.__channel)
    
    @property
    def status(self):
        return self.__ticket_status
    
    @status.setter
    def status(self, value):
        if value not in ["open", "closed", "deleted", "saved"]:
            raise ValueError("Invalid ticket status")
        
        self.__ticket_status = value

    @property
    def ticketType(self):
        return self.__ticketType
    
    @ticketType.setter
    def ticketType(self, value):
        self.__ticketType = value
    
    @property
    def openTime(self):
        if not self.__openTime:
            return None
        
        return datetime.fromisoformat(self.__openTime)
    
    @openTime.setter
    def openTime(self, value: datetime):
        if value is None:
            self.__openTime = None
            return
        
        self.__openTime = datetime.isoformat(value)

    @property
    def closeTime(self):
        if not self.__closeTime:
            return None
        
        return datetime.fromisoformat(self.__closeTime)
    
    @closeTime.setter
    def closeTime(self, value: datetime):
        if value is None:
            self.__closeTime = None
            return
        
        self.__closeTime = datetime.isoformat(value)

    async def save(self):
        con, cur = await loadDB()
        try:
            await cur.execute("UPDATE tickets SET guild = ?, user = ?, channel = ?, ticket_status = ?, open_time = ?, close_time = ? WHERE channel = ?", (self.__guild, self.__user, self.__channel, self.__ticket_status, self.__openTime, self.__closeTime, self.__channel))
            await con.commit()
        finally:
            await closeDB(con, cur)

    @staticmethod
    async def createInstance(guild: str, user: str, channel: str, ticket_status: str, ticketType: str, open_time: datetime = None, close_time: datetime = None):
        con, cur = await loadDB()
        try:
            await cur.execute("INSERT INTO tickets (guild, user, channel, ticket_status, ticket_type, open_time, close_time) VALUES (?, ?, ?, ?, ?, ?, ?)", (guild, user, channel, ticket_status, ticketType, open_time.isoformat() if open_time else None, close_time.isoformat() if close_time else None))
            await con.commit()
        finally:
            await closeDB(con, cur)
        return Ticket(guild, user, channel, ticket_status, open_time, close_time)

    @staticmethod
    async def findByChannelId(channelId):
        con, cur = await loadDB()
        await cur.execute("SELECT * FROM tickets WHERE channel = ?", (channelId,))
        row = await cur.fetchone()
        await closeDB(con, cur)

        return Ticket(row["guild"], row["user"], row["channel"], row["ticket_status"], row["ticket_type"], datetime.fromisoformat(row["open_time"]) if row["open_time"] else None, datetime.fromisoformat(row["close_time"]) if row["close_time"] else None)
    
    @staticmethod
    async def findByGuildId(guildId) -> list["Ticket"]:
        result = []

        con, cur = await loadDB()
        await cur.execute("SELECT * FROM tickets WHERE guild = ? ORDER BY id ASC", (guildId,))
        rows = await cur.fetchall()
        await closeDB(con, cur)

        for row in rows:
            result.append(Ticket(row["guild"], row["user"], row["channel"], row["ticket_status"], row["ticket_type"], datetime.fromisoformat(row["open_time"]) if row["open_time"] else None, datetime.fromisoformat(row["close_time"]) if row["close_time"] else None))

        return result

    @staticmethod
    async def findOpenTicket(guildId, userId, ticketTypeId) -> list["Ticket"]:
        result = []

        con, cur = await loadDB()
        await cur.execute("SELECT * FROM tickets WHERE guild = ? AND user = ? AND ticket_status = ? AND ticket_type = ?", (guildId, userId, "open", ticketTypeId))
        rows = await cur.fetchall()
        await closeDB(con, cur)

        for row in rows:
            result.append(Ticket(row["guild"], row["user"], row["channel"], row["ticket_status"], row["ticket_type"], datetime.fromisoformat(row["open_time"]) if row["open_time"] else None, datetime.fromisoformat(row["close_time"]) if row["close_time"] else None))

        return result