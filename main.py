import pygame
import pytmx

from math import atan2, pi
from random import randint, shuffle, random
from timelimit import time_limit, TimeoutException

from player_demo.bot import move as move0
from player_dm.bot import move as move1
from player_slow.bot import move as move2

PLAYERS = [{"name": "Speedy", "bot": move1, "img": 0, "level": 0.8},
           {"name": "Luigi", "bot": move1, "img": 1, "level": 0.6},
           {"name": "McQueen", "bot": move1, "img": 2, "level": 0.5},
           {"name": "Quido", "bot": move1, "img": 3, "level": 0.3},
           {"name": "Ramone", "bot": move2, "img": 4, "level": 0},
           {"name": "Lizzie", "bot": move0, "img": 5, "level": 0},
           ]
WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 1100, 800
FPS = 20
MAPS_DIR = "maps"
IMAGES_DIR = "images"
LEVELS = ["map1.tmx", "map2.tmx"]
EVENT_TYPE = 30
DELAY = 300
FRAMES_PER_TICK = FPS * DELAY // 1000
WINNERS_NUMBER = 4


class Labyrinth:

    def __init__(self, filename):
        self.track = pytmx.load_pygame(f"{MAPS_DIR}/{filename}")
        self.height = self.track.height
        self.width = self.track.width
        self.tile_size = min(WINDOW_HEIGHT // self.height, WINDOW_WIDTH // self.width)
        self.start_tiles = [78, 47]
        self.finish_tiles = [79, 449]
        self.free_tiles = [175] + self.start_tiles + self.finish_tiles
        self.start_angles = {78: 0, 47: -90}

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

    def get_start_positions(self) -> list[tuple[int, int]]:
        result = []
        for row in range(self.height):
            for col in range(self.width):
                if self.get_tile_id((row, col)) in self.start_tiles:
                    result.append((row, col))
        return result

    def is_in_map(self, position):
        return 0 <= position[0] < self.height and 0 <= position[1] < self.width

    def is_free(self, position):
        return self.get_tile_id(position) in self.free_tiles

    def is_finish(self, position):
        return self.get_tile_id(position) in self.finish_tiles


class Car:

    def __init__(self, pic, move_function, position, name, level, time=0):
        self.image = pic
        self.row, self.col = position
        self.real_y, self.real_x = position
        self.move = move_function
        self.vx = 0
        self.vy = 0
        self.real_vx = 0
        self.real_vy = 0
        self.name = name
        self.rotate_angle = 0
        self.lost_control = False
        self.finished = False
        self.paused = False
        self.level = level
        self.time = time
        self.result = 10 ** 6

    def get_position(self):
        return self.row, self.col

    def set_position(self, position):
        self.row, self.col = position

    def get_velocity(self):
        return self.vy, self.vx

    def set_velocity(self, velocity):
        self.vy, self.vx = velocity

    def get_real_position(self):
        return self.real_y, self.real_x

    def set_real_position(self, position):
        self.real_y, self.real_x = position

    def set_real_velocity(self, velocity):
        self.real_vy, self.real_vx = velocity

    def move_real(self):
        self.real_x += self.real_vx
        self.real_y += self.real_vy

    def rotate_random(self):
        self.rotate_angle = randint(0, 359)

    def render(self, screen, tile_size):
        if self.image.get_width() != tile_size:
            self.image = pygame.transform.smoothscale(self.image, (tile_size, tile_size * 1.6))
        if self.vx != 0 or self.vy != 0:
            self.rotate_angle = atan2(-self.real_vy, self.real_vx) * 180 / pi - 90
        rotated_image = pygame.transform.rotate(self.image, self.rotate_angle)
        delta_x = (rotated_image.get_width() - tile_size) // 2
        delta_y = (rotated_image.get_height() - tile_size) // 2
        screen.blit(rotated_image, (self.real_x * tile_size - delta_x, self.real_y * tile_size - delta_y))


class Boom:

    def __init__(self, position, cars, time):
        self.row, self.col = position
        self.cars = cars
        for car in cars:
            car.paused = True
        self.time = time
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
        if not self.activated:
            for car in self.cars:
                if free_tiles:
                    car.set_position(free_tiles.pop())
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
        for car in self.cars:
            car.rotate_angle = self.labyrinth.start_angles[self.labyrinth.get_tile_id(car.get_position())]
        self.time = 0
        self.results = []
        self.booms = set()

    def render(self, screen):
        self.labyrinth.render(screen)
        self.show_legend(screen)
        for car in self.cars:
            car.render(screen, self.labyrinth.tile_size)
        for boom in list(self.booms):
            if boom.time <= self.time:
                # boom.activate(self.free_neighbours(boom.get_position()))
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
                if tile_id in self.labyrinth.start_tiles:
                    symb = "S"
                elif tile_id in self.labyrinth.finish_tiles:
                    symb = "F"
                if (i, j) in cars_coords:
                    symb = "C"
                line.append(symb)
            track_map.append("".join(line))
        return track_map

    def move_cars_real(self):
        for car in self.cars:
            if car.time == self.time:
                car.move_real()
            else:
                car.set_real_position(car.get_position())
                if not car.finished:
                    car.rotate_random()

    def move_cars(self):
        self.time += 1
        track_map = self.symbol_map()
        cars_coords = {}
        for car in self.cars:
            if car.finished:
                continue
            if car.paused:
                if random() > car.level:
                    car.paused = False
                if car.get_position() not in cars_coords:
                    cars_coords[car.get_position()] = []
                cars_coords[car.get_position()].append(car)
                continue
            car.time = self.time
            vy, vx = car.get_velocity()
            if not car.lost_control:
                try:
                    with time_limit(1):
                        vy, vx = car.move(track_map[:], car.get_position(), car.get_velocity())
                except TimeoutException as e:
                    print("Timed out!")
                    car.lost_control = True

            if abs(vx - car.vx) > 1 or abs(vy - car.vy) > 1:
                vy, vx = car.get_velocity()
            next_row, next_col = car.row + vy, car.col + vx
            if abs(vx) > abs(vy):
                shift = 1 if vx > 0 else -1
                x = car.col
                while x != next_col + shift:
                    y = car.row + vy * (x - car.col) // vx
                    if self.labyrinth.is_finish((y, x)):
                        next_row, next_col = car.row + vy * (x - car.col) // vx, x
                        car.set_velocity((0, 0))
                        break
                    elif not self.labyrinth.is_in_map((y, x)) or \
                            not self.labyrinth.is_free((y, x)):
                        self.booms.add(Boom((y, x), [car], self.time + 1))
                        next_row, next_col = car.row + vy * (x - car.col) // vx, x
                        car.set_velocity((0, 0))
                        break
                    x += shift
                else:
                    car.set_velocity((vy, vx))
            elif vy:
                shift = 1 if vy > 0 else -1
                y = car.row
                while y != next_row + shift:
                    x = car.col + vx * (y - car.row) // vy
                    if self.labyrinth.is_finish((y, x)):
                        next_row, next_col = y, car.col + vx * (y - car.row) // vy
                        car.set_velocity((0, 0))
                    if not self.labyrinth.is_in_map((y, x)) or \
                            not self.labyrinth.is_free((y, x)):
                        self.booms.add(Boom((y, x), [car], self.time + 1))
                        next_row, next_col = y, car.col + vx * (y - car.row) // vy
                        car.set_velocity((0, 0))
                        break
                    y += shift
                else:
                    car.set_velocity((vy, vx))
            car.set_real_position(car.get_position())
            car.set_position((next_row, next_col))
            real_vy = (next_row - car.get_real_position()[0]) / FRAMES_PER_TICK
            real_vx = (next_col - car.get_real_position()[1]) / FRAMES_PER_TICK
            car.set_real_velocity((real_vy, real_vx))
            if self.labyrinth.get_tile_id((next_row, next_col)) not in self.labyrinth.finish_tiles:
                if (next_row, next_col) not in cars_coords:
                    cars_coords[(next_row, next_col)] = []
                cars_coords[(next_row, next_col)].append(car)
        for coords in cars_coords:
            if len(cars_coords[coords]) > 1:
                self.booms.add(Boom(coords, cars_coords[coords], self.time + 1))
                for car in cars_coords[coords]:
                    car.set_velocity((0, 0))
        for boom in self.booms:
            boom.activate(self.free_neighbours(boom.get_position()))

    def check_winners(self) -> list[str]:
        for car in self.cars:
            if car.finished:
                continue
            if self.labyrinth.get_tile_id(car.get_position()) in self.labyrinth.finish_tiles:
                car.finished = True
                car.result = self.time
                self.results.append((car.name, self.time))
        if len(self.results) < WINNERS_NUMBER or \
                max(self.cars, key=lambda car: car.result if car.finished else 0).result == self.time:
            return []
        return self.results

    def show_legend(self, screen):
        self.cars.sort(key=lambda x: x.result)
        for i in range(len(self.cars)):
            car = self.cars[i]
            if car.image.get_width() != self.labyrinth.tile_size:
                car.image = pygame.transform.smoothscale(car.image, (self.labyrinth.tile_size,
                                                                     self.labyrinth.tile_size * 1.6))
            screen.blit(car.image, (self.labyrinth.width * self.labyrinth.tile_size + 30,
                                    50 + i * 50))
            font = pygame.font.Font(None, 30)
            text = font.render(car.name, 1, (150, 200, 200))
            screen.blit(text, (self.labyrinth.width * self.labyrinth.tile_size + 60, 60 + i * 50))
            if car.finished:
                text = font.render(str(car.result), 1, (150, 200, 200))
                screen.blit(text, (self.labyrinth.width * self.labyrinth.tile_size + 250, 60 + i * 50))


def show_message(screen, message):
    font = pygame.font.Font(None, 30)
    text = font.render(message, 1, (150, 200, 200))
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

    start_positions = labyrinth.get_start_positions()
    shuffle(start_positions)
    cars = [Car(car_images[p["img"]], p["bot"], start_positions.pop(), p["name"], p["level"]) for p in PLAYERS]

    game = Game(labyrinth, cars)

    clock = pygame.time.Clock()
    pygame.time.set_timer(EVENT_TYPE, DELAY)
    running = True
    game_over = False
    while running:
        if not game_over:
            game.move_cars_real()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == EVENT_TYPE and not game_over:
                game.move_cars()
        screen.fill((0, 0, 0))
        game.render(screen)
        if winners := game.check_winners():
            game_over = True
            # show_message(screen, "Winners: " + ", ".join(f"{player[0]}: {player[1]}" for player in winners))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == '__main__':
    main()
