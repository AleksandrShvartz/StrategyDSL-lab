import telebot.async_telebot as atb;
import pandas as pd;
import asyncio;
import battler as bt;
from pathlib import Path


b = bt.Battler(game_cls=bt.Kalah, game_run="play_alpha_beta")

bot = atb.AsyncTeleBot('5998949800:AAGj_6DfBQEbQLe-tC5B78ZdBfy3IG4ALko');
table = pd.DataFrame({
   'name': [],
   'code': [],
   'score': []
})
save_dir = "D:/Documents/temp"

@bot.message_handler(content_types=['text'])
async def get_text_messages(message):
    
    if message.text == "/start":
        bot.send_message(message.from_user.id, "Введите /register ФАМИЛСЯ_ИМЯ_ГРУППА для регистрации")
    elif message.text[0:9] == "/register":
        register(message)
        bot.send_message(message.from_user.id, "Можешь загрузить свой файл в любое время")
        
    elif message.text == "/start_bt":
       start_battle()
        
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю.")




@bot.message_handler(content_types=['document'])
async def get_doc_messages(message):
    file_name = message.document.file_name
    file_id = message.document.file_name
    file_id_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_id_info.file_path)
    src = file_name
    with open(save_dir + "/" + src, 'wb') as new_file:
        new_file.write(downloaded_file)
    bot.send_message(message.from_user.id, 'Сохранил')
    table.loc[message.from_user.id,'code'] = save_dir + "/" + src
    print(table)
    

def register(message):
    table.loc[message.from_user.id] = [message.text[9:len(message.text)], ' ', 0]
    print(table)
    
def save_table():
    table.to_csv('dsl_table.csv')
    
def load_table():
    temp_table = pd.read_csv('dsl_table.csv', sep=',')
    return temp_table

def run_test():
    print("тест")
    

def send_result(res):
    print(res)
    
def start_battle():
    async def _():
        await b.check_contestants(Path("./mail_test"), func_name="func")
        await b.run_tournament(n_workers=4, timeout=2.5)
        await b.form_results()
        await b.save_results(Path("result.json"))

    asyncio.run(_())
    



asyncio.run(bot.polling())

