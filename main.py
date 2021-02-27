import discord, os, server, time, datetime, asyncio, math
from discord.ext import commands
from easypydb import DB

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True

client = commands.Bot(
	command_prefix="+",
	case_insensitive=True,
	help_command=None,
	intents=intents
)


db = DB("db", os.getenv("dbToken"))



def pfp(user):
	try:
		user2 = client.get_user(int(user))
		if user2.is_avatar_animated():
			format = "gif"
		else:
			format = "png"
		pfp = str(user2.avatar_url_as(format=format))
	except AttributeError:
		pfp = None
	return pfp


def timeStrToSeconds(time):
	time = time.lower()
	try:
		if time[-1] == "s":
			return int(time[:-1])
		elif time[-1] == "m":
			return int(time[:-1]) * 60
		elif time[-1] == "h":
			return int(time[:-1]) * 3600
		elif time[-1] == "d":
			return int(time[:-1]) * 3600 * 24
	except ValueError:
		return "error"
	return "error"

def seconds_to_real_display(time):
	if time != "indefinite":
		y = str(math.floor(time / (3600 * 24) / 30.436875 / 12) + 1970)
		m = str(math.floor(time / (3600 * 24) / 30.436875 % 12) + 1)
		d = str(math.floor(time / (3600 * 24) % 30.436875))

		h = str(math.floor(time / 3600 % 24))
		i = str(math.floor(time % 3600 / 60))
		s = str(math.floor(time % 3600 % 60))

		if len(m) < 2: m = "0" + m
		if len(d) < 2: d = "0" + d

		if len(h) < 2: h = "0" + h
		if len(i) < 2: i = "0" + i
		if len(s) < 2: s = "0" + s

		return f"{d}/{m}/{y} {h}:{i}:{s}"
	return time

def timestamp_to_display(time): # basically without the + 1970
	if time != "indefinite":
		time = seconds_to_real_display(time)
		splitTime = time.split(" ")
		splitDate = splitTime[0].split("/")
		date = splitDate[0] + "/" + str(int(splitDate[1]) - 1) + "/" + str(int(splitDate[2]) - 1970)
		return date + " " + splitTime[1]
	return time

async def get_role_from_id(guild, roleID):
	for i in guild.roles:
		if str(i.id) == str(roleID):
			return i
	return "error"

async def get_member_from_id(guild, memberID):
	for i in guild.members:
		if str(i.id) == str(memberID):
			return i
	return "error"

async def get_guild_from_id(guildID):
	for i in client.guilds:
		if str(i.id) == str(guildID):
			return i
	return "error"


def time_left(guild, user):
	start = db["servers"][guild]["mutes"][user]["start"]
	duration = db["servers"][guild]["mutes"][user]["duration"]
	if duration != "indefinite":
		return int(round(start + duration - time.time(), 0))
	else:
		return "indefinite"

@client.command()
async def ping(ctx):
	await ctx.send("pong")



async def loop():
	while True:
		await check_mutes()
		await asyncio.sleep(10)

async def check_mutes():
	now = time.time()
	removeMutes = {}
	for guild in db["servers"]:
		removeMutes[guild] = []
		for muted in db["servers"][guild]["mutes"]:
			if db["servers"][guild]["mutes"][muted]["duration"] != "indefinite":
				if db["servers"][guild]["mutes"][muted]["start"] + db["servers"][guild]["mutes"][muted]["duration"] <= now:
					target = await get_member_from_id(await get_guild_from_id(guild), muted)
					await target.remove_roles(await get_role_from_id(await get_guild_from_id(guild), db["servers"][guild]["mute"]))
					removeMutes[str((await get_guild_from_id(guild)).id)].append(str(target.id))
	for guild in removeMutes:
		for member in removeMutes[guild]:
			del db["servers"][guild]["mutes"][member]
			db.save()


async def check_db():
	for guild in client.guilds:
		if str(guild.id) not in db["servers"]:
			db["servers"][str(guild.id)] = {
				"logs": 0,
				"mute": 0,
				"warn_mute": 0,
				"strike_mute": 0,
				"auto_strike": 0,
				"auto_ban": 0,
				"nicknames_channel": 0,
				"nicknames": {},
				"infractions":{},
				"mutes":{}
			}
			db.save()


@client.event
async def on_ready():
	print("Im in")
	await check_db()
	asyncio.ensure_future(loop())


@client.event
async def on_command_error(ctx, error):
	embed = discord.Embed(color=0xff0000,title="ERROR", description=str(error))
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(5)
	await msg.delete()


