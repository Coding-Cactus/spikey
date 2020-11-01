import discord, os, server, time, datetime
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



@client.event
async def on_ready():
	print('Im in')


@client.event
async def on_guild_join(guild):
	db['servers'][str(guild.id)] = {
		'logs':0,
		'infractions':{}
	}
	db.save()



@client.event
async def on_member_join(member):
	if db['servers'][str(member.guild.id)]['logs'] != 0:
		await client.get_channel(db['servers'][str(member.guild.id)]['logs']).send(
			embed=discord.Embed(
			title='Member joined!!',
			description='<@' + str(member.id) + '> joined!',
			color=0x00cc00
			)
		)


@client.event
async def on_member_leave(member):
	if db['servers'][str(member.guild.id)]['logs'] != 0:
		await client.get_channel(db['servers'][str(member.guild.id)]['logs']).send(
			embed=discord.Embed(
			title='Member left!!',
			description=str(member) + ' left!',
			color=0xcc0000
			)
		)	


@client.event
async def on_message_delete(message):
	if db['servers'][str(message.guild.id)]['logs'] != 0:
		embed = discord.Embed(
			title='Message deleted!',
			description='Message from: <@' + str(message.author.id) + '>\nContent: ' + message.content,
			color=0xcc0000
		)
		await client.get_channel(db['servers'][str(message.guild.id)]['logs']).send(embed=embed)


@client.event
async def on_message_edit(before, after):
	if db['servers'][str(before.guild.id)]['logs'] != 0:
		if before.author.id != 757277754503856169 and before.content != after.content:
			embed = discord.Embed(
				title='Message edited!',
				description='Message from <@' + str(before.author.id) + '>\nIn <#' + str(before.channel.id) + '>\n\nOriginal content:\n\t' + before.content + '\n\nNew content:\n\t' + after.content,
				color=0x00cc00
			)
			await client.get_channel(db['servers'][str(before.guild.id)]['logs']).send(embed=embed)


@client.event
async def on_guild_channel_create(channel):
	if db['servers'][str(channel.guild.id)]['logs'] != 0:
		embed = discord.Embed(
			title='Channel created!',
			description=str(channel) + ' was created.',
			color=0x00cc00
		)
		await client.get_channel(db['servers'][str(channel.guild.id)]['logs']).send(embed=embed)


@client.event
async def on_guild_channel_delete(channel):
	if db['servers'][str(channel.guild.id)]['logs'] != 0:
		embed = discord.Embed(
			title='Channel deleted!',
			description=str(channel) + ' was deleted.',
			color=0xcc0000
		)
		await client.get_channel(db['servers'][str(channel.guild.id)]['logs']).send(embed=embed)


@client.event
async def on_guild_role_create(role):
	if db['servers'][str(role.guild.id)]['logs'] != 0:
		embed = discord.Embed(
			title='Role created!',
			description=role.name + ' was created.',
			color=0x00cc00
		)
		await client.get_channel(db['servers'][str(role.guild.id)]['logs']).send(embed=embed)


@client.event
async def on_guild_role_delete(role):
	if db['servers'][str(role.guild.id)]['logs'] != 0:
		embed = discord.Embed(
			title='Role deleted!',
			description=role.name + ' was deleted.',
			color=0xcc0000
		)
		await client.get_channel(db['servers'][str(role.guild.id)]['logs']).send(embed=embed)


@client.event
async def on_guild_role_update(before, after):	
	if db['servers'][str(before.guild.id)]['logs'] != 0:
		desc = ''
		if before.name != after.name:
			desc += '\nName Change:\n  Before: ' + before.name + '\n  After: ' + after.name
		if before.hoist != after.hoist:
			desc += '\nHoist Change:\n  Before: ' + str(before.hoist) + '\n  After: ' + str(after.hoist)
		if before.position != after.position:
			desc += '\nPosition Change:\n  Before: ' + str(before.position) + '\n  After: ' + str(after.position)
		if before.mentionable != after.mentionable:
			desc += '\nMentionable Change:\n  Before: ' + str(before.mentionable) + '\n  After: ' + str(after.mentionable)
		if before.permissions != after.permissions:
			desc += '\nPermitions Change:\n  Before: ' + str(before.permissions) + '\n  After: ' + str(after.permissions)
		if before.color != after.color:
			desc += '\nColour Change:\n  Before: ' + str(before.color) + '\n  After: ' + str(after.color)
		embed = discord.Embed(
			title='The role `'+before.name+'` changed!',
			description=desc,
			color=0xcc0000
		)
		await client.get_channel(db['servers'][str(before.guild.id)]['logs']).send(embed=embed)


@client.event
async def on_member_ban(guild, user):
	if db['servers'][str(guild.id)]['logs'] != 0:
		embed = discord.Embed(
		title='Banned!',
		description=str(user) + ' has been banned.',
		color=0xcc0000
		)
		await client.get_channel(db['servers'][str(guild.id)]['logs']).send(embed=embed)


@client.event
async def on_member_unban(guild, user):
	if db['servers'][str(guild.id)]['logs'] != 0:
		embed = discord.Embed(
		title='Banned!',
		description=str(user) + ' has been unbanned.',
		color=0x00cc00
		)
		await client.get_channel(db['servers'][str(guild.id)]['logs']).send(embed=embed)








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
						description=str(member) + ' warned for: **' + reason + '**',
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
						description=str(member) + ' striked for: **' + reason + '**',
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
async def infractions(ctx):
	guild = ctx.guild.id
	user = ctx.author.id

	if str(user) in db['servers'][str(guild)]['infractions']:
		infractions = db['servers'][str(guild)]['infractions'][str(user)]

		warns = '**__Warns__**\n'
		for warn in infractions['warns']:
			warns += "Warn id: **" + warn + '**\nReason: **' + str(infractions['warns'][warn]['reason']) + '**\nDate: **' + datetime.datetime.fromtimestamp(infractions['warns'][warn]['time']).strftime('%Y-%m-%d %H:%M:%S') + '**\n\n'

		strikes = '**__Strikes__**\n'
		for strike in infractions['strikes']:
			strikes += "Strike id: **" + strike + '**\nReason: **' + str(infractions['strikes'][strike]['reason']) + '**\nDate: **' + datetime.datetime.fromtimestamp(infractions['strikes'][strike]['time']).strftime('%Y-%m-%d %H:%M:%S') + '**\n\n'
		
		await ctx.author.send(
			embed=discord.Embed(
				title=str(ctx.author) + "'s infractions",
				description=warns + '\n\n' + strikes,
				color=0x00cc00
			).set_thumbnail(url=pfp(user))
		)




server.s()
client.run(os.getenv('token'))