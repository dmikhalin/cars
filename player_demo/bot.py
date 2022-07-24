from random import randint


def move(track, car_position, velocity):
    """
    Do your move! Accelerate, break or keep moving with the previous speed!
    :param track: Map of the track:
        "#" --- wall
        "." --- free cell
        "S" --- start position
        "F" --- finish
        "C" --- cars
    :param car_position: (x, y), y --- from top to bottom, 0-indexed
    :param velocity: (vx, vy)
    :return: new velocity (new_vx, new_vy), such that
             abs(new_vx - vx) <= 1 and abs(new_vy - vy) <= 1
    """
    x, y = car_position
    vx, vy = velocity

    return randint(vx - 1, vx + 1), randint(vy - 1, vy + 1)


def main():
    pass


if __name__ == '__main__':
    main()