@client.event
async def on_guild_join(guild):
	db["servers"][str(guild.id)] = {
		"logs": 0,
		"mute" :0,
		"warn_mute": 0,
		"strike_mute": 0,
		"auto_strike": 0,
		"auto_ban": 0,
		"nicknames_channel": 0,
		"nicknames": {},
		"infractions":{},
		"mutes":{}
	}
	db.save()



@client.event
async def on_member_join(member):
	if str(member.id) in db["servers"][str(member.guild.id)]["mutes"]:
		await member.add_roles(await get_role_from_id(member.guild, db["servers"][str(member.guild.id)]["mute"]))
	if db["servers"][str(member.guild.id)]["logs"] != 0:
		await client.get_channel(db["servers"][str(member.guild.id)]["logs"]).send(
			embed=discord.Embed(
				title="Member joined!!",
				description="<@" + str(member.id) + "> joined!",
				color=0x00cc00
			).set_thumbnail(url=pfp(member.id))
		)


@client.event
async def on_member_remove(member):
	if db["servers"][str(member.guild.id)]["logs"] != 0:
		await client.get_channel(db["servers"][str(member.guild.id)]["logs"]).send(
			embed=discord.Embed(
				title="Member left!!",
				description="<@" + str(member.id) + "> left!",
				color=0xcc0000
			).set_thumbnail(url=pfp(member.id))
		)


@client.event
async def on_message_delete(message):
	if message.channel.type is not discord.ChannelType.private:
		if db["servers"][str(message.guild.id)]["logs"] != 0 and message.content != "":
			embed = discord.Embed(
				title="Message deleted!",
				description="Message from: <@" + str(message.author.id) + ">\nIn <#" + str(message.channel.id) + ">",
				color=0xcc0000
			)
			embed.add_field(name="content", value=message.content)
			embed.set_footer(text=datetime.datetime.fromtimestamp(time.time()).strftime("%d/%m/%y %H:%M") + " UTC")
			embed.set_thumbnail(url=pfp(message.author.id))
			await client.get_channel(db["servers"][str(message.guild.id)]["logs"]).send(embed=embed)


@client.event
async def on_message_edit(before, after):
	if before.channel.type is not discord.ChannelType.private:
		if db["servers"][str(before.guild.id)]["logs"] != 0:
			if before.author.id != 757277754503856169 and before.content != after.content:
				embed = discord.Embed(
					title="Message edited!",
					description="Message from <@" + str(before.author.id) + ">\nIn <#" + str(before.channel.id) + ">",
					color=0x00cc00
				)
				embed.add_field(name="before", value=before.content)
				embed.add_field(name="after", value=after.content)
				embed.set_footer(text=datetime.datetime.fromtimestamp(time.time()).strftime("%d/%m/%y %H:%M") + " UTC")
				embed.set_thumbnail(url=pfp(before.author.id))
				await client.get_channel(db["servers"][str(before.guild.id)]["logs"]).send(embed=embed)


@client.event
async def on_member_ban(guild, user):
	if db["servers"][str(guild.id)]["logs"] != 0:
		embed = discord.Embed(
			title="Banned!",
			description=str(user) + " has been banned.",
			color=0xcc0000
		).set_thumbnail(url=pfp(user.id))
		await client.get_channel(db["servers"][str(guild.id)]["logs"]).send(embed=embed)


@client.event
async def on_member_unban(guild, user):
	if db["servers"][str(guild.id)]["logs"] != 0:
		embed = discord.Embed(
			title="Banned!",
			description=str(user) + " has been unbanned.",
			color=0x00cc00
		).set_thumbnail(url=pfp(user.id))
		await client.get_channel(db["servers"][str(guild.id)]["logs"]).send(embed=embed)




