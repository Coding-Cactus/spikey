import discord, os, server, time, datetime, asyncio
from discord.ext import commands
from easypydb import DB

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True

client = commands.Bot(
	command_prefix='+',
	case_insensitive=True,
	help_command=None,
	intents=intents
)


db = DB('db', os.getenv('dbToken'))



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
		if time[-1] == 's':
			return int(time[:-1])
		elif time[-3:] == 'sec':
			return int(time[:-3])
		elif time[-4:] == 'secs':
			return int(time[:-4])
		elif time[-6:] == 'second':
			return int(time[:-6])
		elif time[-7:] == 'seconds':
			return int(time[:-7])
		elif time[-1] == 'm':
			return int(time[:-1]) * 60
		elif time[-3:] == 'min':
			return int(time[:-3]) * 60
		elif time[-4:] == 'mins':
			return int(time[:-4]) * 60
		elif time[-6:] == 'minute':
				return int(time[:-6]) * 60
		elif time[-7:] == 'minutes':
			return int(time[:-7]) * 60
		elif time[-1] == 'h':
			return int(time[:-1]) * 3600
		elif time[-2:] == 'hr':
			return int(time[:-2]) * 3600
		elif time[-3:] == 'hrs':
			return int(time[:-3]) * 3600
		elif time[-4:] == 'hour':
			return int(time[:-4]) * 3600
		elif time[-5:] == 'hours':
			return int(time[:-5]) * 3600
		elif time[-1] == 'd':
			return int(time[:-1]) * 3600 * 24
		elif time[-3:] == 'day':
			return int(time[:-3]) * 3600 * 24
		elif time[-4:] == 'days':
			return int(time[:-4]) * 3600 * 24
	except ValueError:
		return 'error'
	return 'error'


async def get_role_from_id(guild, roleID):
	for i in guild.roles:
		if str(i.id) == str(roleID):
			return i
	return 'error'

async def get_member_from_id(guild, memberID):
	for i in guild.members:
		if str(i.id) == str(memberID):
			return i
	return 'error'

async def get_guild_from_id(guildID):
	for i in client.guilds:
		if str(i.id) == str(guildID):
			return i
	return 'error'


def time_left(guild, user):
	start = db['servers'][guild]['mutes'][user]['start']
	duration = db['servers'][guild]['mutes'][user]['duration']
	if duration != 'indefinite':
		return int(round(start + duration - time.time(), 0))
	else:
		return 'indefinite'

@client.command()
async def ping(ctx):
	await ctx.send('pong')



async def loop():
	while True:
		await check_mutes()
		await asyncio.sleep(10)

async def check_mutes():
	now = time.time()
	removeMutes = {}
	for guild in db['servers']:
		removeMutes[guild] = []
		for muted in db['servers'][guild]['mutes']:
			if db['servers'][guild]['mutes'][muted]['duration'] != 'indefinite':
				if db['servers'][guild]['mutes'][muted]['start'] + db['servers'][guild]['mutes'][muted]['duration'] <= now:
					target = await get_member_from_id(await get_guild_from_id(guild), muted)
					await target.remove_roles(await get_role_from_id(await get_guild_from_id(guild), db['servers'][guild]['mute']))
					removeMutes[str((await get_guild_from_id(guild)).id)].append(str(target.id))
	for guild in removeMutes:
		for member in removeMutes[guild]:
			del db['servers'][guild]['mutes'][member]
			db.save()


async def check_db():
	for guild in client.guilds:
		if str(guild.id) not in db['servers']:
			db['servers'][str(guild.id)] = {
				'logs':0,
				'mute':0,
				'infractions':{},
				'mutes':{}
			}
			db.save()

@client.event
async def on_ready():
	print('Im in')
	await check_db()
	asyncio.ensure_future(loop())


@client.event
async def on_command_error(ctx, error):
	embed = discord.Embed(color=0xff0000,title='ERROR', description=str(error))
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(5)
	await msg.delete()

@client.event
async def on_guild_join(guild):
	db['servers'][str(guild.id)] = {
		'logs':0,
		'mute':0,
		'infractions':{},
		'mutes':{}
	}
	db.save()



@client.event
async def on_member_join(member):
	if str(member.id) in db['servers'][str(member.guild.id)]['mutes']:
		await member.add_roles(await get_role_from_id(member.guild, db['servers'][str(member.guild.id)]['mute']))
	if db['servers'][str(member.guild.id)]['logs'] != 0:
		await client.get_channel(db['servers'][str(member.guild.id)]['logs']).send(
			embed=discord.Embed(
			title='Member joined!!',
			description='<@' + str(member.id) + '> joined!',
			color=0x00cc00
			).set_thumbnail(url=pfp(member.id))
		)


