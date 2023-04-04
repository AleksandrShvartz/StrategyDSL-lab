import asyncio
from pathlib import Path

import battler as bt
from dsl.interpreter import parse_file
from kalah import Kalah
import pandas as pd
import telebot.async_telebot as atb

b = bt.Battler(game_cls=Kalah, game_run="play_alpha_beta")

dummy = Path("mail_test/fedor_novikov.py")

bot = atb.AsyncTeleBot("5998949800:AAGj_6DfBQEbQLe-tC5B78ZdBfy3IG4ALko")
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
            message.from_user.id, "Введите /register ФАМИЛИЯ_ИМЯ_ГРУППА для регистрации"
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
        else:
            parsed_test_path.rename(save_path)
            await bot.send_message(message.from_user.id, "Сохранил")
            table.loc[message.from_user.id, "code"] = save_path
            print("Add FILE " + str(message.from_user.id))
    else:
        await bot.send_message(
            message.from_user.id,
            f"Expected file extension '.py', got {Path(file_name).suffix!r}",
        )
        test_path.unlink()


async def register(message):
    if len(message.text) < 11:
        await bot.send_message(message.from_user.id, "Некорректное имя")
        return
    table.loc[message.from_user.id, "name"] = message.text[9:]
    await bot.send_message(
        message.from_user.id, "Можешь загрузить свой файл в любое время"
    )
    print("Add people " + str(message.from_user.id))


async def save_table():
    table.to_excel("dsl_table.xlsx")
    print("Saving table")


async def load_table():
    temp_table = pd.read_excel("dsl_table.xlsx", index_col="id")
    print("Load table")
    return temp_table


async def print_table():
    print(table)


async def send_text_mes(mes):
    print("Send all msg")
    for user in table.index:
        await bot.send_message(user, mes)


def run_test():
    print("тест")


async def send_result(res):
    print("отправка")
    for user_id, score in res.items():
        table.loc[user_id, "score"] = score
        await bot.send_message(
            user_id, f"Ваш результат в последнем турнире: {score:.1f}"
        )


async def start_battle():
    await send_text_mes(
        "Раунд начинается, ваше последнее решение примет участие в турнире"
    )
    b.check_contestants(save_dir, func_name="func")
    await b.run_tournament()
    res = b.form_results()
    await send_result(res)
    b.save_results(Path("result.json"))


if __name__ == "__main__":
    asyncio.run(bot.polling())
