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
    
    async def play(self, ctx, fname: str):
        f = open(fname, "rb")
        source = discord.PCMVolumeTransformer(discord.PCMAudio(f)) #TODO: FFmpegPCMAudio needs more research (idk what im doing) (after research, consider just using PCM audio files instead and use discord.PCMAudio?)
        ctx.voice_client.play(source)

    async def join(self, ctx, channel: discord.VoiceChannel):
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
        Allows member to join the study group indicated by role
        """
        await ctx.author.add_roles(role)
        await ctx.send("Successfully joined the study session!")

    @commands.command(name="startSession", description="Begins a new study session")
    async def startSession(self, ctx):
        """
        Begins a new study session for the member that invoked this command
        """
        #create pomodoro category (if it does not already exist), dont worry about this yet until discussed with mark
        # await member.guild.create_category()
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
        addTwoFive = datetime.timedelta(minutes=25)
        newTime = currTime + addTwoFive
        self.timeOp.put((newTime.hour, newTime.minute), (newRole, "breakstart"))

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

    #TODO: how does this loop get started? (upon first group being made)
    @tasks.loop(minutes=1.0) #check if we reached any of the upcoming checkpoints every minute
    async def peekCheckpoints(self, fname: str):
        """
        checks if the current time matches any of the checkpoint times found in the file given by fname
        """
        currTime = await datetime.utcnow()
        #TODO: compare currTime.hour and currTime.minute to the next checkpoint
        if self.timeOp.has_key((currTime.hour, currTime.minute)):
            operation = self.timeOp.get((currTime.hour, currTime.minute))
            if operation[1] == "breakstart": #TODO: set new breakover event to happen in 5 minutes
                
                pass
            else: #operation == "breakover", TODO: get user to check in and make new breakstart?
                
                pass

async def setup(bot):
    await bot.add_cog(pomodoro(bot))
    