@client.event
async def on_member_leave(member):
	if db['servers'][str(member.guild.id)]['logs'] != 0:
		await client.get_channel(db['servers'][str(member.guild.id)]['logs']).send(
			embed=discord.Embed(
			title='Member left!!',
			description='<@' + str(member.id) + '> left!',
			color=0xcc0000
			).set_thumbnail(url=pfp(member.id))
		)



@client.event
async def on_message_delete(message):
	if message.channel.type is not discord.ChannelType.private:
		if db['servers'][str(message.guild.id)]['logs'] != 0:
			embed = discord.Embed(
				title='Message deleted!',
				description='Message from: <@' + str(message.author.id) + '>\nIn <#' + str(message.channel.id) + '>',
				color=0xcc0000
			)
			embed.add_field(name='content', value=message.content)
			embed.set_thumbnail(url=pfp(message.author.id))
			await client.get_channel(db['servers'][str(message.guild.id)]['logs']).send(embed=embed)


@client.event
async def on_message_edit(before, after):
	if before.channel.type is not discord.ChannelType.private:
		if db['servers'][str(before.guild.id)]['logs'] != 0:
			if before.author.id != 757277754503856169 and before.content != after.content:
				embed = discord.Embed(
					title='Message edited!',
					description='Message from <@' + str(before.author.id) + '>\nIn <#' + str(before.channel.id) + '>',
					color=0x00cc00
				)
				embed.add_field(name='before', value=before.content)
				embed.add_field(name='after', value=after.content)
				embed.set_thumbnail(url=pfp(before.author.id))
				await client.get_channel(db['servers'][str(before.guild.id)]['logs']).send(embed=embed)


@client.event
async def on_member_ban(guild, user):
	if db['servers'][str(guild.id)]['logs'] != 0:
		embed = discord.Embed(
			title='Banned!',
			description=str(user) + ' has been banned.',
			color=0xcc0000
		).set_thumbnail(url=pfp(user.id))
		await client.get_channel(db['servers'][str(guild.id)]['logs']).send(embed=embed)


@client.event
async def on_member_unban(guild, user):
	if db['servers'][str(guild.id)]['logs'] != 0:
		embed = discord.Embed(
			title='Banned!',
			description=str(user) + ' has been unbanned.',
			color=0x00cc00
		).set_thumbnail(url=pfp(user.id))
		await client.get_channel(db['servers'][str(guild.id)]['logs']).send(embed=embed)