@client.command(aliases=["commands"])
async def help(ctx, catagory=None):
	if catagory == None:
		embed = discord.Embed(
			title="Command Categories",
			color=0x00cc00
		)
		embed.add_field(name="Configuration", value="The commands to set up the bot.", inline=False)
		embed.add_field(name="Infractions", value="The commands to infract someone for being naughty.", inline=False)
		embed.add_field(name="Repealing", value="The commands to repeal an infraction when mods get a little too trigger happy.", inline=False)
		embed.add_field(name="Muting", value="The commands to make people shut up.", inline=False)
		embed.add_field(name="Member", value="The commands for any server member to use.", inline=False)
		embed.set_footer(text="Do `+help category` to view a certain catagory")
		await ctx.send(embed=embed)
	else:
		catagory = catagory.lower()
		if catagory in ["configuration", "infractions", "repealing", "muting", "member"]:
			if catagory == "configuration":
				embed = discord.Embed(
					title="Configuration Commands",
					color=0x00cc00
				)
				embed.add_field(name="config_logs", value="Choose to which channel I should send the logs.\nIn the form `+config_logs TextChannel`.", inline=False)
				embed.add_field(name="config_mute", value="Choose which role to be addded to a member when muted.\nIn the form `+config_mute Role`.", inline=False)
				embed.add_field(name="config_warn_mute", value="Choose for how long a member will be muted after being warned.\nIn the form `+config_warn_mute time`.", inline=False)
				embed.add_field(name="config_strike_mute", value="Choose for how long a member will be muted after being struck.\nIn the form `+config_strike_mute time`.", inline=False)
				embed.add_field(name="config_auto_strike", value="Choose how many warnings until a member gets automatically struck.\nIn the form `+config_auto_strike integer`.", inline=False)
				embed.add_field(name="config_auto_ban", value="Choose how many strikes until a member gets automatically banned.\nIn the form `+config_auto_ban integer`.", inline=False)
				embed.add_field(name="config_nicknames", value="Choose to which channel I should send the nickname requests.\nIn the form `+config_nicknames TextChannel`.", inline=False)
				embed.set_footer(text="These commands can only be used by server admins")
			elif catagory == "infractions":
				embed = discord.Embed(
					title="Infraction Commands",
					color=0x00cc00
				)
				embed.add_field(name="warn", value="Warn a member for being naughty.\nIn the form `+warn Member <reason>`.", inline=False)
				embed.add_field(name="strike", value="sStrike a member for being naughty.\nIn the form `+strike Member <reason>`.", inline=False)
				embed.add_field(name="infractions", value="View your infractions from this server. Moderators can do `+infractions Member` to view another member's infractions. Must allow DMs from me.", inline=False)
				embed.set_footer(text="These commands can only be used by server moderators (except the infractions command)")
			elif catagory == "repealing":
				embed = discord.Embed(
					title="Repealing Commands",
					color=0x00cc00
				)
				embed.add_field(name="repeal_warn", value="Repeal one of a member's warns.\nIn the form `+repeal_warn Member WarnID`.", inline=False)
				embed.add_field(name="repeal_strike", value="Repeal one of a member's strikes.\nIn the form `+repeal_strike Member strikeID`.", inline=False)
				embed.set_footer(text="These commands can only be used by server moderators")
			elif catagory == "muting":
				embed = discord.Embed(
					title="Muting Commands",
					color=0x00cc00
				)
				embed.add_field(name="mute", value="Make a member shut up.\nIn the form `+mute Member <time>`, if a time is omitted, then they will be muted indefinitely.", inline=False)
				embed.add_field(name="unmute", value="Allow a member to speak again.\nIn the form `+mute Member`.", inline=False)
				embed.add_field(name="view_mutes", value="View your current mutes across all the servers that I am in. Must allow DMs from me.", inline=False)
				embed.add_field(name="view_servers_mutes", value="View the current mutes in this server. Must allow DMs from me.", inline=False)
				embed.set_footer(text="These commands can only be used by server moderators (except the view_mutes command)")
			elif catagory == "member":
				embed = discord.Embed(
					title="Member Commands",
					color=0x00cc00
				)
				embed.add_field(name="infractions", value="View your infractions from this server. Moderators can do `+infractions Member` to view another member's infractions. Must allow DMs from me.", inline=False)
				embed.add_field(name="view_mutes", value="View your current mutes across all the servers that I am in. Must allow DMs from me.", inline=False)
				embed.add_field(name="nickname", value="Request a nickname to have in this server.\nIn the form `+nickname Name`", inline=False)
				embed.set_footer(text="These commands can be used by any server member")
			await ctx.send(embed=embed)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="Category '" + catagory + "' not found.",
					color=0xcc0000
				)
			)
		
	



@client.command()
async def config_logs(ctx,  *, channel: discord.TextChannel=None):
	if ctx.message.author.guild_permissions.administrator:
		if channel != None:
			db["servers"][str(ctx.guild.id)]["logs"] = channel.id
			db.save()
			await ctx.send(
				embed=discord.Embed(
					title="Logs configured!",
					description="The logs channel for this server has been set to <#" + str(channel.id) + ">",
					color=0x00cc00
				)
			)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You did not provide a channel",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You are not an admin of this server",
				color=0xcc0000
			)
		)


@client.command()
async def config_mute(ctx, *, role: discord.Role=None):
	if ctx.message.author.guild_permissions.administrator:
		if role != None:
			db["servers"][str(ctx.guild.id)]["mute"] = role.id
			db.save()
			await ctx.send(
				embed=discord.Embed(
					title="Mute configured!",
					description="The mute role for this server has been set to " + str(role.mention),
					color=0x00cc00
				)
			)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You did not provide a role",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You are not an admin of this server",
				color=0xcc0000
			)
		)


