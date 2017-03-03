from config import config
import discord
import asyncio
import aiohttp
import datetime
import random
import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import textwrap
import os
import uuid
from wand.image import Image as WandImage

dir_path = os.path.dirname(os.path.realpath(__file__)) # File folder path to this script

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    print('Connected servers')
    for serv in client.servers:
        print(serv.name)
    print('------')

class CheckUser():
    async def is_admin(user): # check if user is admin
        roles = []
        for role in user.roles:
            roles.append(role.id)
        if config["ADMIN_ROLE"] in roles:
            return True
        return False

    async def is_member(user):
        roles = []
        for role in user.roles:
            roles.append(role.id)
        if config["MEMBER_ROLE"] in roles:
            return True
        return False

class Spoiler():
    async def send_spoiler_gif(text, content, channel): # send_spoiler_gif(spoiled msg, bot msg, send to channel)
        wrapped = textwrap.wrap(text, 55)
        font = ImageFont.truetype(dir_path + "/aileron_font/Aileron-SemiBold.otf", 13)

        img_cover = Image.new("RGBA", (400, (20 * len(wrapped)) + 20), (64, 64, 64))
        draw_cover = ImageDraw.Draw(img_cover)
        draw_cover.text((10, 10), "( Hover to reveal spoiler )", (160, 160, 160), font=font)

        img_spoiler = Image.new("RGBA", (400, (20 * len(wrapped)) + 20), (64, 64, 64))
        draw_spoiler = ImageDraw.Draw(img_spoiler)
        for i, line in enumerate(wrapped):
            draw_spoiler.text((10, (20 * i) + 10), line, (160, 160, 160), font=font)

        unique = str(uuid.uuid4()) #should be unique enough...
        file_cover = "gif_tmp/img_cover_{}.png".format(unique)
        file_spoiler = "gif_tmp/img_spoiler_{}.png".format(unique)
        file_gif = "gif_tmp/{}.gif".format(unique)

        img_cover.save(file_cover)
        img_spoiler.save(file_spoiler)

        with WandImage() as wand:
            with WandImage(filename=file_cover) as cover:
                wand.sequence.append(cover)
            with WandImage(filename=file_spoiler) as spoiler:
                wand.sequence.append(spoiler)
            for cursor in range(2):
                with wand.sequence[cursor] as frame:
                    frame.delay = cursor * 9999999999999999999999999999999999999999999999999999 # setting a really long delay i guess?
            wand.type = 'optimize'
            wand.save(filename=file_gif)

        os.remove(file_cover)
        os.remove(file_spoiler)

        with open(file_gif, 'rb') as gif:
            await client.send_file(channel, gif, filename="spoiler.gif", content=content)

        os.remove(file_gif)

