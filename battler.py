import json
import sys
import time
import warnings
from collections import defaultdict
from copy import deepcopy
from enum import Enum, IntEnum
from importlib import import_module, invalidate_caches, reload
from itertools import permutations
from multiprocessing import Pool, TimeoutError as mpTE
from pathlib import Path
from typing import Callable, Tuple, Any, get_type_hints, get_args
from tqdm.asyncio import tqdm_asyncio
from kalah import Kalah
import aiofiles
from concurrent.futures import ProcessPoolExecutor
import asyncio
from concurrent.futures import TimeoutError


class _State(IntEnum):
    DUMMY = 0,
    INITED = 1,
    CHECKED = 2,
    RAN_TOURNAMENT = 3,
    GOT_RESULTS = 4


class Battler:

    @staticmethod
    def __state_dec(non_valid, after_state, err_msg):
        def wrapper(func):
            def inner_wrapper(self, *a, **kw):
                if self.__state < non_valid:
                    raise RuntimeError(err_msg)
                res = func(self, *a, **kw)
                self.__state = after_state
                return res

            return inner_wrapper

        return wrapper

    def __init__(self, *, game_run: Callable[[Any], Tuple[float, float]] | str, game_cls: Any = None):
        self.__funcs = {}
        self.__score = {}
        self.__results = []
        self.__f, self.__c = Battler.__check_correctness(game_run, game_cls)
        self.__state = _State.INITED

    @staticmethod
    def __check_correctness(game_run, game_cls):
        ret_type_str = tuple[float, float]
        ret_type = (float, float)
        if game_cls is None:
            if isinstance(game_run, str):
                raise TypeError(f"Passed function {game_run!r} should be Callable")
            template = f"Passed function {game_run.__name__!r}"
            if not isinstance(game_run, Callable):
                raise TypeError(f"{template} is not callable")
            if get_type_hints(game_run).get("return", None) is None:
                raise TypeError(f"{template} must have annotations of type \'{ret_type_str}\'")
            if get_args(get_type_hints(game_run)["return"]) != ret_type:
                raise ValueError(f"{template} should have \'{ret_type_str}\' as annotations")
            return game_run, None
        else:
            template = f"Passed class {game_cls.__name__!r}"
            if not isinstance(game_cls, object):
                raise TypeError(f"{template} is not a class")
            if not isinstance(game_run, str):
                raise ValueError(f"Passed {game_run!r} should be of {str!r} type")
            if not hasattr(game_cls, game_run):
                raise AttributeError(f"{template} doesn't have {game_run!r} as its method")
            meth = getattr(game_cls, game_run)
            m_template = f"Method {game_run!r}"
            if get_type_hints(meth).get("return", None) is None:
                raise TypeError(f"{m_template} must have annotations of type \'{ret_type_str}\'")
            if get_args(get_type_hints(meth)["return"]) != ret_type:
                raise ValueError(f"{m_template} should have \'{ret_type_str}\' as annotations")
            return game_run, game_cls

    def _battle(self, files_n_funcs: Tuple[Tuple[str, Callable]]) -> Tuple[Tuple[str, str], Tuple[float, float]]:
        files, funcs = zip(*files_n_funcs)
        try:
            # cython __cinit__
            score = getattr(self.__c.__new__(self.__c, *funcs), self.__f)() if self.__c else self.__f(*funcs)
        except AttributeError:
            # python __init__ as a fallback
            score = getattr(self.__c(*funcs), self.__f)() if self.__c else self.__f(*funcs)
        except Exception:
            score = 0, 0
        return files, score

    @staticmethod
    def __import_func(module: Path, func_name: str):
        imodule = "no module loaded yet"
        try:
            rel_p = module.absolute().relative_to(Path.cwd())
            m_dir, m_name = rel_p.parent.name, rel_p.stem
            module_name = f"{m_dir and f'{m_dir}.' or ''}{m_name}"
            imodule = import_module(module_name)

            # leave only non dunder keys (hopefully, user defined)
            for k in tuple(imodule.__dict__):
                if not k.startswith("__"):
                    imodule.__dict__.pop(k)
            # if not called, uses the cached file contents
            reload(imodule)
            return imodule.__dict__[func_name]
        except ValueError:
            print(f"Path {module.absolute()!r} is not a subpath of {Path.cwd()!r}", file=sys.stderr)
        except KeyError as e:
            print(f"Error importing {e} function from module {imodule!r}", file=sys.stderr)
            e.args = f'`{func_name}` function is missing',
            raise e

    @__state_dec(_State.DUMMY, _State.CHECKED, "Wow, you've nailed it")
    def check_contestants(self, sols_dir: Path, func_name: str, suffixes: set[str] = None):
        # to import new modules, which were created
        # during the run of the program
        invalidate_caches()

        if suffixes is None:
            suffixes = {".py"}
        self.__funcs = {}
        for file in filter(lambda f: f.suffix in suffixes, sols_dir.iterdir()):
            try:
                self.__funcs[file.stem] = Battler.__import_func(file, func_name)
            except Exception as e:
                print(e, file=sys.stderr)

    async def run_dummy(self, user_func: Path | Callable, dummy: Path | Callable, *, func_name: str = None,
                        timeout: float = 1) -> Tuple[Tuple[str, str], Tuple[float, float]] | str:
        # to import new modules, which were created
        # during the run of the program
        invalidate_caches()

        if (isinstance(user_func, Path) or isinstance(dummy, Path)) and func_name is None:
            raise ValueError("Function name should be string when passing paths")
        funcs = []
        for user_func, f_name in zip((user_func, dummy), ("User func", "Dummy func")):
            if isinstance(user_func, Path):
                f_name = user_func.stem
                try:
                    user_func = Battler.__import_func(user_func, func_name)
                except Exception as e:
                    return f"Raised exception during import: {e.__class__.__name__}: {e}"
            funcs.append((f_name, user_func))

        try:
            return await asyncio.gather(
                *(asyncio.wait_for(asyncio.to_thread(self._battle, args), timeout=timeout) for args in
                  (funcs, funcs[::-1])))
        except TimeoutError:
            return "Timed out"
        except Exception as e:
            return f"Raised exception during test run: {e}"

    @__state_dec(_State.CHECKED, _State.RAN_TOURNAMENT, f"Please load contestants before launching a tournament")
    async def run_tournament(self, *, n_workers: int | None = None):
        def _check(what, name, l_lim, u_lim):
            warn_template = "{} is not in [{}, {}], changed to {}"
            if not u_lim >= what >= l_lim:
                what = min(max(what, l_lim), u_lim)
                warnings.warn(warn_template.format(name, l_lim, u_lim, what))
            return what

        # add these as constants?
        n_workers = n_workers is not None and _check(n_workers, "n_workers", 1, 8) or None

        start_time = time.perf_counter()
        executor = ProcessPoolExecutor(max_workers=n_workers)
        loop = asyncio.get_event_loop()
        self.__results = await tqdm_asyncio.gather(
            *(loop.run_in_executor(executor, self._battle, funcs) for funcs in
              permutations(self.__funcs.items(), 2)))

        print(f"Tournament with {(n := len(self.__funcs)) * (n - 1)} battles "
              f"ended in {time.perf_counter() - start_time:.3f} secs")

    @__state_dec(_State.RAN_TOURNAMENT, _State.GOT_RESULTS, f"Please launch a tournament before getting the results")
    def form_results(self):
        self.__score = defaultdict(float)
        for (red, blue), (red_score, blue_score) in self.__results:
            self.__score[red] += red_score
            self.__score[blue] += blue_score
        return deepcopy(self.__score)

    @__state_dec(_State.GOT_RESULTS, _State.DUMMY, f"Please collect the results first `form_results`")
    def save_results(self, dst: Path, *, desc=True) -> None:
        """Sort the results and save them in .json format

        :param dst: path to save results to
        :param desc: if True, sort in descending order, else ascending
        :return: None
        """
        with open(dst, "w") as f:
            f.write(json.dumps(sorted(self.__score.items(), key=lambda tup: (1, -1)[desc] * tup[1])))


if __name__ == "__main__":
    import asyncio

    b = Battler(game_cls=Kalah, game_run="play_alpha_beta")
    from function_template import func


    async def _():
        print(await b.run_dummy(Path("mail_saved/alex_sachuk_yandex_ru.py"), func, func_name="func"))
        b.check_contestants(Path("./mail_saved"), func_name="func")
        await b.run_tournament()
        b.form_results()
        b.save_results(Path("result.json"))


    asyncio.run(_())
