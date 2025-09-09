import discord
import os
import sys
from typing import Literal
from discord.ext import commands, tasks
from os.path import join, dirname
from dotenv import load_dotenv

# 環境変数の取得
dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)
guild_id = int(os.environ.get("GUILD_ID"))

# コマンドの本体
class Starter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild = None
        self.nearest_event = None

    @commands.Cog.listener()
    async def on_ready(self):
        # tokenやidの取得
        self.guild = self.bot.get_guild(guild_id)
        await self.bot.tree.sync(guild=self.guild)
        self.nearest_event = await self.get_nearest_event()
        self.check_event_start.start()
    
    # イベントの変更を検知して一番近いイベントを取得
    async def get_nearest_event(self) -> discord.ScheduledEvent | None:
        events = await self.guild.fetch_scheduled_events()
        if not events:
            return None
        events = sorted(events, key=lambda x: x.start_time)
        return events[0]
    
    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        self.nearest_event = await self.get_nearest_event()
        
    @commands.Cog.listener()
    async def on_scheduled_event_update(self, event: discord.ScheduledEvent, after: discord.ScheduledEvent):
        self.nearest_event = await self.get_nearest_event()

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        self.nearest_event = await self.get_nearest_event()
    
    # 最も近いイベントが開始時間になったら開始して通知
    @tasks.loop(minutes=1)
    async def check_event_start(self):
        if not self.nearest_event:
            return
        if self.nearest_event.start_time <= discord.utils.utcnow():
            channel = self.guild.system_channel
            if channel:
                await self.nearest_event.start()
                await channel.send(f"イベント `{self.nearest_event.name}` が開始されました！")
            self.nearest_event = await self.get_nearest_event()
    

async def setup(bot: commands.Bot):
    await bot.add_cog(
        Starter(bot)
    )