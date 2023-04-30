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
        self.nameNum=1
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
        for checkRole in ctx.guild.roles:
            if(checkRole == role):
                exists = True
        if exists:
            await ctx.author.add_roles(role)
            await ctx.send("Successfully joined the study session!")
        else:
            await ctx.send("That role does not exist!")

    def hasRole(self, member: discord.Member, role: discord.Role):
        for memRole in member.roles:
            if memRole == role:
                return True
        return False

    @commands.command(name="startSession", description="Begins a new study session")
    async def startSession(self, ctx):
        """
        Begins a new study session for the member that invoked this command
        """
        #create pomodoro category (if it does not already exist), dont worry about this yet until discussed with mark
        # await member.guild.create_category()
        await ctx.send("Attempting to create a new session...")
        #create a new role
        self.groupNum+=1
        if self.groupNum == 1: #begin timer if this is the first study session yet
            task = self.peekCheckpoints.start()
        roleName = "studygroup{nameNum}".format(nameNum=self.nameNum)
        newRole = await ctx.guild.create_role(name=roleName)
        #give member the new role
        await ctx.author.add_roles(newRole) #TODO: fix arguments being passed here? probably fine after looking at examples in documentation
        #names for voice and text channels
        voiceChannelName = "{channelName}voice".format(channelName=roleName)
        textChannelName = "{channelName}text".format(channelName=roleName)
        #create new vc
        voiceChannel = await ctx.guild.create_voice_channel(name=voiceChannelName) #TODO: fix arguments passed here? probably fine after looking at examples in documentation
        #create new text channel
        textChannel = await ctx.guild.create_text_channel(name=textChannelName) #TODO: fix arguments passed here? probably fine after looking at examples in documentation
        #update every channel's read/write permission to false for newRole (excluding the channels 
        #"channelName voice" and "channelName text")
        for channel in ctx.guild.text_channels:
            if channel.name != textChannelName:
                await channel.set_permissions(newRole, view_channel=False, send_messages=False)
        for channel in ctx.guild.voice_channels:
            if channel.name != voiceChannelName:
                await channel.set_permissions(newRole, view_channel=False, connect=False)
        for member in ctx.guild.members:
            if not self.hasRole(member=member, role=newRole):
                await textChannel.set_permissions(member, send_messages=False)
                await voiceChannel.set_permissions(member, connect=False)
                
        #use a dictionary with keys as a tuple to represent the time (hour, minute)
        #and value as a tuple to represent the role/group to be affected and the operation being called
        #(role, operation), might be a bad design choice idk
        currTime = datetime.datetime.utcnow()
        addTime = datetime.timedelta(minutes=1) #TODO: revert back to 25 minutes after testing
        newTime = currTime + addTime
        newKey = (newTime.hour, newTime.minute)
        self.timeOp[newKey] = (newRole, "breakstart")
        await ctx.send("New session has been started. Please join the specified voice channel. Good Luck!")

    @commands.command(name="endSession", description="ends an existing study session")
    async def endSession(self, ctx, role: discord.Role):
        """
        ends the session with the given role "role"
        """
        await ctx.send("Ending the current session for {roleName}".format(roleName = role.name))
        #delete channels
        for channel in ctx.guild.voice_channels:
            if channel.name == "{channelName}voice".format(channelName = role.name):
                await channel.delete()
                break
        #delete role
        await role.delete()
        self.groupNum-=1
        #last group study session has ended, stop looking for checkpoints every minute
        if self.groupNum == 0:
            self.peekCheckpoints.cancel()
        await ctx.send("Session successfully ended.")
        for channel in ctx.guild.text_channels:
            if channel.name == "{channelName}text".format(channelName = role.name):
                await channel.delete()
                break

    async def endSessionRoleNoCTX(self, role: discord.Role):
        """
        ends the session with the given role "role"
        """
        #delete channels
        for channel in role.guild.text_channels:
            if channel.name == "{channelName}text".format(channelName = role.name):
                await channel.send("Ending the current session due to inactivity".format(roleName = role.name))
                await channel.delete()
                break
        for channel in role.guild.voice_channels:
            if channel.name == "{channelName}voice".format(channelName = role.name):
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
        currTime = datetime.datetime.utcnow()
        #TODO: compare currTime.hour and currTime.minute to the next checkpoint
        if (currTime.hour, currTime.minute) in self.timeOp:
            operation = self.timeOp[(currTime.hour, currTime.minute)]
            if operation[1] == None:
                pass #do nothing
            elif operation[1] == "breakstart": #TODO: set new breakover event to happen in 5 minutes
                
                addTime = datetime.timedelta(minutes=1)
                newTime = currTime + addTime
                newKey = (newTime.hour, newTime.minute)
                self.timeOp[newKey] = (operation[0], "breakover")
                for channel in operation[0].guild.text_channels:
                    if channel.name == "{channelName}text".format(channelName=operation[0].name):
                        await channel.send("5 Minute break has begun!")
            elif operation[1] == "breakover": #operation == "breakover", TODO: get user to check in and make new breakstart?
                for channel in operation[0].guild.voice_channels:
                    if channel.name == "{channelName}voice".format(channelName=operation[0].name):
                        if len(channel.members) <= 0: #end session
                            await self.endSessionRoleNoCTX(operation[0])
                        else: #continue breakstart
                            addTime = datetime.timedelta(minutes=1)
                            newTime = currTime + addTime
                            newKey = (newTime.hour, newTime.minute)
                            self.timeOp[newKey] = (operation[0], "breakstart")

def setup(bot):
    bot.add_cog(pomodoro(bot))
    