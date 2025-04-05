import sys
import time
import copy
import random
import msvcrt  # Windows


# import sys, tty, termios  # Linux/Mac, jeśli potrzeba

def wait_for_space():
    print("\nNaciśnij SPACJĘ, aby kontynuować...")
    while True:
        char = msvcrt.getch()
        print(f"Zareagowano na: {char}")  # Debug: pokazuje, co zostało wciśnięte
        if char == b' ':
            break


# Definicje graczy
PLAYER_1 = 'B'
PLAYER_2 = 'W'
EMPTY = '_'

# Kierunki ruchu (N, S, E, W)
DIRECTIONS = [(-1, 0), (1, 0), (0, 1), (0, -1)]

# Parametry domyślne
DEFAULT_DEPTH = 3

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
                            if self.board[nr][nc] == self.get_opponent():
                                moves.append(((r, c), (nr, nc)))
        return moves

    def apply_move(self, move):
        (r1, c1), (r2, c2) = move
        self.board[r2][c2] = self.current_player
        self.board[r1][c1] = EMPTY
        return GameState(self.board, self.get_opponent())

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

# Główna funkcja rozgrywki

def play_game(board, heuristic, depth, interactive=False):
    state = GameState(board, PLAYER_1)
    rounds = 0
    total_nodes = 0
    start_time = time.time()

    while not state.is_terminal():
        node_counter = [0]
        print(f'Runda ----------------------- {rounds}')
        print(state)
        _, move = minimax(state, depth, float('-inf'), float('inf'), True, state.current_player, heuristic, node_counter)
        if move is None:
            break
        state = state.apply_move(move)
        rounds += 1
        total_nodes += node_counter[0]

        # if interactive:
        #     wait_for_space()  # Czekaj na spację, jeśli tryb interaktywny

    end_time = time.time()
    print(state)
    print(f"Rundy: {rounds}, Wygrywa: {state.get_opponent()}")
    print(f"Węzły: {total_nodes}", file=sys.stderr)
    print(f"Czas: {end_time - start_time:.2f}s", file=sys.stderr)

def read_board(file_path):
    with open(file_path, 'r') as file:
        board = [line.strip().split() for line in file.readlines()]
    return board


def print_board(board):
    for row in board:
        print(" ".join(row))


# Przykład użycia (np. z pliku):
# python clobber.py < board.txt
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--heurystyka', type=int, help='Wybór heurystyki')
    parser.add_argument('-d', type=int, help='Maksymalna głębokość drzewa')
    parser.add_argument('--board', type=str, help='Ścieżka do pliku z planszą')
    parser.add_argument('--interactive', action='store_true', help='Tryb krok po kroku (SPACJA)')

    args = parser.parse_args()

    with open('plansza.txt', 'r') as f:
        board = [line.strip().split() for line in f.readlines()]

    # play_game(board, args.heurystyka, args.d)
    # play_game(board, 4, 2, True)
    play_game(board, 2, 4, True)