@client.command()
async def config_warn_mute(ctx, time=None):
	if ctx.message.author.guild_permissions.administrator:
		if time != None:
			time = timeStrToSeconds(time)
			if time != "error":
				db["servers"][str(ctx.guild.id)]["warn_mute"] = time
				db.save()
				await ctx.send(
					embed=discord.Embed(
						title="Warn Mute Configured!",
						description="When a member is warned, they will be muted for **" + timestamp_to_display(time) + "**",
						color=0x00cc00
					)
				)
			else:
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description="You entered the duration incorrectly",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You did not provide a time",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You are not an admin of this server",
				color=0xcc0000
			)
		)


@client.command()
async def config_strike_mute(ctx, time=None):
	if ctx.message.author.guild_permissions.administrator:
		if time != None:
			time = timeStrToSeconds(time)
			if time != "error":
				db["servers"][str(ctx.guild.id)]["strike_mute"] = time
				db.save()
				await ctx.send(
					embed=discord.Embed(
						title="Strike Mute Configured!",
						description="When a member is struck, they will be muted for **" + timestamp_to_display(time) + "**",
						color=0x00cc00
					)
				)
			else:
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description="You entered the duration incorrectly",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You did not provide a time",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You are not an admin of this server",
				color=0xcc0000
			)
		)


@client.command()
async def config_auto_strike(ctx, num=None):	
	if ctx.message.author.guild_permissions.administrator:
		if num != None:
			try:
				num = int(num)
				correct = num > 0
			except:
				correct = False
			if correct:
				db["servers"][str(ctx.guild.id)]["auto_strike"] = num
				db.save()
				await ctx.send(
					embed=discord.Embed(
						title="Auto Strike Configured!",
						description="If a member recieves " + str(num) + " warnings, they will be struck",
						color=0x00cc00
					)
				)
			else:
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description="Invalid number entered",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You did not provide a number",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You are not an admin of this server",
				color=0xcc0000
			)
		)


@client.command()
async def config_auto_ban(ctx, num=None):	
	if ctx.message.author.guild_permissions.administrator:
		if num != None:
			try:
				num = int(num)
				correct = num > 0
			except:
				correct = False
			if correct:
				db["servers"][str(ctx.guild.id)]["auto_ban"] = num
				db.save()
				await ctx.send(
					embed=discord.Embed(
						title="Auto Ban Configured!",
						description="If a member recieves " + str(num) + " strikes, they will be banned",
						color=0x00cc00
					)
				)
			else:
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description="Invalid number entered",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You did not provide a number",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You are not an admin of this server",
				color=0xcc0000
			)
		)


@client.command()
async def config_nicknames(ctx, *, channel: discord.TextChannel=None):
	if ctx.message.author.guild_permissions.administrator:
		if channel != None:
			db["servers"][str(ctx.guild.id)]["nicknames_channel"] = channel.id
			db.save()
			await ctx.send(
				embed=discord.Embed(
					title="Nicknames configured!",
					description="The nickname request channel for this server has been set to <#" + str(channel.id) + ">",
					color=0x00cc00
				)
			)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You did not provide a channel",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You are not an admin of this server",
				color=0xcc0000
			)
		)

	

async def check_auto_ban(ctx, member):
	guildID = str(ctx.guild.id)
	if db["servers"][guildID]["auto_ban"] != 0:
		if len(db["servers"][guildID]["infractions"][str(member.id)]["warns"]) >= db["servers"][guildID]["auto_ban"]:
			await member.send(
				embed=discord.Embed(
					title="Ban",
					description="You have been automatically bannes as you have **" + str(len(db["servers"][guildID]["infractions"][str(member.id)]["strikes"])) + " strikes**",
					color=0xcc0000
				)
			)
			await ctx.guild.ban(member, reason=str(len(db["servers"][guildID]["infractions"][str(member.id)]["strikes"])) + " strikes")


async def check_auto_strike(ctx, member):
	guildID = str(ctx.guild.id)
	if db["servers"][guildID]["auto_strike"] != 0:
		if len(db["servers"][guildID]["infractions"][str(member.id)]["warns"]) % db["servers"][guildID]["auto_strike"] == 0:
			await member.send(
				embed=discord.Embed(
					title="Strike",
					description="You have been automatically struck as you have **" + str(len(db["servers"][guildID]["infractions"][str(member.id)]["warns"])) + " warnings**",
					color=0xcc0000
				)
			)
			duration = db["servers"][guildID]["strike_mute"]
			if duration != 0:
				role = await get_role_from_id(ctx.guild, db["servers"][guildID]["mute"])
				if role != "error":
					await member.add_roles(role)
					db["servers"][guildID]["mutes"][str(member.id)] = {
						"start": time.time(),
						"duration": duration
					}
					db.save()
			else:
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description="Your mute role is set up incorrectly, do `+config_mute Role`.",
						color=0xcc0000
					)
				)
			await check_auto_ban(guildID, member)


