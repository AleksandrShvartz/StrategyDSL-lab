from utils import timed


class Kalah:
    __tup = (0, 0, 0, 0, 0, 0)
    __p1r = slice(0, 6)
    __p2r = slice(7, 13)
    __r = range(14)
    __h = 7
    __depth = 5

    def __init__(self, funcs):
        self.current_state = [6, 6, 6, 6, 6, 6, 0, 6, 6, 6, 6, 6, 6, 0]
        self.player = 0
        self.fs = funcs

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

    def _transfer_stones(self, pos, ign=13):

        num_stones, self.current_state[pos] = self.current_state[pos], 0
        pos += 1

        if ign == 13:
            for _ in range(num_stones):
                if pos == 13:
                    pos = 0
                self.current_state[pos], pos = self.current_state[pos] + 1, pos + 1
        else:
            for _ in range(num_stones):
                if pos == 6:
                    pos = 7
                if pos == 14:
                    pos = 0
                self.current_state[pos], pos = self.current_state[pos] + 1, pos + 1

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
                self._transfer_stones(i, ign=6)

                m, _ = self.max_alpha_beta(deep + 1, alpha, beta)
                if m < minv:
                    minv = m

                self.current_state = tmp

                if minv <= alpha:
                    return minv

                if minv < beta:
                    beta = minv

        return minv

    @timed
    def play_alpha_beta(self):
        while not self.is_end():
            _, h = self.max_alpha_beta(0, -2000, 2000)
            self._transfer_stones(h)

            self.current_state[:self.__h], self.current_state[self.__h:] = \
                self.current_state[self.__h:], self.current_state[:self.__h]
            self.player ^= 1
        # print(self.current_state[6] == self.current_state[13])
        # changing sign affects the results table
        # bcoz the equality isn't taken into account
        return self.player ^ (self.current_state[6] > self.current_state[13])


def main():
    from pathlib import Path
    from importlib import import_module
    d = Path("mail_saved")
    a = import_module(f"{d}.fedor_novikov").func
    b = import_module(f"{d}.alex_sachuk_yandex_ru").func
    g = Kalah((a, b))

    return g.play_alpha_beta()


if __name__ == "__main__":
    print(main())
