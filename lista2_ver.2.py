import time
import sys
import copy

# Definicje graczy
PLAYER_1 = 'B'
PLAYER_2 = 'W'
EMPTY = '_'

# Kierunki ruchu (N, S, E, W)
DIRECTIONS = [(-1, 0), (1, 0), (0, 1), (0, -1)]


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
        new_board = copy.deepcopy(self.board)
        new_board[r2][c2] = self.current_player
        new_board[r1][c1] = EMPTY
        return GameState(new_board, self.get_opponent())

    def is_terminal(self):
        return len(self.get_possible_moves()) == 0

    def __str__(self):
        return '\n'.join(' '.join(row) for row in self.board)


def print_board(board):
    sys.stdout.write("\033[H\033[J")  # Czyszczenie ekranu (jeśli działa)
    for row in board:
        print(" ".join(row))
    sys.stdout.flush()  # Wymusza natychmiastowe wyświetlenie


def invert_position_color(board, start_pos, end_pos):
    """
    Inwersja kolorów pozycji. Zmienia tło i tekst na odwrotne w miejscu startowym i końcowym.
    """
    r1, c1 = start_pos
    r2, c2 = end_pos

    temp_board = copy.deepcopy(board)

    # Inwersja kolorów tła i tekstu
    def invert_cell(cell):
        if cell == 'W':
            return '[W]'  # Zmieniamy kolor W na białe tło z czarnym napisem
        elif cell == 'B':
            return '[B]'  # Zmieniamy kolor B na czarne tło z białym napisem
        return '[ ]'  # Puste miejsce

    # Zmieniamy kolory w miejscach startowym i końcowym
    temp_board[r1][c1] = invert_cell(' ')  # Puste miejsce na startowej pozycji
    temp_board[r2][c2] = invert_cell('B' if board[r2][c2] == 'B' else 'W')  # Inwersja koloru pionka

    # Wyświetlamy planszę
    print_board(temp_board)


def animate_move(board, start_pos, end_pos, current_player):
    """
    Animacja polegająca na inwersji kolorów w miejscach startowym i końcowym.
    """
    r1, c1 = start_pos
    r2, c2 = end_pos

    steps = 10  # liczba kroków animacji
    for step in range(steps):
        # Obliczanie "pozycji" pionka na podstawie proporcji
        intermediate_r = int(r1 + (r2 - r1) * (step / steps))
        intermediate_c = int(c1 + (c2 - c1) * (step / steps))

        temp_board = copy.deepcopy(board)

        # Inwersja kolorów: Zmieniamy tło i tekst na odpowiednich pozycjach
        if step > 0:  # Po pierwszym kroku usuwamy pionka z poprzedniej pozycji
            temp_board[r1][c1] = ' '  # Puste miejsce

        temp_board[intermediate_r][intermediate_c] = current_player  # Umieszczamy pionka w nowej pozycji

        # Wyświetlamy planszę
        print_board(temp_board)
        time.sleep(0.05)  # Czas pomiędzy klatkami animacji (można dostosować)

    # Ostateczna zmiana na końcową pozycję
    final_board = copy.deepcopy(board)
    final_board[r1][c1] = ' '  # Usuwamy pionka z oryginalnej pozycji
    final_board[r2][c2] = current_player  # Wstawiamy pionka na końcową pozycję

    print_board(final_board)  # Wyświetlamy finalną planszę
    return final_board


def play_game(board, heuristic, depth, interactive=False):
    state = GameState(board, PLAYER_1)
    rounds = 0
    total_nodes = 0
    start_time = time.time()

    while not state.is_terminal():
        node_counter = [0]
        print(f'Runda ----------------------- {rounds}')
        print(state)
        _, move = minimax(state, depth, float('-inf'), float('inf'), True, state.current_player, heuristic,
                          node_counter)
        if move is None:
            break
        start_pos, end_pos = move
        # Animowanie ruchu z inwersją miejsc
        print(f"\nRuch: {state.current_player} z {start_pos} na {end_pos}")
        state.board = animate_move(state.board, start_pos, end_pos, state.current_player)

        state = state.apply_move(move)
        rounds += 1
        total_nodes += node_counter[0]

        # Wizualizacja inwersji ruchu:
        time.sleep(1)  # Opcjonalnie czekamy 1 sekundę, by ruch był widoczny

    end_time = time.time()
    print(state)
    print(f"Rundy: {rounds}, Wygrywa: {state.get_opponent()}")
    print(f"Węzły: {total_nodes}", file=sys.stderr)
    print(f"Czas: {end_time - start_time:.2f}s", file=sys.stderr)


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


def read_board(file_path):
    with open(file_path, 'r') as file:
        board = [line.strip().split() for line in file.readlines()]
    return board


def wait_for_space():
    print("\nNaciśnij SPACJĘ, aby kontynuować...")
    while True:
        char = msvcrt.getch()
        print(f"Zareagowano na: {char}")  # Debug: pokazuje, co zostało wciśnięte
        if char == b' ':
            break



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
    #TEST
    # python lista2_ver.2.py --board plansza2.txt -H 2 -d 4 --interactive
    # play_game(board, args.heurystyka, args.d)
    # play_game(board, 4, 2, True)
    play_game(board, 2, 4, True)