@client.command()
async def warn(ctx, member: discord.Member=None, *, reason=None):
	if ctx.message.author.guild_permissions.manage_messages:
		if member != None:
			if len(reason) < 2000:
				if str(member.id) not in db["servers"][str(ctx.guild.id)]["infractions"]:
					db["servers"][str(ctx.guild.id)]["infractions"][str(member.id)]= {
						"warns":{},
						"strikes":{}
					}
					db.save()
				warns = db["servers"][str(ctx.guild.id)]["infractions"][str(member.id)]["warns"]
				highest = 0
				for warn in warns:
					if int(warn) > highest:
						highest = int(warn)
				db["servers"][str(ctx.guild.id)]["infractions"][str(member.id)]["warns"][str(highest+1)] = {
					"moderator": ctx.author.id,
					"reason":reason,
					"time": time.time()
				}
				db.save()
				await ctx.send(
					embed=discord.Embed(
						title="Warn",
						description=str(member) + " warned for: **" + str(reason) + "**",
						color=0xcc0000
					)
				)
				message = "You have been warned for **" + reason + "**"
				role = "error"
				duration = db["servers"][str(ctx.guild.id)]["warn_mute"]
				if duration != 0:
					role = await get_role_from_id(ctx.guild, db["servers"][str(ctx.guild.id)]["mute"])
					if role != "error":
						await member.add_roles(role)
						db["servers"][str(ctx.guild.id)]["mutes"][str(member.id)] = {
							"start": time.time(),
							"duration": duration
						}
						db.save()
				else:
					await ctx.send(
						embed=discord.Embed(
							title="Error",
							description="Your mute role is set up incorrectly, do `+config_mute Role`.",
							color=0xcc0000
						)
					)
				if role != "error":
					message += "\nYou have been muted for **" + str(timestamp_to_display(db["servers"][str(ctx.guild.id)]["warn_mute"])) + "**"
				await member.send(
					embed=discord.Embed(
						title="Warn",
						description=message,
						color=0xcc0000
					)
				)
				await check_auto_strike(ctx, member)
			else:
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description="Reason must be less than 2000 characters",
						color=0xcc0000
					)
				)				
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You did not provide a member",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You are not a moderator of this server",
				color=0xcc0000
			)
		)



@client.command()
async def strike(ctx, member: discord.Member=None, *, reason=None):
	if ctx.message.author.guild_permissions.manage_messages:
		if member != None:
			if len(reason) < 2000:
				if str(member.id) not in db["servers"][str(ctx.guild.id)]["infractions"]:
					db["servers"][str(ctx.guild.id)]["infractions"][str(member.id)]= {
						"warns":{},
						"strikes":{}
					}
					db.save()
				strikes = db["servers"][str(ctx.guild.id)]["infractions"][str(member.id)]["strikes"]
				highest = 0
				for strike in strikes:
					if int(strike) > highest:
						highest = int(strike)
				db["servers"][str(ctx.guild.id)]["infractions"][str(member.id)]["strikes"][str(highest+1)] = {
					"moderator": ctx.author.id,
					"reason":reason,
					"time": time.time()
				}
				db.save()
				await ctx.send(
					embed=discord.Embed(
						title="Strike",
						description=str(member) + " struck for: **" + str(reason) + "**",
						color=0xcc0000
					)
				)
				message = "You have been struck for **" + reason + "**"
				role = "error"
				duration = db["servers"][str(ctx.guild.id)]["strike_mute"]
				if duration != 0:
					role = await get_role_from_id(ctx.guild, db["servers"][str(ctx.guild.id)]["mute"])
					if role != "error":
						await member.add_roles(role)
						db["servers"][str(ctx.guild.id)]["mutes"][str(member.id)] = {
							"start": time.time(),
							"duration": duration
						}
						db.save()
				else:
					await ctx.send(
						embed=discord.Embed(
							title="Error",
							description="Your mute role is set up incorrectly, do `+config_mute Role`.",
							color=0xcc0000
						)
					)
				if role != "error":
					message += "\nYou have been muted for **" + str(timestamp_to_display(db["servers"][str(ctx.guild.id)]["strike_mute"])) + "**"
				await member.send(
					embed=discord.Embed(
						title="Strike",
						description=message,
						color=0xcc0000
					)
				)
				await check_auto_ban(ctx, member)
			else:				
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description="Reason must be less than 2000 characters",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You did not provide a member",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You are not a moderator of this server",
				color=0xcc0000
			)
		)




