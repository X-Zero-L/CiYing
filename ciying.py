import asyncio
from playwright.async_api import async_playwright
from hoshino import Service
from hoshino.typing import CQEvent, HoshinoBot
import base64

sv_help = '''
词影游戏
[CY|词影 四字成语] 开始游戏
[CY|词影 reset] 重置游戏
[CY|词影 show] 查看当前游戏状态
源网站：https://cy.surprising.studio/
'''.strip()

sv = Service('ciying', enable_on_default=True, help_=sv_help)

ciying_instances = {}
ciying_instance_locks = {}

async def get_ciying_instance(group_id):
    if group_id not in ciying_instances:
        ciying_instances[group_id] = await Ciying.create()
    return ciying_instances[group_id]

async def destroy_ciying_instance(group_id):
    if group_id in ciying_instances:
        await ciying_instances[group_id].browser.close()
        await ciying_instances[group_id].playwright.stop()
        del ciying_instances[group_id]

class Ciying:
    def __init__(self):
        pass
    
    async def async_setup(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 480, "height": 800},
        )
        self.page = await self.context.new_page()
        await self.prepare()
    
    @classmethod
    async def create(cls):
        instance = cls()
        await instance.async_setup()
        return instance
    
    async def check_text_exists(self, text: str):
        locator = self.page.locator(f'text="{text}"')
        count = await locator.count()
        return count > 0
    
    async def get_screenshot(self):
        img = await self.page.screenshot(type="png")
        img = base64.b64encode(img).decode()
        img = f"[CQ:image,file=base64://{img}]"
        return img
    
    async def prepare(self):    
        await self.page.goto("https://cy.surprising.studio/")   
        await self.close_background()
        await self.close_tutorial()

    async def round(self, idiom: str):
        await self.input_idiom(idiom)
        if await self.game_over():
            return True,await self.get_answer()
        return False, await self.get_screenshot()

    async def input_idiom(self, idiom: str):
        await self.page.locator("input").first.fill(idiom[0:4])
        await self.page.locator("input:nth-child(4)").first.press("Enter")
        await self.page.wait_for_timeout(2000)
    
    async def game_over(self):
        await self.page.wait_for_timeout(1000)
        if await self.check_text_exists("再来一局"):
            await self.page.wait_for_timeout(1000)
            await self.page.locator(".absolute > div > .relative > .absolute").click()
            return True
        return False

    async def get_answer(self):
        await self.page.wait_for_selector('text="再来一局"')
        if await self.check_text_exists("再来一局"):
            await self.page.wait_for_timeout(1000)
            return await self.get_screenshot()
        return False

    async def close_background(self):
        await self.page.wait_for_selector('text="故事背景"')
        is_exists = await self.check_text_exists("故事背景")
        if is_exists:
            async with asyncio.Lock():
                while is_exists:
                    await self.page.locator("div:nth-child(3) > div > .relative > .absolute").nth(0).click()
                    await asyncio.sleep(0.5)
                    is_exists = await self.check_text_exists("故事背景")
            return True
        
    async def close_tutorial(self):
        await self.page.wait_for_timeout(2000)
        await self.page.wait_for_selector('text="词影"')
        is_exists = await self.check_text_exists("词影")
        if is_exists:
            while is_exists:
                await self.page.locator(".flex > .relative > .absolute").nth(0).click()
                await self.page.wait_for_timeout(2000)
                is_exists = await self.check_text_exists("新版词影")
            return True

async def reset_ciying_instance(bot, ev, group_id):
    lock = ciying_instance_locks.setdefault(group_id, asyncio.Lock())
    async with lock:
        await destroy_ciying_instance(group_id)
        await bot.send(ev, "已重置")


async def show_screenshot(bot, ev, group_id):
    lock = ciying_instance_locks.setdefault(group_id, asyncio.Lock())
    async with lock:
        ciying_instance = await get_ciying_instance(group_id)
        img = await ciying_instance.get_screenshot()
        await bot.send(ev, img)


async def play_round(bot, ev, group_id, idiom):
    lock = ciying_instance_locks.setdefault(group_id, asyncio.Lock())
    async with lock:
        ciying_instance = await get_ciying_instance(group_id)
        status, img = await ciying_instance.round(idiom)
        if status:
            await destroy_ciying_instance(group_id)
    await bot.send(ev, img)

def is_chinese_character(char):
    return u'\u4e00' <= char <= u'\u9fff'

@sv.on_prefix(('CY', '词影'))
async def ciying(bot: HoshinoBot, ev: CQEvent):
    group_id = ev.group_id
    if not group_id:
        await bot.send(ev, "请在群聊中使用")
        return
    idiom = ev.message.extract_plain_text().strip()
    if not idiom:
        await bot.send(ev, sv_help)
        return
    if idiom == "重置" or idiom == "reset":
        await reset_ciying_instance(bot, ev, group_id)
        return
    if idiom == "show" or idiom == "截图":
        await show_screenshot(bot, ev, group_id)
        return
    if len(idiom) != 4:
        await bot.send(ev, "请输入四字成语")
        return
    if not all(is_chinese_character(char) for char in idiom):
        await bot.send(ev, "请输入汉字")
        return
    await play_round(bot, ev, group_id, idiom)