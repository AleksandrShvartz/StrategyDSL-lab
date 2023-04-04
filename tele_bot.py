import telebot.async_telebot as atb
import pandas as pd
import asyncio
import battler as bt
from pathlib import Path
import os

from dsl.interpreter import parse_file

b = bt.Battler(game_cls=bt.Kalah, game_run="play_alpha_beta")

dummy = Path('mail_test/fedor_novikov.py')

bot = atb.AsyncTeleBot('5998949800:AAGj_6DfBQEbQLe-tC5B78ZdBfy3IG4ALko');
table = pd.DataFrame({
    'name': [],
    'code': [],
    'score': []
})
table.index.name = 'id'
save_dir = 'mail_saved'



@bot.message_handler(content_types=['text'])
async def get_text_messages(message):
    if message.text == "/start":
        await bot.send_message(message.from_user.id, "Введите /register ФАМИЛИЯ_ИМЯ_ГРУППА для регистрации")
    elif message.text[0:9] == "/register":
        await register(message)
    elif message.text == "/start_bt":
        await start_battle()
    elif message.text == "/save_tb":
        await save_table()
    elif message.text == "/load_tb":
        global table
        table = await load_table()
    elif message.text[0:8] == "/send_ms":
        await send_text_mes(message.text[9:])
    elif message.text == "/print_tb":
        await print_table()

    else:
        await bot.send_message(message.from_user.id, "Я тебя не понимаю.")


@bot.message_handler(content_types=['document'])
async def get_doc_messages(message):
    file_name = message.document.file_name
    file_id = message.document.file_name
    file_id_info = await bot.get_file(message.document.file_id)
    downloaded_file = await bot.download_file(file_id_info.file_path)
    src = str(message.from_user.id) + '_test' + '.py'
    old_file = str(message.from_user.id) + '.py'
    save_path = save_dir + "/" + src
    save_path = parse_file(Path(save_path))
    if save_path:
        with open(save_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        res = await b.run_dummy(Path(save_path), dummy, func_name='func')
        if isinstance(res, str):
            await bot.send_message(message.from_user.id, res)
            os.remove(save_path)
        else:
            if os.path.exists(save_dir + "/" + old_file):
                print('Remove old file')
                os.remove(save_dir + "/" + old_file)
            os.rename(save_path, save_dir + "/" + old_file)
            await bot.send_message(message.from_user.id, 'Сохранил')
            table.loc[message.from_user.id, 'code'] = Path(save_dir + "/" + old_file)
            print('Add FILE ' + str(message.from_user.id))
    else:
        await bot.send_message(message.from_user.id, "File has incorrect extension.")


async def register(message):
    if (len(message.text)<11):
        await bot.send_message(message.from_user.id, 'Некорректное имя')
        return
    table.loc[message.from_user.id, 'name'] = message.text[9:len(message.text)]
    await bot.send_message(message.from_user.id, "Можешь загрузить свой файл в любое время")
    print('Add people ' + str(message.from_user.id))


async def save_table():
    table.to_excel('dsl_table.xlsx')
    print('Saving table')


async def load_table():
    temp_table = pd.read_excel('dsl_table.xlsx', index_col='id')
    print('Load table')
    return temp_table


async def print_table():
    print(table)


async def send_text_mes(mes):
    print('Send all msg')
    for user in table.index:
        await bot.send_message(user, mes)


def run_test():
    print("тест")


async def send_result(res):
    print('отпрвка')
    for item in res.items():
        table.loc[int(item[0]), 'score'] = item[1]
        await bot.send_message(item[0], 'Ваш результат в последнем турнире: %.1f' % item[1])



async def start_battle():
    await send_text_mes('Раунд начинается, ваше последнее решение примет участие в турнире')
    b.check_contestants(Path(save_dir), func_name="func")
    await b.run_tournament(n_workers=4, timeout=2.5)
    res = b.form_results();
    await send_result(res)
    b.save_results(Path("result.json"))



if __name__ == "__main__":
    asyncio.run(bot.polling())
