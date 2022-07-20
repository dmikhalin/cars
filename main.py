import pygame
import pytmx
from math import atan2, pi
from random import randint

from timelimit import time_limit, TimeoutException
from player_dm.bot import move as move0
from player_demo.bot import move as move1

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 800, 800
FPS = 20
MAPS_DIR = "maps"
IMAGES_DIR = "images"
LEVELS = ["map1.tmx"]
TILE_SIZE = 32
EVENT_TYPE = 30
DELAY = 200


class Labyrinth:

    def __init__(self, filename):
        self.track = pytmx.load_pygame(f"{MAPS_DIR}/{filename}")
        self.height = self.track.height
        self.width = self.track.width
        self.tile_size = min(WINDOW_HEIGHT // self.height, WINDOW_WIDTH // self.width)
        self.start_tile = 78
        self.finish_tile = 79
        self.free_tiles = [175, 78, 79]

    # Deprecated
    def get_tile_image(self, row, col):
        color = "black"
        if self.track[row][col] == ".":
            color = "white"
        elif self.track[row][col] == "#":
            color = "blue"
        surf = pygame.Surface((self.tile_size, self.tile_size))
        pygame.draw.rect(surf, color, (0, 0, self.tile_size, self.tile_size))
        return surf

    def render(self, screen):
        for row in range(self.height):
            for col in range(self.width):
                tile_image = self.track.get_tile_image(col, row, 0)
                if tile_image:
                    image = pygame.transform.smoothscale(tile_image, (self.tile_size, self.tile_size))
                    screen.blit(image, (col * self.tile_size, row * self.tile_size))

    def get_tile_id(self, position):
        gid = self.track.get_tile_gid(position[1], position[0], 0)
        if gid == 0:
            return 0
        return self.track.tiledgidmap[gid]

    def is_in_map(self, position):
        return 0 <= position[0] < self.height and 0 <= position[1] < self.width

    def is_free(self, position):
        return self.get_tile_id(position) in self.free_tiles

    def is_finish(self, position):
        return self.get_tile_id(position) == self.finish_tile


class Car:

    def __init__(self, pic, move_function, position, name):
        self.image = pic
        self.row, self.col = position
        self.move = move_function
        self.vx = 0
        self.vy = 0
        self.name = name
        self.rotate_angle = 0
        self.lost_control = False
        self.finished = False
        self.paused = False

    def get_position(self):
        return self.row, self.col

    def set_position(self, position):
        self.row, self.col = position

    def render(self, screen, tile_size):
        if self.image.get_width() != tile_size:
            self.image = pygame.transform.smoothscale(self.image, (tile_size, tile_size * 2))
        if self.vx != 0 or self.vy != 0:
            self.rotate_angle = atan2(-self.vy, self.vx) * 180 / pi - 90
        rotated_image = pygame.transform.rotate(self.image, self.rotate_angle)
        delta_x = (rotated_image.get_width() - tile_size) // 2
        delta_y = (rotated_image.get_height() - tile_size) // 2
        screen.blit(rotated_image, (self.col * tile_size - delta_x, self.row * tile_size - delta_y))
        # screen.blit(self.image, (5 * tile_size - delta_x, 29 * tile_size - delta_y))


class Boom:

    def __init__(self, position, cars):
        self.row, self.col = position
        self.cars = cars
        for car in cars:
            car.paused = True
        self.time = -1
        self.images = [pygame.Surface((240, 240)).convert_alpha() for i in range(48)]
        all_images = pygame.image.load(f"{IMAGES_DIR}/explosions-sprite.png").convert_alpha()
        for k in range(48):
            i = k // 8
            j = k % 8
            self.images[k].blit(all_images, (0, 0), (j * 256 + 8, i * 256 + 8, 240, 240))
        self.img_ind = 0
        self.activated = False
        self.ended = False

    def get_position(self):
        return self.row, self.col

    def activate(self, free_tiles: set[tuple[int, int]]):
        if self.img_ind > 10 and not self.activated:
            for car in self.cars:
                if free_tiles:
                    car.set_position(free_tiles.pop())
                car.paused = False
                car.rotate_angle = randint(0, 359)
            self.activated = True

    def render(self, screen, tile_size):
        if not self.ended:
            image = self.images[self.img_ind]
            if image.get_width() > 2 * tile_size:
                image = pygame.transform.smoothscale(image, (2 * tile_size, 2 * tile_size))
            delta_x = (image.get_width() - tile_size) // 2
            delta_y = (image.get_height() - tile_size) // 2
            screen.blit(image, (self.col * tile_size - delta_x, self.row * tile_size - delta_y))
        self.img_ind += 4
        if self.img_ind >= len(self.images):
            self.ended = True


class Game:

    def __init__(self, labyrinth, cars):
        self.labyrinth = labyrinth
        self.cars = cars
        self.time = 0
        self.results = []
        self.booms = set()

    def render(self, screen):
        self.labyrinth.render(screen)
        for car in self.cars:
            car.render(screen, self.labyrinth.tile_size)
        for boom in list(self.booms):
            boom.activate(self.free_neighbours(boom.get_position()))
            boom.render(screen, self.labyrinth.tile_size)
            if boom.ended:
                self.booms.discard(boom)

    def free_neighbours(self, position):
        row, col = position
        cars_coords = {car.get_position() for car in self.cars}
        return {(row + dy, col + dx) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                if self.labyrinth.is_in_map((row + dy, col + dx)) and
                self.labyrinth.is_free((row + dy, col + dx)) and
                ((row + dy, col + dx) not in cars_coords)}


    def symbol_map(self) -> list[str]:
        track_map = []
        cars_coords = {car.get_position() for car in self.cars}
        for i in range(self.labyrinth.track.height):
            line = []
            for j in range(self.labyrinth.track.width):
                tile_id = self.labyrinth.get_tile_id((i, j))
                symb = "#"
                if tile_id in self.labyrinth.free_tiles:
                    symb = "."
                if tile_id == self.labyrinth.start_tile:
                    symb = "S"
                elif tile_id == self.labyrinth.finish_tile:
                    symb = "F"
                if (i, j) in cars_coords:
                    symb = "C"
                line.append(symb)
            track_map.append("".join(line))
        return track_map

    def move_cars(self):
        self.time += 1
        track_map = self.symbol_map()
        cars_coords = {}
        for car in self.cars:
            if car.finished:
                continue
            if car.paused:
                if car.get_position() not in cars_coords:
                    cars_coords[car.get_position()] = []
                cars_coords[car.get_position()].append(car)
                continue
            vx = car.vx
            vy = car.vy
            if not car.lost_control:
                try:
                    with time_limit(1):
                        vy, vx = car.move(track_map[:], (car.row, car.col), (car.vy, car.vx))
                except TimeoutException as e:
                    print("Timed out!")
                    car.lost_control = True

            if abs(vx - car.vx) > 1 or abs(vy - car.vy) > 1:
                vx = car.vx
                vy = car.vy
            next_row, next_col = car.row + vy, car.col + vx
            if abs(vx) > abs(vy):
                shift = 1 if vx > 0 else -1
                x = car.col
                while x != next_col + shift:
                    y = car.row + vy * (x - car.col) // vx
                    if self.labyrinth.is_finish((y, x)):
                        next_row, next_col = car.row + vy * (x - car.col) // vx, x
                        car.vx = 0
                        car.vy = 0
                        break
                    elif not self.labyrinth.is_in_map((y, x)) or \
                            not self.labyrinth.is_free((y, x)):
                        self.booms.add(Boom((y, x), [car]))
                        next_row, next_col = car.row + vy * (x - car.col) // vx, x
                        car.vx = 0
                        car.vy = 0
                        break
                    x += shift
                else:
                    car.vx = vx
                    car.vy = vy
            elif vy:
                shift = 1 if vy > 0 else -1
                y = car.row
                while y != next_row + shift:
                    x = car.col + vx * (y - car.row) // vy
                    if self.labyrinth.is_finish((y, x)):
                        next_row, next_col = y, car.col + vx * (y - car.row) // vy
                        car.vx = 0
                        car.vy = 0
                    if not self.labyrinth.is_in_map((y, x)) or \
                            not self.labyrinth.is_free((y, x)):
                        self.booms.add(Boom((y, x), [car]))
                        next_row, next_col = y, car.col + vx * (y - car.row) // vy
                        car.vx = 0
                        car.vy = 0
                        break
                    y += shift
                else:
                    car.vx = vx
                    car.vy = vy
            car.set_position((next_row, next_col))
            if self.labyrinth.get_tile_id((next_row, next_col)) != self.labyrinth.finish_tile:
                if (next_row, next_col) not in cars_coords:
                    cars_coords[(next_row, next_col)] = []
                cars_coords[(next_row, next_col)].append(car)
        for coords in cars_coords:
            if len(cars_coords[coords]) > 1:
                self.booms.add(Boom(coords, cars_coords[coords]))
                for car in cars_coords[coords]:
                    car.vx = 0
                    car.vy = 0

    def check_winners(self) -> list[str]:
        for car in self.cars:
            if car.finished:
                continue
            if self.labyrinth.get_tile_id(car.get_position()) == self.labyrinth.finish_tile:
                car.finished = True
                self.results.append((car.name, self.time))
        if len(self.results) < 3:
            return []
        return self.results



def show_message(screen, message):
    font = pygame.font.Font(None, 30)
    text = font.render(message, 1, (150, 255, 255))
    text_x = WINDOW_WIDTH // 2 - text.get_width() // 2
    text_y = WINDOW_HEIGHT // 2 - text.get_height() // 2
    text_w = text.get_width()
    text_h = text.get_height()
    pygame.draw.rect(screen, (50, 50, 50), (text_x - 10, text_y - 10,
                                              text_w + 20, text_h + 20))
    screen.blit(text, (text_x, text_y))


def load_car_images() -> list:
    car_surfaces = [pygame.Surface((60, 100)).convert_alpha() for i in range(6)]
    all_cars = pygame.image.load(f"{IMAGES_DIR}/cars1.png").convert_alpha()
    car_surfaces[0].blit(all_cars, (0, 0), (65, 115, 60, 100))
    car_surfaces[1].blit(all_cars, (0, 0), (125, 15, 60, 100))
    car_surfaces[2].blit(all_cars, (0, 0), (185, 15, 60, 100))
    car_surfaces[3].blit(all_cars, (0, 0), (245, 115, 60, 100))
    car_surfaces[4].blit(all_cars, (0, 0), (370, 15, 60, 100))
    car_surfaces[5].blit(all_cars, (0, 0), (65, 15, 60, 100))
    return car_surfaces


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)

    labyrinth = Labyrinth(LEVELS[0])
    car_images = load_car_images()
    cars = [Car(car_images[0], move0, (28, 2), "Speedy"),
            Car(car_images[1], move0, (28, 3), "Luigi"),
            Car(car_images[2], move0, (28, 4), "McQueen"),
            Car(car_images[3], move0, (28, 5), "Quido"),
            Car(car_images[4], move1, (28, 6), "Ramone"),
            Car(car_images[5], move1, (28, 7), "Lizzie")]
    game = Game(labyrinth, cars)

    clock = pygame.time.Clock()
    pygame.time.set_timer(EVENT_TYPE, DELAY)
    running = True
    game_over = False
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == EVENT_TYPE and not game_over:
                game.move_cars()
        screen.fill((0, 0, 0))
        game.render(screen)
        if winners := game.check_winners():
            game_over = True
            show_message(screen, "Winners: " + ", ".join(f"{player[0]}: {player[1]}" for player in winners))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == '__main__':
    main()