class Command():
    async def spoiler(message):
        content = message.content[8:]
        msg = "{} has sent a spoiler~".format(message.author.mention)
        channel = message.channel
        await client.delete_message(message)
        await Spoiler.send_spoiler_gif(content, msg, channel)

    async def setspoiler(message):
        if await CheckUser.is_admin(message.author):
            spoiled_message = await client.get_message(message.channel, message.content[12:])
            msg = "{} has marked {}'s message as a spoiler~".format(message.author.mention, spoiled_message.author.mention)
            channel = message.channel
            spoiled_content = spoiled_message.content
            await client.delete_message(message)
            await client.delete_message(spoiled_message)
            await Spoiler.send_spoiler_gif(spoiled_content, msg, channel)

    async def reqspoiler(message):
        role = discord.utils.get(message.server.roles, id=config["SPOILER_ROLE"])
        await client.add_roles(message.author, role)
        await client.send_message(message.channel, "{}, you now have access to the spoiler channel!".format(message.author.mention))

    async def reqmember(message):
        member = message.author
        if member.avatar_url != "":
            avatar = member.avatar_url
        else:
            avatar = member.default_avatar_url

        embed = discord.Embed(title="__Member Role Request__", colour=discord.Colour(0x807bbe), description="{} has requested to obtain the Member Role!\n\n**Begin your voting!**".format(member.name))

        embed.set_author(name="{}".format(member.name), icon_url="{}".format(avatar))
        embed.set_footer(text="User ID: {}".format(member.id))

        embed.add_field(name="👍/👎", value="Agree/Disagree on {}'s member role.".format(member.name), inline=True)
        embed.add_field(name="👌/👇", value="**[Admins Only]** Instantly grant/decline member status to {}.".format(member.name), inline=True)

        staff_channel = discord.utils.get(message.server.channels, id=config["STAFF_CHANNEL"])
        msg = await client.send_message(staff_channel, embed=embed)
        await client.send_message(message.channel, "Your request has been sent! Please wait for the staff's decision on your member request!")

        await client.add_reaction(msg, "👍")
        await client.add_reaction(msg, "👎")
        await client.add_reaction(msg, "👌")
        await client.add_reaction(msg, "👇")

        await client.pin_message(msg)

    async def sponsormember(message):
        if not await CheckUser.is_member(message.author):
            await client.send_message(message.channel, "You are not a member yet! You cannot sponsor a member without having the member role. Why don't you request a membership status with `!reqmember`?")
            return
        if len(message.mentions) == 0:
            await client.send_message(message.channel, "Please mention a user to sponsor membership.")
            return
        sponsormember = message.author
        member = message.mentions[0]
        if member.avatar_url != "":
            avatar = member.avatar_url
        else:
            avatar = member.default_avatar_url

        embed = discord.Embed(title="__Member Role Sponsorship Request__", colour=discord.Colour(0x807bbe), description="{} has requested to sponsor **{}** for the the Member Role!\n\n**Begin your voting!**".format(sponsormember.name, member.name))

        embed.set_author(name="{}".format(member.name), icon_url="{}".format(avatar))
        embed.set_footer(text="User ID: {}".format(member.id))

        embed.add_field(name="👍/👎", value="Agree/Disagree on {}'s member role.".format(member.name), inline=True)
        embed.add_field(name="👌/👇", value="**[Admins Only]** Instantly grant/decline member status to {}.".format(member.name), inline=True)

        staff_channel = discord.utils.get(message.server.channels, id=config["STAFF_CHANNEL"])
        msg = await client.send_message(staff_channel, embed=embed)
        await client.send_message(message.channel, "Your request has been sent! Please wait for the staff's decision on your member sponsorship request!")

        await client.add_reaction(msg, "👍")
        await client.add_reaction(msg, "👎")
        await client.add_reaction(msg, "👌")
        await client.add_reaction(msg, "👇")

        await client.pin_message(msg)

    async def pick(message):
        if message.content.find(' or ') != -1:
            options=message.content[6:].split(' or ')
            choice=random.randint(0, len(options) - 1)
            await client.send_message(message.channel, 'Ummm..... I\'ll go with **' + options[choice] + '**.')
        else:
            await client.send_message(message.channel, "or...?")

