import json
import time
import timeit
from importlib import import_module, invalidate_caches
from itertools import permutations
from multiprocessing import Pool
from pathlib import Path
from typing import Callable, Dict, Tuple

from wrapper import Kalah

MAX_GAME_TIME = 20  # seconds



def battle(fmap: Dict[str, Callable]) -> Tuple[Tuple[str, str], Tuple[bool, float]]:
    """Multiprocessing wrapper for the actual strategies' simulation

    :param fmap: {file: func} mapping with 2 keys
    :return: ((filename1, filename2), (winner, score))
    """
    files, funcs = zip(*fmap)
    # b = time.perf_counter()
    # p = Kalah(funcs).play_alpha_beta()
    # e = time.perf_counter()
    p, t = Kalah(funcs).play_alpha_beta()
    # return files, Kalah(funcs).play_alpha_beta()
    # return files, p - 1, e - b
    return files, p-1, t


def check(*, sols_dir: Path, p_num: int = 4):
    """Runs every submitted solution with every other

    :param sols_dir: directory to take solutions from
    :param p_num: number of parallel workers
    :return:
    """

    # to import new modules, which were created
    # during the run of the program
    invalidate_caches()

    sols_dir.mkdir(parents=True, exist_ok=True)

    funcs = {f.stem: import_module(f"{sols_dir}.{f.stem}").func for f in
             filter(lambda f: f.suffix in {".py"}, sols_dir.iterdir())}

    ss = len(funcs) * (len(funcs) - 1)
    b = time.perf_counter()
    # *all_res, = map(battle, permutations(funcs.items(), 2))
    # with ppe(p_num) as p:
    #     *all_res, = p.map(battle, permutations(funcs.items(), 2), chunksize=ss // p_num)
    with Pool(p_num) as p:
        *all_res, = p.imap_unordered(battle, permutations(funcs.items(), 2), chunksize=ss // p_num)
    print("finished testing, now computing scoreboard")
    print(time.perf_counter() - b, "secs")

    score_board = dict.fromkeys(funcs.keys(), 0.0)
    # for fs, (pl, t) in all_res:
    for fs, pl, t in all_res:
        score_board[fs[pl]] += MAX_GAME_TIME - t

    # return score_board

    # # decreasing by score
    score_board_as_list = sorted(score_board.items(), key=lambda tup: -tup[1])
    with Path("result.json").open("w") as f:
        f.write(json.dumps(score_board_as_list))

if __name__ == "__main__":
    # print(timeit.timeit('check(sols_dir=Path("mail_saved"))', number=10, globals={"check": check, "Path": Path}))
    check(sols_dir=Path("mail_saved"))
