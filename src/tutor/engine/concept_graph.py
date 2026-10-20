"""The concept dependency graph (spec section 5).

Edges point from a prerequisite to the concept that needs it.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable, Mapping

from tutor.models.content import Concept


class ConceptGraph:
    def __init__(self, concepts: Mapping[str, Concept]):
        self.concepts = dict(concepts)
        self.prereqs: dict[str, list[str]] = {cid: list(c.prerequisites) for cid, c in self.concepts.items()}
        self.dependents: dict[str, list[str]] = {cid: [] for cid in self.concepts}
        for cid, pres in self.prereqs.items():
            for p in pres:
                if p in self.dependents:
                    self.dependents[p].append(cid)

    # --- validation -----------------------------------------------------------

    def undefined_references(self) -> list[tuple[str, str]]:
        """(concept, missing prerequisite) pairs."""
        return [(cid, p) for cid, pres in self.prereqs.items() for p in pres if p not in self.concepts]

    def find_cycle(self) -> list[str] | None:
        """Return one cycle as a list of ids (first == last), or ``None``."""
        WHITE, GREY, BLACK = 0, 1, 2
        color = {cid: WHITE for cid in self.concepts}
        stack: list[str] = []

        def visit(node: str) -> list[str] | None:
            color[node] = GREY
            stack.append(node)
            for p in self.prereqs.get(node, []):
                if p not in color:
                    continue
                if color[p] == GREY:
                    return stack[stack.index(p) :] + [p]
                if color[p] == WHITE:
                    found = visit(p)
                    if found:
                        return found
            stack.pop()
            color[node] = BLACK
            return None

        for cid in sorted(self.concepts):
            if color[cid] == WHITE:
                cycle = visit(cid)
                if cycle:
                    return cycle
        return None

    # --- queries --------------------------------------------------------------------

    def ancestors(self, cid: str) -> set[str]:
        """All direct and indirect prerequisites of ``cid``."""
        seen: set[str] = set()
        queue = deque(self.prereqs.get(cid, []))
        while queue:
            p = queue.popleft()
            if p in seen or p not in self.concepts:
                continue
            seen.add(p)
            queue.extend(self.prereqs.get(p, []))
        return seen

    def topological_order(self, subset: Iterable[str] | None = None) -> list[str]:
        """Kahn's algorithm, prerequisites first; ties broken by (track order, id) for stability."""
        nodes = set(self.concepts if subset is None else subset)
        indeg = {n: sum(1 for p in self.prereqs.get(n, []) if p in nodes) for n in nodes}
        track_rank = {"math": 0, "physics": 1, "electrical": 2, "course_l01": 3, "course_l02": 4, "course_l03": 5}

        def key(n: str) -> tuple[int, str]:
            return (track_rank.get(self.concepts[n].track, 9), n)

        ready = sorted((n for n, d in indeg.items() if d == 0), key=key)
        order: list[str] = []
        while ready:
            n = ready.pop(0)
            order.append(n)
            for d in self.dependents.get(n, []):
                if d in indeg:
                    indeg[d] -= 1
                    if indeg[d] == 0:
                        ready.append(d)
                        ready.sort(key=key)
        if len(order) != len(nodes):
            raise ValueError("Concept graph has a cycle")
        return order

    def path_to(self, cid: str) -> list[str]:
        """Everything needed before ``cid``, in a valid learning order, ending with ``cid``."""
        return self.topological_order(self.ancestors(cid) | {cid})

    def unmastered_prerequisites(self, cid: str, mastered: set[str], direct_only: bool = True) -> list[str]:
        pool = self.prereqs.get(cid, []) if direct_only else sorted(self.ancestors(cid))
        return [p for p in pool if p in self.concepts and p not in mastered]

    def roots(self) -> list[str]:
        return sorted(c for c, p in self.prereqs.items() if not p)

    def grounded_in_foundations(self, cid: str) -> bool:
        """A course concept must build on at least one foundation (math/physics/electrical) concept."""
        if cid not in self.concepts:
            return False
        if self.concepts[cid].track in ("math", "physics", "electrical"):
            return True
        return any(self.concepts[a].track in ("math", "physics", "electrical") for a in self.ancestors(cid))
