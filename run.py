"""
Pygame presentation layer for Minesweeper.

This module owns:
- Renderer: all drawing of cells, header, and result overlays
- InputController: translate mouse input to board actions and UI feedback
- Game: orchestration of loop, timing, state transitions, and composition

The logic lives in components.Board; this module should not implement rules.
"""

import sys

import pygame

import config
from components import Board
from pygame.locals import Rect
import random


class Renderer:
    """Draws the Minesweeper UI.

    Knows how to draw individual cells with flags/numbers, header info,
    and end-of-game overlays with a semi-transparent background.
    """

    def __init__(self, screen: pygame.Surface, board: Board):
        self.screen = screen
        self.board = board
        self.font = pygame.font.Font(config.font_name, config.font_size)
        self.header_font = pygame.font.Font(config.font_name, config.header_font_size)
        self.result_font = pygame.font.Font(config.font_name, config.result_font_size)

    def cell_rect(self, col: int, row: int) -> Rect:
        """Return the rectangle in pixels for the given grid cell."""
        x = config.margin_left + col * config.cell_size
        y = config.margin_top + row * config.cell_size
        return Rect(x, y, config.cell_size, config.cell_size)

    def draw_cell(self, col: int, row: int, highlighted: bool,is_hover: bool,is_hint: bool) -> None:
        """Draw a single cell, respecting revealed/flagged state and highlight."""
        cell = self.board.cells[self.board.index(col, row)]
        rect = self.cell_rect(col, row)
        if cell.state.is_revealed:
            pygame.draw.rect(self.screen, config.color_cell_revealed, rect)
            if cell.state.is_mine:
                pygame.draw.circle(self.screen, config.color_cell_mine, rect.center, rect.width // 4)
            elif cell.state.adjacent > 0:
                color = config.number_colors.get(cell.state.adjacent, config.color_text)
                label = self.font.render(str(cell.state.adjacent), True, color)
                label_rect = label.get_rect(center=rect.center)
                self.screen.blit(label, label_rect)
        else:
           # base_color = config.color_highlight if highlighted else config.color_cell_hidden
            if is_hint:
                base_color = config.color_hint
            elif highlighted:
                base_color = config.color_highlight
            elif is_hover:
                base_color = config.color_cell_hover # 마우스 올렸을 때 색상
            else:
                base_color = config.color_cell_hidden
            pygame.draw.rect(self.screen, base_color, rect)
            if cell.state.is_flagged:
                flag_w = max(6, rect.width // 3)
                flag_h = max(8, rect.height // 2)
                pole_x = rect.left + rect.width // 3
                pole_y = rect.top + 4
                pygame.draw.line(self.screen, config.color_flag, (pole_x, pole_y), (pole_x, pole_y + flag_h), 2)
                pygame.draw.polygon(
                    self.screen,
                    config.color_flag,
                    [
                        (pole_x + 2, pole_y),
                        (pole_x + 2 + flag_w, pole_y + flag_h // 3),
                        (pole_x + 2, pole_y + flag_h // 2),
                    ],
                )
            
        pygame.draw.rect(self.screen, config.color_grid, rect, 1)

    def draw_header(self, remaining_mines: int, time_text: str) -> None:
        """Draw the header bar containing remaining mines and elapsed time."""
        pygame.draw.rect(
            self.screen,
            config.color_header,
            Rect(0, 0, config.width, config.margin_top - 4),
        )
        left_text = f"Mines: {remaining_mines}"
        right_text = f"Time: {time_text}"
        left_label = self.header_font.render(left_text, True, config.color_header_text)
        right_label = self.header_font.render(right_text, True, config.color_header_text)
        self.screen.blit(left_label, (10, 5))
        self.screen.blit(right_label, (config.width - right_label.get_width() - 10, 5))
        #깃발 색상 선택 체크박스
        start_x = 20
        y_pos = 35
        for i, (name, color) in enumerate(config.flag_color_options.items()):
            cb_rect = Rect(start_x + (i * config.checkbox_gap), y_pos, config.checkbox_size, config.checkbox_size)
            
            # 체크박스 테두리
            pygame.draw.rect(self.screen, (200, 200, 200), cb_rect, 2)
            
            # 현재 선택된 색상이면 채우기 (체크 표시 대용)
            if config.color_flag == color:
                pygame.draw.rect(self.screen, color, cb_rect.inflate(-6, -6))
            
            # 색상 이름 텍스트
            color_label = self.font.render(name, True, config.color_header_text) # 첫 글자만 표시하거나 작게 표시
            self.screen.blit(color_label, (cb_rect.right + 5, y_pos - 2))
        hint_rect = Rect(config.hint_button_x, config.hint_button_y, config.hint_button_w, config.hint_button_h)
        pygame.draw.rect(self.screen, config.color_hint_button, hint_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), hint_rect, 2) # 테두리
        
        hint_label = self.font.render("HINT", True, config.color_header_text)
        self.screen.blit(hint_label, hint_label.get_rect(center=hint_rect.center))


    def draw_result_overlay(self, text: str | None) -> None:
        """Draw a semi-transparent overlay with centered result text, if any."""
        if not text:
            return
        overlay = pygame.Surface((config.width, config.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, config.result_overlay_alpha))
        self.screen.blit(overlay, (0, 0))
        label = self.result_font.render(text, True, config.color_result)
        rect = label.get_rect(center=(config.width // 2, config.height // 2))
        self.screen.blit(label, rect)


class InputController:
    """Translates input events into game and board actions."""

    def __init__(self, game: "Game"):
        self.game = game

    def pos_to_grid(self, x: int, y: int):
        """Convert pixel coordinates to (col,row) grid indices or (-1,-1) if out of bounds."""
        if not (config.margin_left <= x < config.width - config.margin_right):
            return -1, -1
        if not (config.margin_top <= y < config.height - config.margin_bottom):
            return -1, -1
        col = (x - config.margin_left) // config.cell_size
        row = (y - config.margin_top) // config.cell_size
        if 0 <= col < self.game.board.cols and 0 <= row < self.game.board.rows:
            return int(col), int(row)
        return -1, -1

    def handle_mouse(self, pos, button) -> None:
        # TODO: Handle mouse button events: left=reveal, right=flag, middle=neighbor highlight  in here
        game = self.game
         #체크박스 클릭시 색상변경
        if pos[1] < config.margin_top:
            if button == config.mouse_left:
                #힌트버튼 클릭 확인
                hint_rect = Rect(config.hint_button_x,config.hint_button_y,config.hint_button_w,config.hint_button_h)
                if hint_rect.collidepoint(pos) and game.started and not game.paused:
                    self.give_hint()
                    return
                start_x = 20
                y_pos = 35
                for i, (name, color) in enumerate(config.flag_color_options.items()):
                    # 클릭 판정 영역 (너비 70으로 넉넉히 잡아야 글자 부분 클릭이 됨)
                    click_area = Rect(start_x + (i * config.checkbox_gap), y_pos, 70, 25)
                    
                    if click_area.collidepoint(pos):
                        config.color_flag = color  # 색상 변경
                        return  # 성공 시 여기서 함수 종료 (아래 지뢰판 로직 실행 방지)
            return # 헤더 영역이면 지뢰판 로직을 실행하지 않고 종료
        col, row = self.pos_to_grid(pos[0], pos[1])
        if col == -1: return

        # 좌클릭(1)수정
        if button == config.mouse_left:
            game.highlight_targets.clear()
            if not game.started:
                game.started = True
                game.start_ticks_ms = pygame.time.get_ticks()
            game.board.reveal(col, row)


        # 게임이 시작 x      
            if not game.started:
                game.started = True
                game.start_ticks_ms = pygame.time.get_ticks()
            game.board.reveal(col, row) # reveal 호출
        
        # 우클릭(3)
        elif button == config.mouse_right:
            game.highlight_targets.clear()
            game.board.toggle_flag(col, row) # 플래그 on/off
        
        # 휠(2)
        elif button == config.mouse_middle:
            neighbors = game.board.neighbors(col, row)
            game.highlight_targets = {
                (nc, nr) for (nc, nr) in neighbors 
                if not game.board.cells[game.board.index(nc, nr)].state.is_revealed
            }
            game.highlight_until_ms = pygame.time.get_ticks() + config.highlight_duration_ms
    def give_hint(self):
        """지뢰가 없는 닫힌 칸 하나를 찾아 힌트로 표시합니다."""
        game = self.game
        safe_cells = []
        
        for r in range(game.board.rows):
            for c in range(game.board.cols):
                cell = game.board.cells[game.board.index(c, r)]
                # 지뢰가 아니고, 열리지 않았고, 깃발도 안 꽂힌 칸 수집
                if not cell.state.is_mine and not cell.state.is_revealed and not cell.state.is_flagged:
                    safe_cells.append((c, r))
        
        if safe_cells:
            game.hint_pos = random.choice(safe_cells)
            # 1초(1000ms) 동안 힌트 표시
            game.hint_until_ms = pygame.time.get_ticks() + 1000

class Game:
    """Main application object orchestrating loop and high-level state."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(config.title)
        self.screen = pygame.display.set_mode(config.display_dimension)
        self.clock = pygame.time.Clock()
        self.board = Board(config.cols, config.rows, config.num_mines)
        self.renderer = Renderer(self.screen, self.board)
        self.input = InputController(self)
        self.highlight_targets = set()
        self.highlight_until_ms = 0
        self.started = False
        self.start_ticks_ms = 0
        self.end_ticks_ms = 0
        self.paused = False #일시정지 상태 변수
        self.paused_start_ticks = 0# 정지된 시점의 시간 기록
        self.hover_pos = (-1, -1)  # 현재 마우스가 위치한 (col, row)
        self.hint_pos = (-1,-1) #현재 힌트로 선택된(col,row)
        self.hint_until_ms=0 #힌트를 표시할 종료 시간

    def reset(self):
        """Reset the game state and start a new board."""
        self.board = Board(config.cols, config.rows, config.num_mines)
        self.renderer.board = self.board
        self.highlight_targets.clear()
        self.highlight_until_ms = 0
        self.started = False
        self.start_ticks_ms = 0
        self.end_ticks_ms = 0
        self.paused = False
        self.paused_start_ticks = 0


    def _elapsed_ms(self) -> int:
        """Return elapsed time in milliseconds (stops when game ends)."""
        if not self.started:
            return 0
        if self.end_ticks_ms:
            return self.end_ticks_ms - self.start_ticks_ms
        #일시정지 중이라면 정지 버튼을 누른 시점까지만 계산
        if self.paused:
            return self.paused_start_ticks - self.start_ticks_ms

        return pygame.time.get_ticks() - self.start_ticks_ms

    def _format_time(self, ms: int) -> str:
        """Format milliseconds as mm:ss string."""
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _result_text(self) -> str | None:
        """Return result label to display, or None if game continues."""
        if self.board.game_over:
            return "GAME OVER"
        if self.board.win:
            return "GAME CLEAR"
        return None

    def draw(self):
        """Render one frame: header, grid, result overlay."""
        if pygame.time.get_ticks() > self.highlight_until_ms and self.highlight_targets:
            self.highlight_targets.clear()
        self.screen.fill(config.color_bg)
        remaining = max(0, config.num_mines - self.board.flagged_count())
        self.renderer.draw_header(remaining, self._format_time(self._elapsed_ms()))
        time_text = self._format_time(self._elapsed_ms())
        self.renderer.draw_header(remaining, time_text)
        now = pygame.time.get_ticks()
      
        mouse_x,mouse_y = pygame.mouse.get_pos()
        hover_col,hover_row = self.input.pos_to_grid(mouse_x,mouse_y)
        
        
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                #미들 클릭 하이라이트 확인
                now = pygame.time.get_ticks()
                is_mid_highlight = (now <= self.highlight_until_ms) and ((c, r) in self.highlight_targets)
                #힌트 하이라이트(현재 시간보다 힌트 종료 시간이 뒤일 때)
                is_hint = (now <= self.hint_until_ms)and(c == self.hint_pos[0] and r== self.hint_pos[1])
                #마우스 오버 하이라이트 확인
                
                is_hover = (c == hover_col and r == hover_row)
                self.renderer.draw_cell(c, r, is_mid_highlight,is_hover,is_hint)
        if self.paused:
            self.renderer.draw_result_overlay("PAUSED")
        else:
            self.renderer.draw_result_overlay(self._result_text())
        pygame.display.flip()

    def run_step(self) -> bool:
        """Process inputs, update time, draw, and tick the clock once."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            #ESC 키를 누르면 일시정지 토글
            if event.type == pygame.KEYDOWN:
                if not self.board.game_over and not self.board.win and self.started:
                        if not self.paused:
                            self.paused = True
                            self.pause_start_ticks = pygame.time.get_ticks()

            if event.type == pygame.MOUSEBUTTONDOWN:
                #일시정지 상태일때
                if self.paused:
                    if event.button == config.mouse_left:
                        pause_duration = pygame.time.get_ticks() - self.pause_start_ticks
                        self.start_ticks_ms += pause_duration
                        self.paused = False
                else:
                    #정지 상태가 아닐 떄만 기존 마우스 핸들러 작동
                    self.input.handle_mouse(event.pos, event.button)
        if (self.board.game_over or self.board.win) and self.started and not self.end_ticks_ms:
            self.end_ticks_ms = pygame.time.get_ticks()
        self.draw()
        self.clock.tick(config.fps)
        return True


def main() -> int:
    """Application entrypoint: run the main loop until quit."""
    game = Game()
    running = True
    while running:
        running = game.run_step()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())