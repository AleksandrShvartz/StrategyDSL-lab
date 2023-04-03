# cython: language_level=3, boundscheck=False

cdef inline void transfer_stones(list state, int pos, char* trt) noexcept:
    cdef char num_stones = state[pos]
    cdef int i
    state[pos], pos = 0, trt[pos]
    for i in range(num_stones):
        state[pos] += 1
        pos = trt[pos]

DEF __h = 7
DEF __depth = 5
cdef char[13] __trt13 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 0]
cdef char[14] __trt6 = [1, 2, 3, 4, 5, 7, 100, 8, 9, 10, 11, 12, 13, 0]
cdef list __zer = [0, 0, 0, 0, 0, 0]

cdef class Kalah:
    cdef list current_state
    cdef bint player
    cdef object f1, f2

    def __cinit__(self, f1, f2):
        self.current_state = [6, 6, 6, 6, 6, 6, 0, 6, 6, 6, 6, 6, 6, 0]
        self.player = 0
        self.f1 = f1
        self.f2 = f2

    cdef char _is_end(self) noexcept:
        if not sum(self.current_state[:6]):
            self.current_state[13] = 72 - self.current_state[6]
            self.current_state[7:13] = __zer
            return 1
        elif not sum(self.current_state[7:13]):
            self.current_state[6] = 72 - self.current_state[13]
            self.current_state[:6] = __zer
            return 1
        return 0

    cdef (short, char) max_alpha_beta(self, char deep, short alpha, short beta):
        cdef int i
        cdef short maxv = -1990
        cdef char h = -1
        cdef list tmp

        if deep == __depth or self._is_end():
            return (self.f2 if self.player else self.f1)(self.current_state.copy()), 0

        for i in range(6):
            if self.current_state[i]:
                tmp = self.current_state.copy()
                transfer_stones(self.current_state, i, __trt13)

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

    cdef short min_alpha_beta(self, char deep, short alpha, short beta):
        cdef int i
        cdef short minv = 1990
        cdef list tmp
        cdef char _

        if deep == __depth or self._is_end():
            return (self.f2 if self.player else self.f1)(self.current_state.copy())

        for i in range(7, 13):
            if self.current_state[i]:
                tmp = self.current_state.copy()
                transfer_stones(self.current_state, i, __trt6)

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
        cdef short h, _

        while not self._is_end():
            _, h = self.max_alpha_beta(0, -2000, 2000)
            transfer_stones(self.current_state, h, __trt13)

            self.current_state[:__h], self.current_state[__h:] = \
                self.current_state[__h:], self.current_state[:__h]
            self.player ^= 1

        if self.current_state[6] == self.current_state[13]:
            return .5, .5
        return (0, 1) if self.current_state[6] < self.current_state[13] ^ self.player else (1, 0)
