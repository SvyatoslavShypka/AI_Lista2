import argparse
import pygame
import time
import copy
import sys
import random

# Gracze
PLAYER_1 = 'B'
PLAYER_2 = 'W'
EMPTY = '_'

# Kierunki ruchu (N, S, E, W)
KIERUNKI = [(-1, 0), (1, 0), (0, 1), (0, -1)]

# Kolory
YELLOW_GROUND = (225, 238, 18)
BROWN_GROUND = (87, 47, 38)
BORDER = (169, 169, 169)
CZARNY = (0, 0, 0)
BIALY = (255, 255, 255)

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
        for y in range(len(self.board)):
            for x in range(len(self.board[0])):
                if self.board[y][x] == self.current_player:
                    for dy, dx in KIERUNKI:
                        new_y, new_x = y + dy, x + dx
                        if 0 <= new_y < len(self.board) and 0 <= new_x < len(self.board[0]):
                            if self.board[new_y][new_x] == self.get_opponent():
                                moves.append(((y, x), (new_y, new_x)))
        return moves

    def apply_move(self, move):
        (r1, c1), (r2, c2) = move
        new_board = copy.deepcopy(self.board)
        new_board[r2][c2] = self.current_player
        new_board[r1][c1] = EMPTY
        return GameState(new_board, self.get_opponent())

    def is_finish(self):
        return len(self.get_possible_moves()) == 0

    def __str__(self):
        return '\n'.join(' '.join(row) for row in self.board)

# Zwraca liczbę możliwych ruchów gracza w danym stanie gry. /Im więcej ruchów gracz może wykonać, tym lepiej./
# + Prosta i szybka, nadaje się na początek gry.
# - Nie rozróżnia stanów o tej samej liczbie ruchów, ale bardzo różnych sytuacjach strategicznych.
def heuristic_1(state, player):
    return len(state.get_possible_moves())

# Ocenia łączną liczbę pionków gracza na planszy. Im więcej pionków gracz ma, tym lepiej.
# + Dobra do późniejszych etapów gry, gdzie eliminacja przeciwnika się liczy.
# - Ignoruje, czy pionki mogą się ruszać — pionki „uwięzione” też się liczą.
def heuristic_2(state, player):
    return sum(row.count(player) for row in state.board)

# Ocenia różnicę między liczbą pionków gracza a przeciwnika. /bilans sił/
# + Uwzględnia siłę przeciwnika, nie tylko własną.
# - Nie uwzględnia ruchliwości pionków, ani pozycji – tylko liczby.
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

def minimax(state, depth, alpha, beta, maximizing, player, heuristic, node_counter):
    node_counter[0] += 1
    if depth == 0 or state.is_finish():
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

def draw_board(game_state, screen):
    for row in range(BOARD_SIZE_Y):
        for col in range(BOARD_SIZE_X):
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            color = BROWN_GROUND if (row + col) % 2 == 0 else YELLOW_GROUND
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BORDER, rect, 2)

            pionek = game_state.board[row][col]
            if pionek == PLAYER_1:
                pygame.draw.circle(screen, BIALY, rect.center, CELL_SIZE // 3)
            elif pionek == PLAYER_2:
                pygame.draw.circle(screen, CZARNY, rect.center, CELL_SIZE // 3)

def animate_move(game_state, start_pos, end_pos, screen, steps=10):
    r1, c1 = start_pos
    r2, c2 = end_pos
    dx = (c2 - c1) * CELL_SIZE / steps
    dy = (r2 - r1) * CELL_SIZE / steps

    for step in range(steps):
        screen.fill(YELLOW_GROUND)
        draw_board(game_state, screen)
        new_x = c1 * CELL_SIZE + dx * step
        new_y = r1 * CELL_SIZE + dy * step

        if game_state.board[r1][c1] == PLAYER_1:
            pygame.draw.circle(screen, BIALY, (int(new_x + CELL_SIZE // 2), int(new_y + CELL_SIZE // 2)), CELL_SIZE // 3)
        elif game_state.board[r1][c1] == PLAYER_2:
            pygame.draw.circle(screen, CZARNY, (int(new_x + CELL_SIZE // 2), int(new_y + CELL_SIZE // 2)), CELL_SIZE // 3)

        pygame.display.flip()
        pygame.time.delay(50)

def choose_move(state, player_settings, node_counter):
    moves = state.get_possible_moves()
    if player_settings["random"] and random.random() < 0.3:
        return random.choice(moves) if moves else None
    _, move = minimax(state, player_settings["depth"], float('-inf'), float('inf'),
                      True, state.current_player, player_settings["heuristic"], node_counter)
    return move

def play_game(board, p1_settings, p2_settings, interactive):
    state = GameState(board, PLAYER_1)
    rounds = 0
    total_nodes = 0
    start_time = time.time()

    screen = None
    if interactive:
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Clobber Game")

    while not state.is_finish():
        # Listy w Pythonie są mutowalne (mutable) na odmianę z int - dla rekursji odnosimy się do tej że listy
        node_counter = [0]
        print(f'Runda {rounds}')
        print(state)

        current_settings = p1_settings if state.current_player == PLAYER_1 else p2_settings
        move = choose_move(state, current_settings, node_counter)
        if move is None:
            break

        if interactive and screen:
            draw_board(state, screen)
            pygame.display.flip()
            animate_move(state, move[0], move[1], screen)
        # robimy ruch
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

def read_board(file_path):
    with open(file_path, 'r') as file:
        board = [line.strip().split() for line in file.readlines()]
    return board

if __name__ == "__main__":
    # TEST
    # AI vs AI, obaj optymalni
    # python lista2_extended.py --player1-strategy 1 --player2-strategy 2 --interactive

    # Jeden AI „głupi” Player1, drugi inteligentny
    # U player1 ruchy są losowe, czyli nie używa minimaxa, a tzn nie analizuje przyszłości!
    # python lista2_extended.py --player1-strategy 3 --player1-random --player2-strategy 1 --player2-depth 5 --interactive

    parser = argparse.ArgumentParser()
    parser.add_argument('--board', type=str, default='plansza.txt')
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--player1-strategy', type=int, default=2)
    parser.add_argument('--player2-strategy', type=int, default=2)
    parser.add_argument('--player1-depth', type=int, default=4)
    parser.add_argument('--player2-depth', type=int, default=4)
    parser.add_argument('--player1-random', action='store_true')
    parser.add_argument('--player2-random', action='store_true')
    args = parser.parse_args()

    board = read_board(args.board)
    n, m = len(board), len(board[0])
    if n * m % 2 != 0:
        print(f"Plansza {n}x{m} nieprawidłowa", file=sys.stderr)
        sys.exit(1)

    BOARD_SIZE_Y = n
    BOARD_SIZE_X = m
    CELL_SIZE = 80
    SCREEN_WIDTH = BOARD_SIZE_X * CELL_SIZE
    SCREEN_HEIGHT = BOARD_SIZE_Y * CELL_SIZE

    player1 = {
        "heuristic": args.player1_strategy,
        "depth": args.player1_depth,
        "random": args.player1_random
    }

    player2 = {
        "heuristic": args.player2_strategy,
        "depth": args.player2_depth,
        "random": args.player2_random
    }

    play_game(board, player1, player2, args.interactive)

    sys.exit()
