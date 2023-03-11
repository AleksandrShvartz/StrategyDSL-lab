import json
import sys
import time
import timeit
from collections import defaultdict
from importlib import import_module, invalidate_caches
from itertools import permutations
from multiprocessing import Pool, TimeoutError as mpTE
from pathlib import Path
from typing import Callable, Dict, Tuple

from wrapper import Kalah

MAX_GAME_TIME = 20  # seconds


def battle(red: Dict[str, Callable], blue: Dict[str, Callable]) -> Tuple[Tuple[str, str], Tuple[float, float], float]:
    """Multiprocessing wrapper for the actual strategies' simulation

    :param red: (filename, func) of the 1st player
    :param blue: (filename, func) of the 2nd player
    :return: ((filename1, filename2), (score), time)
    """
    files, funcs = zip(red, blue)
    score, t = Kalah(funcs).play_alpha_beta()
    return files, score, t


def calc_score(res, *, save=True):
    score = defaultdict(float)
    for (r, b), (rs, bs), _t in res:
        score[r] += rs * (MAX_GAME_TIME - _t)
        score[b] += bs * (MAX_GAME_TIME - _t)
    if save:
        score_board_as_list = sorted(score.items(), key=lambda tup: -tup[1])
        with Path("result.json").open("w") as f:
            f.write(json.dumps(score_board_as_list))
    return score


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

    b = time.perf_counter()
    all_res = []
    with Pool(p_num) as pool:
        res = [pool.apply_async(battle, funcs) for funcs in permutations(funcs.items(), 2)]
        for r in res:
            try:
                all_res.append(r.get(timeout=MAX_GAME_TIME))
            except mpTE as e:
                print("TIMEOUT", e, file=sys.stderr)
                pass
            except Exception as e:
                print(e, file=sys.stderr)

    print("finished testing, now computing scoreboard")
    print(time.perf_counter() - b, "secs")

    return calc_score(all_res)


if __name__ == "__main__":
    # print(timeit.timeit('check(sols_dir=Path("mail_saved"))', number=10, globals={"check": check, "Path": Path}))
    check(sols_dir=Path("mail_saved"))