@client.command()
async def infractions(ctx, *, member: discord.Member=None):
	guild = ctx.guild.id
	correct = True
	if member == None:
		user = ctx.author.id
		username = str(ctx.author)
	elif ctx.message.author.guild_permissions.manage_messages:
		user = member.id
		username = str(member)
	else:
		correct = False
	if correct:
		if str(user) in db["servers"][str(guild)]["infractions"]:
			infractions = db["servers"][str(guild)]["infractions"][str(user)]

			overview = "**__Info__**\nWarnings: "
			if db["servers"][str(guild)]["auto_strike"] == 0:
				overview += "**" + str(len(infractions["warns"])) + "**\n"
			else:
				overview += "**" + str(len(infractions["warns"]) % db["servers"][str(guild)]["auto_strike"]) + " / " + str(db["servers"][str(guild)]["auto_strike"]) + "**\n"
			overview += "Strikes: "
			if db["servers"][str(guild)]["auto_ban"] == 0:
				overview += "**" + str(len(infractions["strikes"])) + "**\n"
			else:
				overview += "**" + str(len(infractions["strikes"]) % db["servers"][str(guild)]["auto_ban"]) + " / " + str(db["servers"][str(guild)]["auto_ban"]) + "**\n"
			

			
			warns = "\n**__Warns__**\n"
			for warn in infractions["warns"]:
				newWarn = "Warn id: **" + warn + "**\nReason: **" + str(infractions["warns"][warn]["reason"]) + "**\nDate: **" + datetime.datetime.fromtimestamp(infractions["warns"][warn]["time"]).strftime("%d/%m/%y %H:%M") + "**\n\n"
				if len(warns + newWarn) < 2040:
					warns += newWarn
				else:
					await ctx.author.send(
						embed=discord.Embed(
							title=username + "'s infractions",
							description=overview + warns,
							color=0x00cc00
						).set_thumbnail(url=pfp(user))
					)
					warns = newWarn
					overview = ""

			if warns == "**__Warns__**\n":
				warns += "Member has never been warned."

			strikes = "**__Strikes__**\n"
			for strike in infractions["strikes"]:
				newStrike = "Strike id: **" + strike + "**\nReason: **" + str(infractions["strikes"][strike]["reason"]) + "**\nDate: **" + datetime.datetime.fromtimestamp(infractions["strikes"][strike]["time"]).strftime("%d/%m/%y %H:%M") + "**\n\n"
				if len(warns + strikes + newStrike) < 2040:
					strikes += newStrike
				else:
					await ctx.author.send(
						embed=discord.Embed(
							title=username + "'s infractions",
							description=overview + warns + strikes,
							color=0x00cc00
						).set_thumbnail(url=pfp(user))
					)
					strikes = newStrike
					overview = ""
					warns = ""

			if strikes == "**__Strikes__**\n":
				strikes += "Member has never been struck."
			
			await ctx.author.send(
				embed=discord.Embed(
					title=username + "'s infractions",
					description=overview + warns + strikes,
					color=0x00cc00
				).set_thumbnail(url=pfp(user))
			)
		else:
			await ctx.author.send(
				embed=discord.Embed(
					title=username + "'s infractions",
					description="Member has never been infracted.",
					color=0x00cc00
				).set_thumbnail(url=pfp(user))
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You are not a moderator of this server",
				color=0xcc0000
			)
		)


@client.command()
async def repeal_warn(ctx, member: discord.Member=None, num=None):
	if ctx.message.author.guild_permissions.manage_messages:
		if member != None:
			try:
				int(num)
				correct = True
			except:
				correct = False
			if correct:
				guildID = str(ctx.guild.id)
				memberID = str(member.id)
				if memberID in  db["servers"][guildID]["infractions"]:
					if num in db["servers"][guildID]["infractions"][memberID]["warns"]:
						del db["servers"][guildID]["infractions"][memberID]["warns"][num]
						db.save()
						await ctx.send(
							embed=discord.Embed(
								title="Warn Repealed",
								description="Warn id **" + num + "** repealed",
								color=0x00cc00
							)
						)
					else:
						await ctx.send(
							embed=discord.Embed(
								title="Error",
								description="Warn id **" + num + "** not found",
								color=0xcc0000
							)
						)
				else:
					await ctx.send(
						embed=discord.Embed(
							title="Error",
							description=str(member) + " has never been infracted",
							color=0xcc0000
						)
					)
			else:
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description="You didn't provide a real number",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You didn't provide a member",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You don't moderate this server",
				color=0xcc0000
			)
		)


