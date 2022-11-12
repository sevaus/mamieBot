import discord
from discord.ext import tasks
import rpyc
import datetime
import io
from PIL import Image
import numpy as np
import configs
rpyc.core.protocol.DEFAULT_CONFIG['allow_pickle'] = True

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        conn = rpyc.connect(configs.SERVER_HOST, configs.SERVER_PORT)
        self.conn_root = conn.root

    async def setup_hook(self) -> None:
        """Starts the task to run in the background."""
        self.my_background_task.start()

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("-"*100)

    @tasks.loop(seconds = 1) 
    async def my_background_task(self):
        channel = self.get_channel(configs.DISCORD_CHANNEL_ID)
        message_logs_raw = self.conn_root.get_main_message_logs()
        message_logs = rpyc.utils.classic.obtain(message_logs_raw)
        for i in range(0, len(message_logs)):
            # If the message has not been sent to Discord yet
            message_log = message_logs[i]
            if not message_log["discord"]:
                try:
                    embed = message_log["embed"]
                    embed = {key: embed[key] for key in embed}
                    embed = discord.Embed.from_dict(embed)

                    # Set the image (if any)
                    if "image" in message_log:
                        image = message_log["image"]
                        bytes = io.BytesIO()
                        image.save(bytes, format = "PNG")
                        bytes.seek(0)
                        file = discord.File(bytes, filename = "image.png")    
                        embed.set_image(url = "attachment://image.png")

                    # Set the fields (if any)
                    if "fields" in message_log:
                        for field in message_log["fields"]:
                            embed.add_field(name = field["name"], value = field["value"], inline = field["inline"])

                    # Set the footer
                    embed.set_footer(text = message_log["footer"])
                   
                    # Send the embed
                    if "image" in message_log:
                        await channel.send(embed = embed, file = file)
                    else:
                        await channel.send(embed = embed)

                    # The message has been sent to discord so we flag it
                    message_logs_raw[i]["discord"] = True

                except Exception as e:
                    print(f"{datetime.datetime.now().strftime(configs.DMYHMS_FORMAT)}: Error {e}")        

        message_logs_raw = [message_log for message_log in message_logs if not message_log["discord"]]

    @my_background_task.before_loop
    async def before_my_task(self):
        """Makes it wait until the bot logs in."""
        await self.wait_until_ready()

client = MyClient(intents = discord.Intents.default())
client.run(configs.DISCORD_TOKEN)