@client.command(aliases=['commands'])
async def help(ctx, catagory=None):
	if catagory == None:
		embed = discord.Embed(
			title='Command Categories',
			color=0x00cc00
		)
		embed.add_field(name='Configuration', value='The commands to set up the bot.', inline=False)
		embed.add_field(name='Infractions', value='The commands to infract someone for being naughty.', inline=False)
		embed.add_field(name='Repealing', value='The commands to repeal an infraction when mods get a little too trigger happy.', inline=False)
		embed.add_field(name='Muting', value='The commands to make people shut up.', inline=False)
		embed.add_field(name='Member', value='The commands for any server member to use.', inline=False)
		embed.set_footer(text='Do `+help category` to view a certain catagory')
		await ctx.send(embed=embed)
	else:
		catagory = catagory.lower()
		if catagory in ['configuration', 'infractions', 'repealing', 'muting', 'member']:
			if catagory == 'configuration':
				embed = discord.Embed(
					title='Configuration Commands',
					color=0x00cc00
				)
				embed.add_field(name='config_logs', value='Choose to which channel I should send the logs.\nIn the form `+config_logs TextChannel`.', inline=False)
				embed.add_field(name='config_mute', value='Choose which role to be addded to a member when muted.\nIn the form `+config_mute Role`.', inline=False)
				embed.set_footer(text='These commands can only be used by server admins')
			elif catagory == 'infractions':
				embed = discord.Embed(
					title='Infraction Commands',
					color=0x00cc00
				)
				embed.add_field(name='warn', value='Warn a member for being naughty.\nIn the form `+warn Member <"reason">`.', inline=False)
				embed.add_field(name='strike', value='sStrike a member for being naughty.\nIn the form `+strike Member <"reason">`.', inline=False)
				embed.add_field(name='infractions', value='View your infractions from this server. Moderators can do `+infractions Member` to view another member\'s infractions. Must allow DMs from me.', inline=False)
				embed.set_footer(text='These commands can only be used by server moderators (except the infractions command)')
			elif catagory == 'repealing':
				embed = discord.Embed(
					title='Repealing Commands',
					color=0x00cc00
				)
				embed.add_field(name='repeal_warn', value='Repeal one of a member\'s warns.\nIn the form `+repeal_warn Member WarnID`.', inline=False)
				embed.add_field(name='repeal_strike', value='Repeal one of a member\'s strikes.\nIn the form `+repeal_strike Member strikeID`.', inline=False)
				embed.set_footer(text='These commands can only be used by server moderators')
			elif catagory == 'muting':
				embed = discord.Embed(
					title='Muting Commands',
					color=0x00cc00
				)
				embed.add_field(name='mute', value='Make a member shut up.\nIn the form `+mute Member <time>`, if a time is omitted, then they will be muted indefinitely.', inline=False)
				embed.add_field(name='unmute', value='Allow a member to speak again.\nIn the form `+mute Member`.', inline=False)
				embed.add_field(name='view_mutes', value='View your current mutes across all the servers that I am in. Must allow DMs from me.', inline=False)
				embed.add_field(name='view_servers_mutes', value='View the current mutes in this server. Must allow DMs from me.', inline=False)
				embed.set_footer(text='These commands can only be used by server moderators (except the view_mutes command)')
			elif catagory == 'member':
				embed = discord.Embed(
					title='Member Commands',
					color=0x00cc00
				)
				embed.add_field(name='infractions', value='View your infractions from this server. Moderators can do `+infractions Member` to view another member\'s infractions. Must allow DMs from me.', inline=False)
				embed.add_field(name='view_mutes', value='View your current mutes across all the servers that I am in. Must allow DMs from me.', inline=False)
				embed.set_footer(text='These commands can only be used by any server member')
			await ctx.send(embed=embed)
		else:
			await ctx.send(
				embed=discord.Embed(
					title='Error',
					description='Category "' + catagory + '" not found.',
					color=0xcc0000
				)
			)
		
	