class Tumblr(object):
    @classmethod
    async def create(cls):
        self = cls()
        self.post_id = 0
        self.title = ""
        self.content = ""
        self.author = ""
        self.author_img_url = ""
        self.post_url = ""
        self.timestamp = 0

        self.has_new_post = False
        self.ignore_initial = True # we dont want to post on bot initialization
        await self.new_post_task()
        return self

    async def update_latest_post(self):
        tumblr_url = "https://api.tumblr.com/v2/blog/btv-news.tumblr.com/posts?api_key={}&limit=2&filter=text&tag=news".format(config["TUMBLR_API_KEY"])
        async with aiohttp.ClientSession() as session:
            async with session.get(tumblr_url) as resp:
                content = await resp.json()
                if content['meta']['status'] == 200 and content['response']['posts'][0]['id'] != self.post_id:
                    post = content['response']['posts'][0]
                    self.post_id = post['id']
                    if 'post_author' in post:
                        self.author = post['post_author']
                    else:
                        self.author = post['blog_name']
                    self.author_img_url = "http://api.tumblr.com/v2/blog/{}.tumblr.com/avatar/32".format(self.author)
                    self.post_url = post['post_url']
                    self.timestamp = post['timestamp']
                    self.content = self.get_content(post)
                    self.title = self.get_title(post)
                    self.has_new_post = True

    async def new_post_task(self): # runs the check for new post, if exist, post the post
        await self.update_latest_post()
        if self.has_new_post:
            self.has_new_post = False

            if self.ignore_initial:
                self.ignore_initial = False
                return

            tumblr_channel = client.get_channel(str(config["TUMBLR_CHANNEL"]))

            embed = discord.Embed(title=self.title, colour=discord.Colour(0x9412b5), url=self.post_url, description=self.content, timestamp=datetime.datetime.utcfromtimestamp(self.timestamp))

            embed.set_author(name=self.author, url="http://{}.tumblr.com/".format(self.author), icon_url=self.author_img_url)
            #embed.set_footer(text="GMT")

            headlines = [
                "News flash!",
                "Ring ring ring!",
                "Hey you, check this out!",
                "New Tumblr news!",
                "Lets get right into the news!",
                "Oh goodie, what's shaken?!",
                "Today, I bring you this..."
            ]
            await client.send_message(tumblr_channel, random.choice(headlines), embed=embed)

    def get_content(self, post):
        if post['type'] == "text":
            return post['body']
        elif post['type'] == "photo":
            if len(post['caption']) >= 50:
                return post['caption'] + "\n" + post['photos']['alt_sizes'][0]['url']
            else:
                return post['photos']['alt_sizes'][0]['url']
        elif post['type'] == "quote":
            return post['text']
        elif post['type'] == "link":
            return post['description'] + "\n" + post['url']
        elif post['type'] == "chat":
            return post['body']
        elif post['type'] == "audio":
            return post['caption']
        elif post['type'] == "video":
            return post['caption']
        elif post['type'] == "answer":
            return "Answer:\n" + post['answer']
        else:
            return "Error content... This should not have happened!"

    def get_title(self, post):
        if post['type'] == "text":
            return post['title']
        elif post['type'] == "photo":
            if len(post['caption']) < 50:
                return post['caption']
            else:
                return "Photo Post"
        elif post['type'] == "quote":
            return post['quote']
        elif post['type'] == "link":
            return post['title']
        elif post['type'] == "chat":
            return post['title']
        elif post['type'] == "audio":
            return post['track_name'] + " - " + post['artist']
        elif post['type'] == "video":
            return "Video Post"
        elif post['type'] == "answer":
            return post['asking_name'] + " asks, " + post['question']
        else:
            return "Error title... This should not have happened!"

class MemberPromotion():
    async def is_valid_message(message): # check if the message is a promotion request posted by the bot
        if message.author.id == client.user.id:
            for embed in message.embeds:
                if embed['type'] == "rich" and (embed['title'] == "__Member Role Request__" or embed['title'] == "__Member Role Sponsorship Request__"):
                    return True
        return False

    async def run_promotion(reaction, user): # promote user depending on the reaction of admin
        if reaction.emoji == "👌" or reaction.emoji == "👇":
            member_id = reaction.message.embeds[0]["footer"]["text"][9:]
            member = discord.utils.get(reaction.message.server.members, id=member_id)
            role = discord.utils.get(reaction.message.server.roles, id=config["MEMBER_ROLE"])

            if reaction.emoji == "👌":
                #promote to member
                await client.add_roles(member, role)
                await client.send_message(reaction.message.channel, "Member role has been approved for {}#{} by {}.".format(member.name, member.discriminator, user.name))

            if reaction.emoji == "👇":
                #demote member
                await client.remove_roles(member, role)
                await client.send_message(reaction.message.channel, "Member role has been declined for {}#{} by {}".format(member.name, member.discriminator, user.name))
            await client.unpin_message(reaction.message)


@client.event
async def on_message(message):
    # Command Handler - tm of endendragon
    if len(message.content.split()) > 0: #making sure there is actually stuff in the message
        msg_cmd = message.content.split()[0].lower() # get first word im message
        if msg_cmd[0] == config["COMMAND_PREFIX"]: # test for cmd prefix
            msg_cmd = msg_cmd[1:] # remove the command prefix
            cmd = getattr(Command, msg_cmd, None) #check if cmd exist, if not its none
            if cmd: # if cmd is not none...
                await client.send_typing(message.channel) #this looks nice
                await getattr(Command, msg_cmd)(message) #actually run cmd, passing in msg obj

@client.event
async def on_reaction_add(reaction, user):
    if await MemberPromotion.is_valid_message(reaction.message) and await CheckUser.is_admin(user):
        await MemberPromotion.run_promotion(reaction, user)

async def tumblr_background_loop():
    await client.wait_until_ready()
    tumblr = await Tumblr.create()
    while not client.is_closed:
        await tumblr.new_post_task()
        await asyncio.sleep(120)

client.loop.create_task(tumblr_background_loop())
client.run(config['DISCORD_BOT_TOKEN'])
