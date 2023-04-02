class Kalah:
    __tup = (0, 0, 0, 0, 0, 0)
    __p1r = slice(0, 6)
    __p2r = slice(7, 13)
    __r = range(14)
    __h = 7
    __depth = 5
    __trt13 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 0)  # 13th is never visited
    __trt6 = (1, 2, 3, 4, 5, 7, 200, 8, 9, 10, 11, 12, 13, 0)  # 200 is never visited

    def __init__(self, f1, f2):
        self.current_state = [6, 6, 6, 6, 6, 6, 0, 6, 6, 6, 6, 6, 6, 0]
        self.player = 0
        self.fs = (f1, f2)

    def is_end(self):
        if not sum(self.current_state[self.__p1r]):
            self.current_state[13] = 72 - self.current_state[6]
            self.current_state[self.__p2r] = self.__tup
            return True
        elif not sum(self.current_state[self.__p2r]):
            self.current_state[6] = 72 - self.current_state[13]
            self.current_state[self.__p1r] = self.__tup
            return True
        return False

    def _transfer_stones(self, pos, trt=__trt13):
        num_stones, self.current_state[pos] = self.current_state[pos], 0
        pos = trt[pos]
        for _ in range(num_stones):
            self.current_state[pos] += 1
            pos = trt[pos]

    def max_alpha_beta(self, deep, alpha, beta):
        maxv = -1990
        h = None

        if deep == self.__depth or self.is_end():
            return self.fs[self.player](self.current_state.copy()), 0

        for i in self.__r[self.__p1r]:
            if self.current_state[i]:
                tmp = self.current_state.copy()
                self._transfer_stones(i)

                m = self.min_alpha_beta(deep + 1, alpha, beta)
                if m > maxv:
                    maxv = m
                    h = i
                self.current_state = tmp

                if maxv >= beta:
                    return maxv, h

                if maxv > alpha:
                    alpha = maxv

        return maxv, h

    def min_alpha_beta(self, deep, alpha, beta):
        minv = 1990

        if deep == self.__depth or self.is_end():
            return self.fs[self.player](self.current_state.copy())

        for i in self.__r[self.__p2r]:
            if self.current_state[i]:
                tmp = self.current_state.copy()
                self._transfer_stones(i, trt=self.__trt6)

                m, _ = self.max_alpha_beta(deep + 1, alpha, beta)
                if m < minv:
                    minv = m

                self.current_state = tmp

                if minv <= alpha:
                    return minv

                if minv < beta:
                    beta = minv

        return minv

    def play_alpha_beta(self) -> tuple[float, float]:
        while not self.is_end():
            _, h = self.max_alpha_beta(0, -2000, 2000)
            self._transfer_stones(h)

            self.current_state[:self.__h], self.current_state[self.__h:] = \
                self.current_state[self.__h:], self.current_state[:self.__h]
            self.player ^= 1

        if self.current_state[6] == self.current_state[13]:
            return .5, .5
        return (0, 1) if self.current_state[6] < self.current_state[13] ^ self.player else (1, 0)


def main(a, b) -> tuple[float, float]:
    # from pathlib import Path
    # from importlib import import_module
    # d = Path("mail_saved")
    # a = import_module(f"{d}.fedor_novikov").func
    # b = import_module(f"{d}.alex_sachuk_yandex_ru").func
    g = Kalah(a, b)

    return g.play_alpha_beta()


if __name__ == "__main__":
    import typing

    assert typing.get_args(typing.get_type_hints(Kalah.__dict__["play_alpha_beta"])["return"]) == (float, float)
    print(main())
