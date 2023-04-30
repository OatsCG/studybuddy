import discord
import typing
import random
import datetime
from discord.ext import commands
from discord.ext import tasks

class pomodoro(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.groupNum=0
        self.songNames = [] #preload all song file names
        self.noiseNames = [] #preload all ambient noise file names
        self.timeOp = {} #dictionary that performs an operation for a given time
    
    async def play(self, ctx, fname: str): #helper for the bot to open and play a local audio file
        f = open(fname, "rb")
        source = discord.PCMVolumeTransformer(discord.PCMAudio(f)) #TODO: FFmpegPCMAudio needs more research (idk what im doing) (after research, consider just using PCM audio files instead and use discord.PCMAudio?)
        ctx.voice_client.play(source)

    async def join(self, ctx, channel: discord.VoiceChannel): #helper for bot to join vcs
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()
    
    @commands.command(name="playMusic", description="Plays a randomly selected lofi song or ambient noise")
    async def playMusic(self, ctx, type: str, role: discord.Role):
        """
        enters the voice chat corresponding to role and plays music/noise according to option picked

        NO IDEA HOW TO SET THIS UP YET, CONSIDER LOOKING AT THE FOLLOWING LINKS:
        https://docs.pycord.dev/en/stable/api/voice.html#discord.FFmpegAudio
        https://docs.pycord.dev/en/stable/api/voice.html#discord.PCMVolumeTransformer
        https://github.com/Pycord-Development/pycord/blob/v2.4.1/examples/basic_voice.py
        """
        if(type.lower() == "lofi"):
            randNum = random.randint(0,len(self.songNames)-1) #pick random song name from index 0 to index len(names)-1
            for channel in ctx.guild.voice_channels: #find the corresponding voice chat to join 
                if channel.name == "{channelName} voice".format(channelName=role.name):
                    self.join(ctx=ctx, channel=channel) #TODO: not sure if arguments must be passed like this
                    #TODO: load randomly selected song to be played
                    self.play(ctx=ctx, fname=self.songNames[randNum]) #TODO: not sure if arguments must be passed like this
                    return
        elif(type.lower() == "ambient"):
            randNum = random.randint(0,len(self.noiseNames)-1) #pick random ambient noise name from index 0 to index len(names)-1
            for channel in ctx.guild.voice_channels: #find the corresponding voice chat to join 
                if channel.name == "{channelName} voice".format(channelName=role.name):
                    self.join(ctx=ctx, channel=channel) #TODO: not sure if arguments must be passed like this
                    #TODO: load randomly selected ambient noise to be played
                    self.play(ctx=ctx, fname=self.noiseNames[randNum]) #TODO: not sure if arguments must be passed like this
                    return
        else:
            await ctx.send("Usage example: 's.playMusic type' where type is 'lofi' or 'ambient'")

    @commands.command(name="joinSession", description="Joins an existing study session")
    async def joinSession(self, ctx, role:discord.Role):
        """ 
        Allows member to join the existing study group indicated by role
        """
        exists = False
        for role in ctx.guild.roles:
            if(role == role):
                exists = True
        if exists:
            await ctx.author.add_roles(role)
            await ctx.send("Successfully joined the study session!")
        else:
            await ctx.send("That role does not exist!")

    @commands.command(name="startSession", description="Begins a new study session")
    async def startSession(self, ctx):
        """
        Begins a new study session for the member that invoked this command
        """
        #create pomodoro category (if it does not already exist), dont worry about this yet until discussed with mark
        # await member.guild.create_category()
        ctx.send("Attempting to create a new session...")
        #create a new role
        self.groupNum+=1
        if self.groupNum == 1: #begin timer if this is the first study session yet
            task = self.peekCheckpoints.start()
        roleName = "Study Group {groupNum}".format(groupNum=self.groupNum)
        newRole = await ctx.guild.create_role(name=roleName)
        #give member the new role
        await ctx.author.add_roles(newRole) #TODO: fix arguments being passed here? probably fine after looking at examples in documentation
        #names for voice and text channels
        voiceChannelName = "{channelName} voice".format(channelName=roleName)
        textChannelName = "{channelName} text".format(channelName=roleName)
        #create new vc
        await ctx.guild.create_voice_channel(name=voiceChannelName) #TODO: fix arguments passed here? probably fine after looking at examples in documentation
        #create new text channel
        await ctx.guild.create_text_channel(name=textChannelName) #TODO: fix arguments passed here? probably fine after looking at examples in documentation
        #update every channel's read/write permission to false for newRole (excluding the channels 
        #"channelName voice" and "channelName text")
        for channel in ctx.guild.text_channels:
            if channel.name != textChannelName:
                await channel.set_permissions(newRole, view_channel=False, send_messages=False)
        for channel in ctx.guild.voice_channels:
            if channel.name != voiceChannelName:
                await channel.set_permissions(newRole, view_channel=False, connect=False)
        #TODO:insert break start and break end into file 
        #ALTERNATIVE: use a dictionary with keys as a tuple to represent the time (hour, minute)
        #and value as a tuple to represent the role/group to be affected and the operation being called
        #(role, operation), might be a bad design choice idk
        currTime = await datetime.utcnow()
        addTime = datetime.timedelta(minutes=25)
        newTime = currTime + addTime
        await self.timeOp.put((newTime.hour, newTime.minute), (newRole, "breakstart"))
        ctx.send("New session has been started. Good Luck!")

    @commands.command(name="endSession", description="ends an existing study session")
    async def forceEndSession(self, ctx, role: discord.role):
        """
        ends the session with the given role "role"
        """
        #delete channels
        for channel in ctx.guild.text_channels:
            if channel.name == "{channelName} text".format(channelName = role.name):
                await channel.delete()
                break
        for channel in ctx.guild.voice_channels:
            if channel.name == "{channelName} voice".format(channelName = role.name):
                await channel.delete()
                break
        #delete role
        await role.delete()
        self.groupNum-=1
        #last group study session has ended, stop looking for checkpoints every minute
        if self.groupNum == 0:
            self.peekCheckpoints.cancel()

    
    async def checkReactions(self, mess: discord.Message):
        if len(mess.reactions)>0:
            return True

    #TODO: how does this loop get started? (upon first group being made)
    @tasks.loop(minutes=1.0) #check if we reached any of the upcoming checkpoints every minute
    async def peekCheckpoints(self):
        """
        checks if the current time matches any of the checkpoint times found in the file given by fname
        """
        currTime = await datetime.utcnow()
        #TODO: compare currTime.hour and currTime.minute to the next checkpoint
        if self.timeOp.has_key((currTime.hour, currTime.minute)):
            operation = self.timeOp.get((currTime.hour, currTime.minute))
            if operation[1] == None:
                pass #do nothing
            elif operation[1] == "breakstart": #TODO: set new breakover event to happen in 5 minutes
                addTime = await datetime.timedelta(minutes=5)
                newTime = currTime + addTime   
                await self.timeOp.put((newTime.hour, newTime.minute), (operation[0], "breakover"))
                pass
            elif operation[1] == "breakover": #operation == "breakover", TODO: get user to check in and make new breakstart?
                mess = None
                addTime = await datetime.timedelta(minutes=5)
                newTime = currTime + addTime   
                await self.timeOp.put((newTime.hour, newTime.minute), (operation[0], "forcequit"))
                for channel in operation[0].guild.text_channels:
                    if channel.name == "{channelName} text".format(channelName=operation[0].name):
                        mess = await channel.send("Please react to this message to indicate you are here")
                if await self.checkReactions(mess): #TODO: DEFINITELY INCORRECT, NEED TO CONSTANTLY CHECK THIS IN A LOOP (consider task.loop again), reaction detected
                    #TODO: if user replies and checks in, set forcequit checkpoint to None
                    await self.timeOp.put((newTime.hour, newTime.minute), (operation[0], None))
                pass
            else: #operation[1] == "forcequit", TODO: shut down the study session due to prolonged break
                for channel in operation[0].guild.text_channels: #delete text channel
                    if channel.name == "{channelName} text".format(channelName=operation[0].name):
                        channel.delete()
                for channel in operation[0].guild.voice_channels: #delete vc
                    if channel.name == "{channelName} voice".format(channelName=operation[0].name):
                        channel.delete()
                operation[0].delete() #delete the role
                #delete the force quit dict entry
                addTime = await datetime.timedelta(minutes=5)
                newTime = currTime + addTime
                self.timeOp.pop((newTime.hour, newTime.minute))

async def setup(bot):
    print("test")
    await bot.add_cog(pomodoro(bot))
    