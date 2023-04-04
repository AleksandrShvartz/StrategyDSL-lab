import asyncio
import logging
from pathlib import Path

import battler as bt
from dsl.interpreter import parse_file
from kalah import Kalah
import pandas as pd
import telebot.async_telebot as atb

b = bt.Battler(game_cls=Kalah, game_run="play_alpha_beta")

dummy = Path("mail_test/fedor_novikov.py")
logging.basicConfig(format='%(asctime)s - %(message)s',level=logging.INFO)
bot = atb.AsyncTeleBot("6017129086:AAGdxzhQbVNtOoPjc8gofp_OJS4FhMQ8SoQ")
table = pd.DataFrame({"name": [], "code": [], "score": []})
table.index.name = "id"
save_dir = Path("tourn")
test_dir = Path("tourn_test")
for d in (save_dir, test_dir):
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)


@bot.message_handler(content_types=["text"])
async def get_text_messages(message):
    if message.text == "/start":
        await bot.send_message(
            message.from_user.id, "-Введите /register [Фамилия Имя /группа] для регистрации\n-/template для загрузки шаблона функции"
        )
    elif message.text[:9] == "/register":
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
    elif message.text[:7] == "/rename":
        temp_str = message.text[8:]
        _id, msg = temp_str.split('@')
        await rename(_id, msg)
    elif message.text[:8] == "/send_to":
        temp_str = message.text[9:]
        _id, msg = temp_str.split('@')
        await send_msg_to(_id,msg)
    elif message.text == "/template":
        await send_temp(message)
    else:
        await bot.send_message(message.from_user.id, "Я тебя не понимаю")


@bot.message_handler(content_types=["document"])
async def get_doc_messages(message):
    file_name = message.document.file_name
    file_id_info = await bot.get_file(message.document.file_id)
    downloaded_file = await bot.download_file(file_id_info.file_path)

    save_path = save_dir.joinpath(f"{message.from_user.id}.py")
    test_path = test_dir.joinpath(file_name)

    with open(test_path, "wb") as new_file:
        new_file.write(downloaded_file)
    parsed_test_path = parse_file(test_path)
    if parsed_test_path:
        res = await b.run_dummy(parsed_test_path, dummy, func_name="func")
        if isinstance(res, str):
            await bot.send_message(message.from_user.id, res)
            parsed_test_path.unlink()
            logging.info(f"{res} |user {message.from_user.id}")
        else:
            parsed_test_path.rename(save_path)
            await bot.send_message(message.from_user.id, "Сохранил")
            table.loc[message.from_user.id, "code"] = save_path
            logging.info("Add FILE " + str(message.from_user.id))
    else:
        await bot.send_message(
            message.from_user.id,
            f"Expected file extension '.py', got {Path(file_name).suffix!r}",
        )
        test_path.unlink()


async def send_temp(message):
    await bot.send_document(message.from_user.id, open(r'function_template.py', 'rb'))


async def register(message):
    if len(message.text) < 11:
        await bot.send_message(message.from_user.id, "Некорректное имя")
        return

    table.loc[message.from_user.id, "name"] = message.text[9:]
    await bot.send_message(
        message.from_user.id, f"Сохранил: {message.text[9:]}"
    )
    await bot.send_document(message.chat.id, open(r'function_template.py', 'rb'))
    logging.info(f"Add people - {message.from_user.id} - {message.text[9:]}")


async def rename(id, name):
    logging.info(f"Rename -{id}- to {name}")
    table.loc[int(id), "name"] = name
    await bot.send_message(
        int(id), f"Ваше имя изменено на: {name}"
    )


async def send_msg_to(id, msg):
    logging.info(f"Send msg to -{id}- text -{msg}-")
    await bot.send_message(int(id), msg)


async def save_table():
    table.to_excel("dsl_table.xlsx")
    logging.info("Saving table")


async def load_table():
    temp_table = pd.read_excel("dsl_table.xlsx", index_col="id")
    logging.info("Load table")
    return temp_table


async def print_table():
    print(table)


async def send_text_mes(mes):
    logging.info("Send all msg")
    for user in table.index:
        await bot.send_message(user, mes)


async def send_result(res):
    logging.info("Send results")
    for user_id, score in res.items():
        table.loc[int(user_id), "score"] = score
        await bot.send_message(
            user_id, f"Ваш результат в последнем раунде: {score:.1f}"
        )


async def start_battle():
    logging.info("Battle start")
    await save_table()
    await send_text_mes(
        "Раунд начинается, ваше последнее решение примет участие в турнире"
    )
    b.check_contestants(save_dir, func_name="func")
    await b.run_tournament(n_workers=8)
    res = b.form_results()
    await send_result(res)
    b.save_results(Path("result.json"))


if __name__ == "__main__":
    asyncio.run(bot.polling())
