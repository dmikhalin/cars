from random import randint


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

    return randint(v_row - 1, v_row + 1), randint(v_col - 1, v_col + 1)


def main():
    pass


if __name__ == '__main__':
    main()