@client.command()
async def config_logs(ctx,  *, channel: discord.TextChannel=None):
	if ctx.message.author.guild_permissions.administrator:
		if channel != None:
			db['servers'][str(ctx.guild.id)]['logs'] = channel.id
			db.save()
			await ctx.send(
				embed=discord.Embed(
					title='Logs configured!',
					description='The logs channel for this server has been set to <#' + str(channel.id) + '>',
					color=0x00cc00
				)
			)
		else:
			await ctx.send(
				embed=discord.Embed(
					title='Error',
					description='You did not provide a channel',
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
				embed=discord.Embed(
					title='Error',
					description='You are not an admin of this server',
					color=0xcc0000
				)
			)


@client.command()
async def config_mute(ctx,  *, role: discord.Role=None):
	if ctx.message.author.guild_permissions.administrator:
		if role != None:
			db['servers'][str(ctx.guild.id)]['mute'] = role.id
			db.save()
			await ctx.send(
				embed=discord.Embed(
					title='Mute configured!',
					description='The mute role for this server has been set to ' + str(role.mention),
					color=0x00cc00
				)
			)
		else:
			await ctx.send(
				embed=discord.Embed(
					title='Error',
					description='You did not provide a role',
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
				embed=discord.Embed(
					title='Error',
					description='You are not an admin of this server',
					color=0xcc0000
				)
			)

	


@client.command()
async def warn(ctx, member: discord.Member=None, reason=None):
	if ctx.message.author.guild_permissions.manage_messages:
		if member != None:
			if str(member.id) not in db['servers'][str(ctx.guild.id)]['infractions']:
				db['servers'][str(ctx.guild.id)]['infractions'][str(member.id)]= {
					'warns':{},
					'strikes':{}
				}
				db.save()
			warns = db['servers'][str(ctx.guild.id)]['infractions'][str(member.id)]['warns']
			highest = 0
			for warn in warns:
				if int(warn) > highest:
					highest = int(warn)
			db['servers'][str(ctx.guild.id)]['infractions'][str(member.id)]['warns'][str(highest+1)] = {
				'moderator': ctx.author.id,
				'reason':reason,
				'time': time.time()
			}
			db.save()
			await ctx.send(
					embed=discord.Embed(
						title='Warn',
						description=str(member) + ' warned for: **' + str(reason) + '**',
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
					embed=discord.Embed(
						title='Error',
						description='You did not provide a member',
						color=0xcc0000
					)
				)
	else:
		await ctx.send(
				embed=discord.Embed(
					title='Error',
					description='You are not a moderator of this server',
					color=0xcc0000
				)
			)



@client.command()
async def strike(ctx, member: discord.Member=None, reason=None):
	if ctx.message.author.guild_permissions.manage_messages:
		if member != None:
			if str(member.id) not in db['servers'][str(ctx.guild.id)]['infractions']:
				db['servers'][str(ctx.guild.id)]['infractions'][str(member.id)]= {
					'warns':{},
					'strikes':{}
				}
				db.save()
			strikes = db['servers'][str(ctx.guild.id)]['infractions'][str(member.id)]['strikes']
			highest = 0
			for strike in strikes:
				if int(strike) > highest:
					highest = int(strike)
			db['servers'][str(ctx.guild.id)]['infractions'][str(member.id)]['strikes'][str(highest+1)] = {
				'moderator': ctx.author.id,
				'reason':reason,
				'time': time.time()
			}
			db.save()
			await ctx.send(
					embed=discord.Embed(
						title='Strike',
						description=str(member) + ' striked for: **' + str(reason) + '**',
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
					embed=discord.Embed(
						title='Error',
						description='You did not provide a member',
						color=0xcc0000
					)
				)
	else:
		await ctx.send(
				embed=discord.Embed(
					title='Error',
					description='You are not a moderator of this server',
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
		if str(user) in db['servers'][str(guild)]['infractions']:
			infractions = db['servers'][str(guild)]['infractions'][str(user)]

			warns = '**__Warns__**\n'
			for warn in infractions['warns']:
				warns += "Warn id: **" + warn + '**\nReason: **' + str(infractions['warns'][warn]['reason']) + '**\nDate: **' + datetime.datetime.fromtimestamp(infractions['warns'][warn]['time']).strftime('%Y-%m-%d %H:%M:%S') + '**\n\n'

			if warns == '**__Warns__**\n':
				warns += 'Member has never been warned.'

			strikes = '**__Strikes__**\n'
			for strike in infractions['strikes']:
				strikes += "Strike id: **" + strike + '**\nReason: **' + str(infractions['strikes'][strike]['reason']) + '**\nDate: **' + datetime.datetime.fromtimestamp(infractions['strikes'][strike]['time']).strftime('%Y-%m-%d %H:%M:%S') + '**\n\n'

			if strikes == '**__Strikes__**\n':
				strikes += 'Member has never been striked.'
			
			await ctx.author.send(
				embed=discord.Embed(
					title=username + "'s infractions",
					description=warns + '\n\n' + strikes,
					color=0x00cc00
				).set_thumbnail(url=pfp(user))
			)
		else:
			await ctx.author.send(
				embed=discord.Embed(
					title=username + "'s infractions",
					description='Member has never been infracted.',
					color=0x00cc00
				).set_thumbnail(url=pfp(user))
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title='Error',
				description='You are not a moderator of this server',
				color=0xcc0000
			)
		)


@client.command()
async def repeal_warn(ctx, member: discord.Member=None):
	if ctx.message.author.guild_permissions.manage_messages:
		if member != None:
			try:
				num = int(ctx.message.content.split(' ')[-1])
				num = str(num)
				correct = True
			except:
				correct = False
			if correct:
				guildID = str(ctx.guild.id)
				memberID = str(member.id)
				if memberID in  db['servers'][guildID]['infractions']:
					if num in db['servers'][guildID]['infractions'][memberID]['warns']:
						del db['servers'][guildID]['infractions'][memberID]['warns'][num]
						db.save()
					else:
						await ctx.send(
							embed=discord.Embed(
								title='Error',
								description='Warn id **' + num + '** not found',
								color=0xcc0000
							)
						)
				else:
					await ctx.send(
						embed=discord.Embed(
							title='Error',
							description=str(member) + ' has never been infracted',
							color=0xcc0000
						)
					)
			else:
				await ctx.send(
					embed=discord.Embed(
						title='Error',
						description="You didn't provide a real number",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title='Error',
					description="You didn't provide a member",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title='Error',
				description="You don't moderate this server",
				color=0xcc0000
			)
		)


@client.command()
async def repeal_strike(ctx, member: discord.Member=None):
	if ctx.message.author.guild_permissions.manage_messages:
		if member != None:
			try:
				num = int(ctx.message.content.split(' ')[-1])
				num = str(num)
				correct = True
			except:
				correct = False
			if correct:
				guildID = str(ctx.guild.id)
				memberID = str(member.id)
				if memberID in  db['servers'][guildID]['infractions']:
					if num in db['servers'][guildID]['infractions'][memberID]['strikes']:
						del db['servers'][guildID]['infractions'][memberID]['strikes'][num]
						db.save()
					else:
						await ctx.send(
							embed=discord.Embed(
								title='Error',
								description='Strike id **' + num + '** not found',
								color=0xcc0000
							)
						)
				else:
					await ctx.send(
						embed=discord.Embed(
							title='Error',
							description=str(member) + ' has never been infracted',
							color=0xcc0000
						)
					)
			else:
				await ctx.send(
					embed=discord.Embed(
						title='Error',
						description="You didn't provide a real number",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title='Error',
					description="You didn't provide a member",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title='Error',
				description="You don't moderate this server",
				color=0xcc0000
			)
		)



@client.command()
async def mute(ctx, member: discord.Member=None, duration=None):
	if ctx.message.author.guild_permissions.manage_messages:
		if member != None:
			guildID = str(ctx.guild.id)
			if db['servers'][guildID]['mute'] != 0:
				if duration == None:
					duration = 'indefinite'
				else:
					duration = timeStrToSeconds(duration)
				if duration != 'error':
					role = await get_role_from_id(ctx.guild, db['servers'][guildID]['mute'])
					if role != 'error':
						await member.add_roles(role)
						db['servers'][guildID]['mutes'][str(member.id)] = {
							'start': time.time(),
							'duration': duration
						}
						db.save()
						embed=discord.Embed(
							title='Muted',
							description=str(member) + ' has been muted for **' + str(duration) + ' seconds**.',
							color=0x00cc00
						)
						await ctx.send(embed=embed)
						if db['servers'][str(guildID)]['logs'] != 0:
							await client.get_channel(db['servers'][str(guildID)]['logs']).send(embed=embed)
					else:
						await ctx.send(
							embed=discord.Embed(
								title='Error',
								description='Your mute role is set up incorrectly, do `+config_mute Role`.',
								color=0xcc0000
							)
						)
				else:
					await ctx.send(
						embed=discord.Embed(
							title='Error',
							description='You entered the duration incorrectly.',
							color=0xcc0000
						)
					)
			else:
				await ctx.send(
					embed=discord.Embed(
						title='Error',
						description='You have not conigured the mute role yet, do `+config_mute Role`.',
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title='Error',
					description='You did not privide a member.',
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title='Error',
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
			if memberID in db['servers'][guildID]['mutes']:
				await member.remove_roles(await get_role_from_id(ctx.guild, db['servers'][guildID]['mute']))
				del db['servers'][guildID]['mutes'][memberID]
				db.save()
				await ctx.send(
					embed=discord.Embed(
						title='Unmuted',
						description=str(member) + ' has been unmuted.',
						color=0x00cc00
					)
				)
			else:
				await ctx.send(
					embed=discord.Embed(
						title='Error',
						description=str(member) + " is not muted.",
						color=0xcc0000
					)
				)
		else:
			await ctx.send(
				embed=discord.Embed(
					title='Error',
					description="You didn't provide a member to unmute.",
					color=0xcc0000
				)
			)
	else:
		await ctx.send(
			embed=discord.Embed(
				title='Error',
				description="You don't moderate this server",
				color=0xcc0000
			)
		)




@client.command()
async def view_mutes(ctx):
	user = str(ctx.author.id)
	message = ""
	for guild in db['servers']:
		if user in db['servers'][guild]['mutes']:
			message += "**__" + str(await get_guild_from_id(guild)) + "__**\nStart: **" + str(datetime.datetime.fromtimestamp(db['servers'][guild]['mutes'][user]['start']).strftime('%Y-%m-%d %H:%M:%S')) + "**\nDuration: **" + str(db['servers'][guild]['mutes'][user]['duration']) + " seconds**\nTime Left: **" + str(time_left(guild, user)) + " seconds**\n\n"
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
		for user in db['servers'][guild]['mutes']:
			message += "**__" + str(client.get_user(int(user))) + "__**\nStart: **" + str(datetime.datetime.fromtimestamp(db['servers'][guild]['mutes'][user]['start']).strftime('%Y-%m-%d %H:%M:%S')) + "**\nDuration: **" + str(db['servers'][guild]['mutes'][user]['duration']) + " seconds**\nTime Left: **" + str(time_left(guild, user)) + " seconds**\n\n"
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
				title='Error',
				description="You don't moderate this server",
				color=0xcc0000
			)
		)


server.s()
client.run(os.getenv('token'))