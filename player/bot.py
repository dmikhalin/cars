from random import randint, shuffle


def move(track: list[str], car_position: tuple[int, int], velocity: tuple[int, int]) -> tuple[int, int]:
    """
    Do your move! Accelerate, break or keep moving with the previous speed!
    :param track: Map of the track:
        "#" --- wall
        "." --- free cell
        "S" --- start position
        "F" --- finish
        "C" --- cars
    :param car_position: (row, col), rows --- from top to bottom, 0-indexed
    :param velocity: (v_row, v_col)
    :return: new velocity (new_v_row, new_v_col), such that
             abs(new_v_row - v_col) <= 1 and abs(new_v_row - v_col) <= 1
    """
    row, col = car_position
    v_row, v_col = velocity
    if 0 <= row + v_row < len(track) and 0 <= col + v_col < len(track[0]) and track[row + v_row][col + v_col] in ".FS":
        next_pos = bfs_next_pos(track, (row + v_row, col + v_col))
        return next_pos[0] - row, next_pos[1] - col
    else:
        return velocity

    # return randint(v_row - 1, v_row), randint(v_col - 1, v_col + 1)
    # return randint(v_row - 1, v_row + 1), randint(v_col - 1, v_col + 1)
    # return -1, 0


def next_points(track: list[str], pos: tuple[int, int]) -> list[tuple[int, int]]:
    ans = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            if (i != 0 or j != 0) and track[pos[0] + i][pos[1] + j] in ".F":
                ans.append((pos[0] + i, pos[1] + j))
    shuffle(ans)
    return ans


def bfs_next_pos(track: list[str], car_position: tuple[int, int]) -> tuple[int, int]:
    queue = [car_position]
    first = 0
    used = [[0] * len(track[0]) for i in range(len(track))]
    used[car_position[0]][car_position[1]] = 1
    dist = [[1000] * len(track[0]) for i in range(len(track))]
    dist[car_position[0]][car_position[1]] = 0
    prev = [[(-1, -1)] * len(track[0]) for i in range(len(track))]
    finish = -1, -1
    min_dist = 1000
    while first < len(queue):
        pos = queue[first]
        first += 1
        for nxt in next_points(track, pos):
            if not used[nxt[0]][nxt[1]]:
                used[nxt[0]][nxt[1]] = 1
                queue.append(nxt)
                dist[nxt[0]][nxt[1]] = dist[pos[0]][pos[1]] + 1
                prev[nxt[0]][nxt[1]] = pos
                if track[nxt[0]][nxt[1]] == "F" and dist[nxt[0]][nxt[1]] < min_dist:
                    min_dist = dist[nxt[0]][nxt[1]]
                    finish = nxt
    pos = finish
    path = []
    while pos != car_position:
        path.append(pos)
        pos = prev[pos[0]][pos[1]]
    return path[-1]


def main():
    pass


if __name__ == '__main__':
    main()