@client.command()
async def repeal_strike(ctx, member: discord.Member=None):
	if ctx.message.author.guild_permissions.manage_messages:
		if member != None:
			try:
				num = int(ctx.message.content.split(" ")[-1])
				num = str(num)
				correct = True
			except:
				correct = False
			if correct:
				guildID = str(ctx.guild.id)
				memberID = str(member.id)
				if memberID in  db["servers"][guildID]["infractions"]:
					if num in db["servers"][guildID]["infractions"][memberID]["strikes"]:
						del db["servers"][guildID]["infractions"][memberID]["strikes"][num]
						db.save()
					else:
						await ctx.send(
							embed=discord.Embed(
								title="Error",
								description="Strike id **" + num + "** not found",
								color=0xcc0000
							)
						)
				else:
					await ctx.send(
						embed=discord.Embed(
							title="Error",
							description=str(member) + " has never been infracted",
							color=0xcc0000
						)
					)
			else:
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description="You didn't provide a real number",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You didn't provide a member",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You don't moderate this server",
				color=0xcc0000
			)
		)



@client.command()
async def mute(ctx, member: discord.Member=None, duration=None):
	if ctx.message.author.guild_permissions.manage_messages:
		if member != None:
			guildID = str(ctx.guild.id)
			if db["servers"][guildID]["mute"] != 0:
				if duration == None:
					duration = "indefinite"
				else:
					duration = timeStrToSeconds(duration)
				if duration != "error":
					role = await get_role_from_id(ctx.guild, db["servers"][guildID]["mute"])
					if role != "error":
						await member.add_roles(role)
						db["servers"][guildID]["mutes"][str(member.id)] = {
							"start": time.time(),
							"duration": duration
						}
						db.save()
						embed=discord.Embed(
							title="Muted",
							description=str(member) + " has been muted for **" + timestamp_to_display(duration) + "**",
							color=0x00cc00
						)
						await ctx.send(embed=embed)
						if db["servers"][str(guildID)]["logs"] != 0:
							await client.get_channel(db["servers"][str(guildID)]["logs"]).send(embed=embed)
					else:
						await ctx.send(
							embed=discord.Embed(
								title="Error",
								description="Your mute role is set up incorrectly, do `+config_mute Role`.",
								color=0xcc0000
							)
						)
				else:
					await ctx.send(
						embed=discord.Embed(
							title="Error",
							description="You entered the duration incorrectly.",
							color=0xcc0000
						)
					)
			else:
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description="You have not conigured the mute role yet, do `+config_mute Role`.",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You did not privide a member.",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You don't moderate this server",
				color=0xcc0000
			)
		)


@client.command()
async def unmute(ctx, member: discord.Member=None):
	if ctx.message.author.guild_permissions.manage_messages:
		if member != None:
			guildID = str(ctx.guild.id)
			memberID = str(member.id)
			if memberID in db["servers"][guildID]["mutes"]:
				await member.remove_roles(await get_role_from_id(ctx.guild, db["servers"][guildID]["mute"]))
				del db["servers"][guildID]["mutes"][memberID]
				db.save()
				await ctx.send(
					embed=discord.Embed(
						title="Unmuted",
						description=str(member) + " has been unmuted.",
						color=0x00cc00
					)
				)
			else:
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description=str(member) + " is not muted.",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You didn't provide a member to unmute.",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You don't moderate this server",
				color=0xcc0000
			)
		)




@client.command()
async def view_mutes(ctx):
	user = str(ctx.author.id)
	message = ""
	for guild in db["servers"]:
		if user in db["servers"][guild]["mutes"]:
			start = db["servers"][guild]["mutes"][user]["start"]
			duration = db["servers"][guild]["mutes"][user]["duration"]
			end = start + duration if duration != "indefinite" else duration
			message += "**__" + str(client.get_user(int(user))) + "__**\n"
			message += "Start: **" + seconds_to_real_display(start) + "**\n"
			message += "End: **" + seconds_to_real_display(end) + "**\n"
			message += "Duration: **" + timestamp_to_display(duration) + "**\n"
			message += "Time Left: **" + timestamp_to_display(time_left(guild, user)) + "**\n\n"
	if message == "":
		message = "You aren't muted in any servers."
	await ctx.author.send(
		embed=discord.Embed(
			title=str(ctx.author) + "'s Current Mutes",
			description=message,
			color=0x00cc00
		).set_thumbnail(url=pfp(user))
	)


