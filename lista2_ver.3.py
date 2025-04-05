import pygame
import time
import copy
import sys

# Gracze
PLAYER_1 = 'B'
PLAYER_2 = 'W'
EMPTY = '_'

# Kierunki ruchu (N, S, E, W)
DIRECTIONS = [(-1, 0), (1, 0), (0, 1), (0, -1)]  # Północ, Południe, Wschód, Zachód

# Wymiary planszy
BOARD_SIZE_X = 5  # 5 wierszy
BOARD_SIZE_Y = 6  # 6 kolumn
CELL_SIZE = 100
SCREEN_WIDTH = BOARD_SIZE_Y * CELL_SIZE
SCREEN_HEIGHT = BOARD_SIZE_X * CELL_SIZE

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (169, 169, 169)

# Klasa reprezentująca stan gry
class GameState:
    def __init__(self, board, current_player):
        self.board = board
        self.current_player = current_player

    def get_opponent(self):
        return PLAYER_2 if self.current_player == PLAYER_1 else PLAYER_1

    def clone(self):
        return GameState(copy.deepcopy(self.board), self.current_player)

    def get_possible_moves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[0])):
                if self.board[r][c] == self.current_player:
                    for dr, dc in DIRECTIONS:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < len(self.board) and 0 <= nc < len(self.board[0]):
                            # Jeśli pole zawiera pionka przeciwnika, to jest to dozwolony ruch
                            if self.board[nr][nc] == self.get_opponent():
                                moves.append(((r, c), (nr, nc)))
        return moves

    def apply_move(self, move):
        (r1, c1), (r2, c2) = move
        new_board = copy.deepcopy(self.board)  # <- bardzo ważne!
        new_board[r2][c2] = self.current_player  # Zastępujemy przeciwnika
        new_board[r1][c1] = EMPTY  # Puste pole po sobie
        return GameState(new_board, self.get_opponent())  # Zwracamy nowy stan gry

    def is_terminal(self):
        return len(self.get_possible_moves()) == 0

    def __str__(self):
        return '\n'.join(' '.join(row) for row in self.board)


# Heurystyki

def heuristic_1(state, player):
    return len(state.get_possible_moves())

def heuristic_2(state, player):
    return sum(row.count(player) for row in state.board)

def heuristic_3(state, player):
    opponent = PLAYER_1 if player == PLAYER_2 else PLAYER_2
    player_count = sum(row.count(player) for row in state.board)
    opponent_count = sum(row.count(opponent) for row in state.board)
    return player_count - opponent_count

HEURISTICS = {
    1: heuristic_1,
    2: heuristic_2,
    3: heuristic_3
}


# Minimax z alfa-beta
def minimax(state, depth, alpha, beta, maximizing, player, heuristic, node_counter):
    node_counter[0] += 1
    if depth == 0 or state.is_terminal():
        return HEURISTICS[heuristic](state, player), None

    best_move = None
    if maximizing:
        max_eval = float('-inf')
        for move in state.get_possible_moves():
            eval, _ = minimax(state.clone().apply_move(move), depth - 1, alpha, beta, False, player, heuristic, node_counter)
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in state.get_possible_moves():
            eval, _ = minimax(state.clone().apply_move(move), depth - 1, alpha, beta, True, player, heuristic, node_counter)
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move


# Funkcja rysująca planszę
def draw_board(game_state, screen):
    for row in range(BOARD_SIZE_X):
        for col in range(BOARD_SIZE_Y):
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            color = GRAY if (row + col) % 2 == 0 else WHITE
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 2)

            piece = game_state.board[row][col]
            if piece == PLAYER_1:
                pygame.draw.circle(screen, BLUE, rect.center, CELL_SIZE // 3)
            elif piece == PLAYER_2:
                pygame.draw.circle(screen, RED, rect.center, CELL_SIZE // 3)


# Funkcja animacji ruchu
def animate_move(game_state, start_pos, end_pos, screen, steps=10):
    r1, c1 = start_pos
    r2, c2 = end_pos
    dx = (c2 - c1) * CELL_SIZE / steps
    dy = (r2 - r1) * CELL_SIZE / steps

    for step in range(steps):
        screen.fill(WHITE)
        draw_board(game_state, screen)

        new_x = c1 * CELL_SIZE + dx * step
        new_y = r1 * CELL_SIZE + dy * step

        if game_state.board[r1][c1] == PLAYER_1:
            pygame.draw.circle(screen, BLUE, (int(new_x + CELL_SIZE // 2), int(new_y + CELL_SIZE // 2)), CELL_SIZE // 3)
        elif game_state.board[r1][c1] == PLAYER_2:
            pygame.draw.circle(screen, RED, (int(new_x + CELL_SIZE // 2), int(new_y + CELL_SIZE // 2)), CELL_SIZE // 3)

        pygame.display.flip()
        pygame.time.delay(50)


# Funkcja oczekiwania na naciśnięcie spacji
def wait_for_space():
    print("\nNaciśnij SPACJĘ, aby kontynuować...")
    while True:
        char = pygame.event.wait()
        if char.type == pygame.KEYDOWN:
            if char.key == pygame.K_SPACE:
                break


# Główna funkcja rozgrywki
def play_game(board, heuristic, depth, interactive=False):
    state = GameState(board, PLAYER_1)
    rounds = 0
    total_nodes = 0
    start_time = time.time()

    screen = None  # <- kluczowe! screen jest widoczny wszędzie

    if interactive:
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Clobber Game")

    while not state.is_terminal():
        node_counter = [0]
        print(f'Runda ----------------------- {rounds}')
        print(state)

        _, move = minimax(state, depth, float('-inf'), float('inf'), True, state.current_player, heuristic, node_counter)
        if move is None:
            break

        if interactive and screen:
            draw_board(state, screen)
            pygame.display.flip()
            animate_move(state, move[0], move[1], screen)
            wait_for_space()

        state = state.apply_move(move)
        rounds += 1
        total_nodes += node_counter[0]

    end_time = time.time()
    print(state)
    print(f"Rundy: {rounds}, Wygrywa: {state.get_opponent()}")
    print(f"Węzły: {total_nodes}", file=sys.stderr)
    print(f"Czas: {end_time - start_time:.2f}s", file=sys.stderr)

    if interactive and screen:
        pygame.quit()


# Funkcja wczytująca planszę z pliku
def read_board(file_path):
    with open(file_path, 'r') as file:
        board = [line.strip().split() for line in file.readlines()]
    return board


# Uruchomienie gry
if __name__ == "__main__":
    board = read_board('plansza.txt')  # Wczytanie planszy z pliku
    play_game(board, 2, 4, interactive=True)  # Uruchomienie gry w trybie interaktywnym
    pygame.quit()
    sys.exit()
