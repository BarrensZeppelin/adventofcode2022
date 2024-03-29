# pyright: reportSelfClsParameterName=none, reportGeneralTypeIssues=none

from __future__ import annotations

import math
import re
import sys
from collections import Counter, defaultdict, deque
from functools import lru_cache, total_ordering
from heapq import heapify, heappop, heappush, heappushpop, heapreplace
from itertools import combinations
from itertools import combinations_with_replacement as combr
from itertools import cycle, permutations, product, repeat
from typing import (Any, Callable, Collection, DefaultDict, Generic, Hashable,
                    Iterable, Iterator, Mapping, Sequence, TypeVar)

sys.setrecursionlimit(1 << 30)

# E N W S
DIR = ((1, 0), (0, 1), (-1, 0), (0, -1))
HEXDIR = ((2, 0), (1, 1), (-1, 1), (-2, 0), (-1, -1), (1, -1))
OCTDIR = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))


def ints(inp: str | None = None) -> Iterator[int]:
    return map(int, re.findall(r"-?\d+", inp or sys.stdin.read()))


def floats(inp: str | None = None) -> Iterator[float]:
    return map(float, re.findall(r"-?\d+(?:\.\d*)?", inp or sys.stdin.read()))


def lines(inp: str | None = None) -> list[str]:
    return (inp or sys.stdin.read()).splitlines()


def prints(*args, copy=len(sys.argv) == 1):
    """
    Function for printing the solution to a puzzle.
    Also copies the solution to the clipboard.
    """
    from subprocess import run

    ans = " ".join(map(str, args))
    print(ans)
    if copy:
        run(["xsel", "-bi"], input=ans, check=True, text=True)
        print("(Copied to clipboard)")


T = TypeVar("T", int, float)


def sign(x: T) -> int:
    return (x > 0) - (x < 0)