@client.command()
async def view_servers_mutes(ctx):
	if ctx.message.author.guild_permissions.manage_messages:
		guild = str(ctx.guild.id)
		message = ""
		for user in db["servers"][guild]["mutes"]:
			start = db["servers"][guild]["mutes"][user]["start"]
			duration = db["servers"][guild]["mutes"][user]["duration"]
			end = start + duration if duration != "indefinite" else duration
			message += "**__" + str(client.get_user(int(user))) + "__**\n"
			message += "Start: **" + seconds_to_real_display(start) + "**\n"
			message += "End: **" + seconds_to_real_display(end) + "**\n"
			message += "Duration: **" + timestamp_to_display(duration) + "**\n"
			message += "Time Left: **" + timestamp_to_display(time_left(guild, user)) + "**\n\n"
		if message == "":
			message = "No one is muted in this server."
		await ctx.author.send(
			embed=discord.Embed(
				title=str(ctx.guild) + "'s Current Mutes",
				description=message,
				color=0x00cc00
			).set_thumbnail(url=ctx.guild.icon_url)
		)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="You don't moderate this server",
				color=0xcc0000
			)
		)



@client.command()
async def nickname(ctx, *, name=None):
	serverId = str(ctx.guild.id)
	nicknameChannel = db["servers"][serverId]["nicknames_channel"]
	if nicknameChannel != 0:
		if name != None:
			userId = str(ctx.message.author.id)
			if len(name) <= 32:
				msg = await client.get_channel(nicknameChannel).send(
					embed=discord.Embed(
						title="Nickname Requested!",
						description="<@" + userId + "> requested the nickname `" + name + "`",
						color=0xcccc00
					)
				)
				await msg.add_reaction("👍")
				await msg.add_reaction("👎")
				db["servers"][serverId]["nicknames"][str(msg.id)] = {
					"userId": int(userId),
					"nickname": name
				}
				db.save()
				await client.get_user(int(userId)).send(
					embed=discord.Embed(
						title="Nickname Requested!",
						description="You have requested the nickname `" + name + "`. A moderator will either accept or deny it shortly.",
						color=0xcccc00
					)
				)
			else:
				await ctx.send(
					embed=discord.Embed(
						title="Error",
						description="Nickname must be 32 characters or less",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title="Error",
					description="You did not provide a nickname",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title="Error",
				description="Nickname requests have not been set up yet. Get an admin to do `+config_nicknames`",
				color=0xcc0000
			)
		)

@client.event
async def on_reaction_add(reaction, user):
	userId = str(user.id)
	if userId != str(client.user.id):
		messageId = str(reaction.message.id)
		channelId = str(reaction.message.channel.id)
		guildId = str(reaction.message.guild.id)
		if user.guild_permissions.manage_messages:
			if channelId == str(db["servers"][guildId]["nicknames_channel"]) and messageId in db["servers"][guildId]["nicknames"]:
				member = await get_member_from_id(reaction.message.guild, db["servers"][guildId]["nicknames"][messageId]["userId"])
				if str(reaction) == "👍":
					try:
						await member.edit(nick=db["servers"][guildId]["nicknames"][messageId]["nickname"])
						await reaction.message.edit(
							embed=discord.Embed(
								title="Nickname Requested!",
								description="<@" + str(db["servers"][guildId]["nicknames"][messageId]["userId"]) + "> requested the nickname `" + db["servers"][guildId]["nicknames"][messageId]["nickname"] + "`",
								color=0x00cc00
							).set_footer(text="Approved by " + str(user))
						)						
						await client.get_user(db["servers"][guildId]["nicknames"][messageId]["userId"]).send(
							embed=discord.Embed(
								title="Nickname Approved!",
								description="You requested the nickname `" + db["servers"][guildId]["nicknames"][messageId]["nickname"] + "` and it has been approved.",
								color=0x00cc00
							)
						)
						for r in reaction.message.reactions:
							await reaction.message.clear_reaction(r)
						del db["servers"][guildId]["nicknames"][messageId]
						db.save()
					except discord.errors.Forbidden:
						await reaction.message.channel.send(
							embed=discord.Embed(
								title="Error",
								description="I do not have high enough permissions to change <@" + str(db["servers"][guildId]["nicknames"][messageId]["userId"]) + ">'s nickname",
								color=0xcc0000
							)
						)
				elif str(reaction) == "👎":
					await reaction.message.edit(
						embed=discord.Embed(
							title="Nickname Requested!",
							description="<@" + str(db["servers"][guildId]["nicknames"][messageId]["userId"]) + "> requested the nickname `" + db["servers"][guildId]["nicknames"][messageId]["nickname"] + "`",
							color=0xcc0000
						).set_footer(text="Denied by " + str(user))
					)
					await client.get_user(db["servers"][guildId]["nicknames"][messageId]["userId"]).send(
						embed=discord.Embed(
							title="Nickname Denied!",
							description="You requested the nickname `" + db["servers"][guildId]["nicknames"][messageId]["nickname"] + "` and it has been denied.",
							color=0xcc0000
						)
					)
					del db["servers"][guildId]["nicknames"][messageId]
					db.save()
					for r in reaction.message.reactions:
						await reaction.message.clear_reaction(r)



server.s()
client.run(os.getenv("token"))