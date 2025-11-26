"""
Core game logic for Minesweeper.

This module contains pure domain logic without any pygame or pixel-level
concerns. It defines:
- CellState: the state of a single cell
- Cell: a cell positioned by (col,row) with an attached CellState
- Board: grid management, mine placement, adjacency computation, reveal/flag

The Board exposes imperative methods that the presentation layer (run.py)
can call in response to user inputs, and does not know anything about
rendering, timing, or input devices.
"""

import random
from typing import List, Tuple


class CellState:
    """Mutable state of a single cell.

    Attributes:
        is_mine: Whether this cell contains a mine.
        is_revealed: Whether the cell has been revealed to the player.
        is_flagged: Whether the player flagged this cell as a mine.
        adjacent: Number of adjacent mines in the 8 neighboring cells.
    """

    def __init__(self, is_mine: bool = False, is_revealed: bool = False, is_flagged: bool = False, adjacent: int = 0):
        self.is_mine = is_mine
        self.is_revealed = is_revealed
        self.is_flagged = is_flagged
        self.adjacent = adjacent


class Cell:
    """Logical cell positioned on the board by column and row."""

    def __init__(self, col: int, row: int):
        self.col = col
        self.row = row
        self.state = CellState()


class Board:
    """Minesweeper board state and rules.

    Responsibilities:
    - Generate and place mines with first-click safety
    - Compute adjacency counts for every cell
    - Reveal cells (iterative flood fill when adjacent == 0)
    - Toggle flags, check win/lose conditions
    """

    def __init__(self, cols: int, rows: int, mines: int):
        self.cols = cols
        self.rows = rows
        self.num_mines = mines
        self.cells: List[Cell] = [Cell(c, r) for r in range(rows) for c in range(cols)]
        self._mines_placed = False
        self.revealed_count = 0
        self.game_over = False
        self.win = False

    def index(self, col: int, row: int) -> int:
        """Return the flat list index for (col,row)."""
        return row * self.cols + col

    def is_inbounds(self, col: int, row: int) -> bool:
        # TODO: Return True if (col,row) is inside the board bounds.
        return 0 <= col < self.cols and 0 <= row < self.rows

    def neighbors(self, col: int, row: int) -> List[Tuple[int, int]]:
        # TODO: Return list of valid neighboring coordinates around (col,row).
        deltas = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0),            (1, 0),
            (-1, 1),  (0, 1),  (1, 1),
        ]
        result = []
        for c,r in deltas:
            n_c = col + c 
            n_r = row + r
            # 범위 체크
            if self.is_inbounds(n_c,n_r):
                result.append((n_c,n_r))
        return result

    def place_mines(self, safe_col: int, safe_row: int) -> None:
        # TODO: Place mines randomly, guaranteeing the first click and its neighbors are safe. And Compute adjacency counts
        # 지뢰 배치 좌표 목록
        all_positions = [(c, r) for r in range(self.rows) for c in range(self.cols)]
        # 맨 처음 클릭한 셸의 좌표와 이웃 셸을 금지 구역 설정
        forbidden = {(safe_col, safe_row)} | set(self.neighbors(safe_col, safe_row))
        # 그 외 지뢰를 둘 수 있는 셸 리스트
        pool = [p for p in all_positions if p not in forbidden]
        random.shuffle(pool)

        # 지뢰 둘 위치 선택
        mine_positions = pool[:self.num_mines]
        
        # 지뢰 적용
        for c, r in mine_positions:
            self.cells[self.index(c, r)].state.is_mine = True
       
       # Compute adjacency counts ( 인접한 지뢰 수 계산 )
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[self.index(c,r)] # cell 객체 반환
                
                 # 지뢰가 아닌 셀에 대해서만 계산
                if not cell.state.is_mine:
                    mine_count = 0
                    # 주변 8칸 순회
                    for nc, nr in self.neighbors(c, r):
                        # 이웃 셀이 지뢰인지 확인
                        if self.cells[self.index(nc, nr)].state.is_mine:
                            mine_count += 1
                    cell.state.adjacent = mine_count
        
        self._mines_placed = True

    def reveal(self, col: int, row: int) -> None:
        # TODO: Reveal a cell; if zero-adjacent, iteratively flood to neighbors.
        if not self.is_inbounds(col, row):
            return
        
        if not self._mines_placed:
            self.place_mines(col, row)
        
        cell = self.cells[self.index(col,row)]
        
        # 오픈되어 잇거나 깃발 둔 상태 처리
        if cell.state.is_revealed or cell.state.is_flagged:
            return
        
        cell.state.is_revealed=True
        self.revealed_count+=1

        # 지뢰이면
        if cell.state.is_mine:
            self.game_over=True
            self._reveal_all_mines()
            return
                # 5. 연쇄 개방 (Flood Fill): 인접 지뢰가 0개라면 주변 셀을 재귀적으로 오픈
        if cell.state.adjacent == 0:
            for nc, nr in self.neighbors(col, row):
                self.reveal(nc, nr) # 재귀 호출

        self._check_win()

    def toggle_flag(self, col: int, row: int) -> None:
        # TODO: Toggle a flag on a non-revealed cell.
        if not self.is_inbounds(col, row):
            return
        
        cell = self.cells[self.index(col,row)]
        if cell.state.is_revealed:
            return

        # 플래그 토글
        cell.state.is_flagged = not cell.state.is_flagged
        
        self._check_win()

    def flagged_count(self) -> int:
        # TODO: Return current number of flagged cells.
        count = 0
        for cell in self.cells:
               if cell.state.is_flagged:
                count+=1
        return count

    def _reveal_all_mines(self) -> None:
        """Reveal all mines; called on game over."""
        for cell in self.cells:
            if cell.state.is_mine:
                cell.state.is_revealed = True

    def _check_win(self) -> None:
        """Set win=True when all non-mine cells have been revealed."""
        total_cells = self.cols * self.rows
        if self.revealed_count == total_cells - self.num_mines and not self.game_over:
            self.win = True
            for cell in self.cells:
                if not cell.state.is_revealed and not cell.state.is_mine:
                    cell.state.is_revealed = True