@total_ordering
class Point(Generic[T]):
    c: list[T]
    __slots__ = ("c",)

    def __init__(self, c: list[T] | tuple[T, ...]):
        if isinstance(c, tuple): c = list(c)
        self.c = c

    @classmethod
    def of(cls, *c: T) -> Point[T]:
        return cls(list(c))

    # Points are generally immutable except that you can set coordinates

    @property
    def x(s) -> T:
        return s.c[0]

    @x.setter
    def x(s, v: T):
        s.c[0] = v

    @property
    def y(s) -> T:
        return s.c[1]

    @y.setter
    def y(s, v: T):
        s.c[1] = v

    @property
    def z(s) -> T:
        return s.c[2]

    @z.setter
    def z(s, v: T):
        s.c[2] = v

    # Standard object methods

    def __lt__(s, o: Point[T]) -> bool:
        return s.c < o.c

    def __eq__(s, o) -> bool:
        return isinstance(o, Point) and s.c == o.c

    def __hash__(s) -> int:
        return hash(tuple(s.c))

    def __str__(s) -> str:
        return f'({", ".join(map(str, s))})'

    def __repr__(s) -> str:
        return f"Point({s.c})"

    def __len__(s) -> int:
        return len(s.c)

    def __iter__(s) -> Iterator[T]:
        return iter(s.c)

    def __getitem__(s, key):
        return s.c[key]

    # Geometry stuff

    def __add__(s, o: Iterable[T]) -> Point[T]:
        return Point([a + b for a, b in zip(s, o)])

    def __sub__(s, o: Iterable[T]) -> Point[T]:
        return Point([a - b for a, b in zip(s, o)])

    def __neg__(s) -> Point[T]:
        return Point([-x for x in s])

    def __abs__(s) -> Point[T]:
        return Point.of(*map(lambda x: abs(x), s))

    def __mul__(s, d: T) -> Point[T]:
        return Point([a * d for a in s])

    __rmul__ = __mul__

    def __floordiv__(s, d: T) -> Point[T]:
        return Point([a // d for a in s])

    def __truediv__(s, d: T) -> Point[float]:
        return Point([a / d for a in s])

    def dot(s, o: Iterable[T]) -> T:
        return sum(a * b for a, b in zip(s, o))

    __matmul__ = dot

    def cross(a, b: Point[T]) -> T:
        assert len(a) == 2
        return a.x * b.y - a.y * b.x

    def cross2(s, a: Point[T], b: Point[T]) -> T:
        "Positive result ⇒  b is left of s -> a"
        return (a - s).cross(b - s)

    def cross_3d(a, b: Point[T]) -> Point[T]:
        assert len(a) == 3
        return Point.of(
            a.y * b.z - a.z * b.y, -a.x * b.z + a.z * b.x, a.x * b.y - a.y * b.x
        )

    def cross2_3d(s, a: Point[T], b: Point[T]) -> Point[T]:
        return (a - s).cross_3d(b - s)

    def manh_dist(s) -> T:
        return sum(map(lambda x: abs(x), s))

    def dist2(s) -> T:
        return sum(x * x for x in s)

    def dist(s) -> float:
        return s.dist2() ** 0.5

    def angle(s) -> float:
        assert len(s) == 2
        return math.atan2(s.y, s.x)

    def perp(s) -> Point[T]:
        "Rotate ccw 90°"
        assert len(s) == 2
        return Point([-s.y, s.x])

    def rotate(s, a: float) -> Point[float]:
        assert len(s) == 2
        co, si = math.cos(a), math.sin(a)
        return Point([s.x * co - s.y * si, s.x * si + s.y * co])


_N = TypeVar("_N", bound=Hashable)


def bfs(
    adj: Mapping[_N, Iterable[_N]], *starts: _N
) -> tuple[dict[_N, int], list[_N], dict[_N, _N]]:
    assert starts

    D = {}
    Q = []
    prev: dict[_N, _N] = {}
    for s in starts:
        D[s] = 0
        Q.append(s)
        prev[s] = s

    for i in Q:
        d = D[i]
        for j in adj[i]:
            if j not in D:
                D[j] = d + 1
                prev[j] = i
                Q.append(j)
    return D, Q, prev


def topsort(adj: Mapping[_N, Iterable[_N]]) -> tuple[list[_N], bool]:
    "Flag is true iff. graph is cyclic"
    indeg: defaultdict[_N, int] = defaultdict(int)
    for i, l in adj.items():
        indeg[i] += 0  # make sure all nodes are in indeg
        for j in l:
            indeg[j] += 1
    Q = [i for i in adj if indeg[i] == 0]
    for i in Q:
        for j in adj[i]:
            indeg[j] -= 1
            if indeg[j] == 0:
                Q.append(j)
    return Q, len(Q) != len(indeg)


_U = TypeVar("_U")


def tile(L: Sequence[_U], S: int) -> list[Sequence[_U]]:
    assert len(L) % S == 0
    return [L[i : i + S] for i in range(0, len(L), S)]


def rotate(M: Iterable[Iterable[_U]], times=1) -> list[list[_U]]:
    "Rotate matrix ccw"
    for _ in range(times % 4):
        M = list(map(list, zip(*M)))[::-1]  # type: ignore
    return M  # type: ignore


def print_coords(L: Collection[tuple[int, int]], empty=" "):
    import collections.abc

    xs, ys = zip(*L)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    print("X", min_x, max_x)
    print("Y", min_y, max_y)

    R = [[empty] * (max_x - min_x + 1) for _ in range(max_y - min_y + 1)]

    if isinstance(L, collections.abc.Mapping):
        for (x, y), c in L.items():
            assert len(c) == 1, ((x, y), c)
            R[y - min_y][x - min_x] = c
    else:
        for x, y in L:
            R[y - min_y][x - min_x] = "#"

    print(*map("".join, R), sep="\n")


def neighbours(
    x: int, y: int, dirs: Iterable[tuple[int, int]] = DIR, V=None
) -> Iterator[tuple[int, int]]:
    for dx, dy in dirs:
        nx, ny = x + dx, y + dy
        if V is None or (nx, ny) in V:
            yield nx, ny
