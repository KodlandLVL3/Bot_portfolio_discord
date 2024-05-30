import discord
from discord.ext import commands
from logic import DB_Manager
from config import DATABASE, TOKEN

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)
manager = DB_Manager(DATABASE)

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

@bot.command(name='start')
async def start_command(ctx):
    await ctx.send("Привет! Я бот-менеджер проектов\nПомогу тебе сохранить твои проекты и информацию о них!)")
    await info(ctx)

@bot.command(name='info')
async def info(ctx):
    await ctx.send("""
Вот команды которые могут тебе помочь:

!new_project - используй для добавления нового проекта
!projects - используй для отображения всех проектов
!update_projects - используй для изменения данных о проекте
!skills - используй для привязки навыков к проекту
!delete - используй для удаления проекта

Также ты можешь ввести имя проекта и узнать информацию о нем!""")

@bot.command(name='new_project')
async def new_project(ctx):
    await ctx.send("Введите название проекта:")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    name = await bot.wait_for('message', check=check)
    data = [ctx.author.id, name.content]
    await ctx.send("Введите ссылку на проект")
    link = await bot.wait_for('message', check=check)
    data.append(link.content)

    statuses = [x[0] for x in manager.get_statuses()]
    await ctx.send("Введите текущий статус проекта", delete_after=60.0)
    await ctx.send("\n".join(statuses), delete_after=60.0)
    
    status = await bot.wait_for('message', check=check)
    if status.content not in statuses:
        await ctx.send("Ты выбрал статус не из списка, попробуй еще раз!)", delete_after=60.0)
        return

    status_id = manager.get_status_id(status.content)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    await ctx.send("Проект сохранен")

@bot.command(name='projects')
async def get_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name: {x[2]} \nLink: {x[4]}\n" for x in projects])
        await ctx.send(text)
    else:
        await ctx.send('У тебя пока нет проектов!\nМожешь добавить их с помощью команды !new_project')

@bot.command(name='skills')
async def skills(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send('Выбери проект для которого нужно выбрать навык')
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send('У тебя нет такого проекта, попробуй еще раз!) Выбери проект для которого нужно выбрать навык')
            return

        skills = [x[1] for x in manager.get_skills()]
        await ctx.send('Выбери навык')
        await ctx.send("\n".join(skills))

        skill = await bot.wait_for('message', check=check)
        if skill.content not in skills:
            await ctx.send('Видимо, ты выбрал навык не из списка, попробуй еще раз!) Выбери навык')
            return

        manager.insert_skill(user_id, project_name.content, skill.content)
        await ctx.send(f'Навык {skill.content} добавлен проекту {project_name.content}')
    else:
        await ctx.send('У тебя пока нет проектов!\nМожешь добавить их с помощью команды !new_project')

@bot.command(name='delete')
async def delete_project(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send("Выбери проект, который хочешь удалить")
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send('У тебя нет такого проекта, попробуй выбрать еще раз!')
            return

        project_id = manager.get_project_id(project_name.content, user_id)
        manager.delete_project(user_id, project_id)
        await ctx.send(f'Проект {project_name.content} удален!')
    else:
        await ctx.send('У тебя пока нет проектов!\nМожешь добавить их с помощью команды !new_project')

@bot.command(name='update_projects')
async def update_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send("Выбери проект, который хочешь изменить")
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send("Что-то пошло не так! Выбери проект, который хочешь изменить еще раз:")
            return

        await ctx.send("Выбери, что требуется изменить в проекте")
        attributes = {'Имя проекта': 'project_name', 'Описание': 'description', 'Ссылка': 'url', 'Статус': 'status_id'}
        await ctx.send("\n".join(attributes.keys()))

        attribute = await bot.wait_for('message', check=check)
        if attribute.content not in attributes:
            await ctx.send("Кажется, ты ошибся, попробуй еще раз!")
            return

        if attribute.content == 'Статус':
            statuses = manager.get_statuses()
            await ctx.send("Выбери новый статус проекта")
            await ctx.send("\n".join([x[0] for x in statuses]))
            update_info = await bot.wait_for('message', check=check)
            if update_info.content not in [x[0] for x in statuses]:
                await ctx.send("Был выбран неверный статус, попробуй еще раз!")
                return
            update_info = manager.get_status_id(update_info.content)
        else:
            await ctx.send(f"Введите новое значение для {attribute.content}")
            update_info = await bot.wait_for('message', check=check)
            update_info = update_info.content

        manager.update_projects(attributes[attribute.content], (update_info, project_name.content, user_id))
        await ctx.send("Готово! Обновления внесены!")
    else:
        await ctx.send('У тебя пока нет проектов!\nМожешь добавить их с помощью команды !new_project')

bot.run(TOKEN)
