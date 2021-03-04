# import and initialize some stuff
import pygame
import random
import os
import itertools

# import numpy as np
from PIL import Image

# TODO: better graphics
# TODO: pieces don't instantly place themselves 
# TODO: physics I think are correct at the moment but research/testing would be good
# TODO: add holding
# TODO: add hard drop
# TODO: add rotating both directions
# TODO: when lines are removed there is a graphic

pygame.init()

# set some global constants
BACKGROUND = pygame.image.load(os.path.join('img', 'Background.png'))
TILE_SIZE = 32
SIZE = WIDTH, HEIGHT = 640, 640
PIECE_BOUNDS = PIECE_BOUND_LEFT, PIECE_BOUND_RIGHT = 160, 480
BLACK = 0, 0, 0
GREEN = 0, 100, 0
FPS = 60


#
# -------------- CLASSES ------------------------------------------------------------
#


class Piece:
    def __init__(self):
        self.start = self.x, self.y = WIDTH / 2 // TILE_SIZE * TILE_SIZE - TILE_SIZE, 0
        self.time_between_drops = 1000  # in milliseconds
        self.time_since_move = 0
        # random.randint(1, 7)
        self.image_file = os.path.join('img', 'piece' + str(random.randint(1, 7)) + '.png')
        self.image = pygame.image.load(self.image_file)
        self.mask = pygame.mask.from_surface(self.image)
        self.width, self.height = self.mask.get_size()
        self.time_since_down = 0
        self.time_since_side = 0
        self.set_pieces = []

    def update_dimensions(self):
        self.mask = pygame.mask.from_surface(self.image)
        self.width, self.height = self.mask.get_size()

    def handle_keys_down(self, keys_down):
        # left and right should be have 300 ms delay then 100 ms intervals not yet though
        if keys_down[pygame.K_LEFT] and not self.check_side('left'):
            if self.time_since_side > 110:
                # make sure we stay in bounds
                if self.x + self.get_mask_rect()[0] - TILE_SIZE >= PIECE_BOUND_LEFT:
                    self.x -= TILE_SIZE
                    self.time_since_side = 0
        if keys_down[pygame.K_RIGHT] and not self.check_side('right'):
            if self.time_since_side > 110:
                # make sure we stay in bounds
                if self.x + self.get_mask_rect()[2] + TILE_SIZE <= PIECE_BOUND_RIGHT:
                    self.x += TILE_SIZE
                    self.time_since_side = 0
        # down we want to repeat it quickly and instantly but not too fast
        if keys_down[pygame.K_DOWN]:
            if self.time_since_down > 50:
                # make sure we don't move through a block
                if not self.handle_collisions():
                    self.time_since_down = 0
                    self.y += TILE_SIZE

    def handle_key_press(self, key):
        key = pygame.key.name(key)
        if key == "up":
            self.image = pygame.transform.rotate(self.image, 90)
            self.mask = pygame.mask.from_surface(self.image)
            # if a rotation puts the piece out of bounds move piece over
            if self.piece_within():
                # it is in another piece so rotate back
                self.image = pygame.transform.rotate(self.image, -90)
                self.mask = pygame.mask.from_surface(self.image)
            elif self.x + self.mask.get_rect()[2] > PIECE_BOUND_RIGHT:
                self.x -= (self.mask.get_rect()[2] + self.x) - PIECE_BOUND_RIGHT
                # here the logic is we get the amount of space between the border
                # and the right side of the shape (using difference via subtraction)
                # and move it to the left (-) by that amount
            elif self.x + self.mask.get_rect()[0] < PIECE_BOUND_LEFT:
                # same here but its plus (to go right) and since the border is
                # on the right of the shape instead of left we have to swap the two values positions
                self.x += PIECE_BOUND_LEFT - (self.mask.get_rect()[0] + self.x)

    def piece_within(self):
        for set_piece in self.set_pieces:
            for rect in self.get_shape_rects():
                for set_rect in set_piece.get_shape_rects():
                    # it is in the other piece
                    if abs(rect.centerx - set_rect.centerx) <= 5 and abs(set_rect.centery - rect.centery) <= 5:
                        return True
        return False

    def handle_collisions(self):
        for set_piece in self.set_pieces:
            for rect in self.get_shape_rects():
                for set_rect in set_piece.get_shape_rects():
                    # it is directly above the other piece
                    if rect.centerx - set_rect.centerx == 0 and -5 < set_rect.centery - rect.centery < 35:
                        return True
        return False

    def check_side(self, side):
        for set_piece in self.set_pieces:
            for rect in self.get_shape_rects():
                for set_rect in set_piece.get_shape_rects():
                    # check if piece left or right
                    distance = rect.centerx - set_rect.centerx
                    same_line = rect.centery - set_rect.centery == 0
                    if (-5 < distance < 35 and side == 'left' or 5 > distance > -35 and side == 'right') and same_line:
                        return True
        return False

    def handle_movement(self):
        if self.time_since_move > self.time_between_drops:
            self.y += TILE_SIZE
            self.time_since_move = 0
            # in case we go below the ground
            if self.y + self.get_mask_rect()[3] >= HEIGHT:
                self.y = HEIGHT - self.get_mask_rect()[1]

    def get_rect(self):
        return self.x, self.y, self.width, self.height

    def increase_time(self, time):
        self.time_since_down += time
        self.time_since_side += time
        self.time_since_move += time

    def get_mask_rect(self):  # unlike a pygame rect this is left top (x1, y1), bottom right (x2, y2)
        xs = []  # and in relation to its own rectangles position
        ys = []
        for i in range(1, self.width // TILE_SIZE + 1):
            for j in range(1, self.height // TILE_SIZE + 1):
                x, y = i * TILE_SIZE - TILE_SIZE // 2, j * TILE_SIZE - TILE_SIZE // 2
                if self.mask.get_at((x, y)):
                    xs.extend((x - TILE_SIZE / 2, x + TILE_SIZE / 2))
                    ys.extend((y - TILE_SIZE / 2, y + TILE_SIZE / 2))
        if len(xs) > 0:
            return min(xs), min(ys), max(xs), max(ys)  # returns x1, y1, x2, y2
        else:
            return self.width, self.height, self.width, self.height

    def get_shape_rects(self):  # this will return all rectangles in the shape
        rects = []
        for i in range(1, self.width // TILE_SIZE + 1):
            for j in range(1, self.height // TILE_SIZE + 1):
                x, y = i * TILE_SIZE - TILE_SIZE // 2, j * TILE_SIZE - TILE_SIZE // 2
                if self.mask.get_at((x, y)):
                    # added a one pixel buffer because to the rect because it hasn't collided
                    # until the shape is in the other shape
                    rect = (self.x + x - (TILE_SIZE // 2), self.y + y - (TILE_SIZE // 2),
                            TILE_SIZE, TILE_SIZE)
                    rects.append(pygame.Rect(rect))
        return rects

    def move_down(self, rows):
        # for every row below move down tile_size
        for row in rows:
            if row > self.y + self.get_mask_rect()[1]:
                self.y += TILE_SIZE

    def remove_rows(self, rows):
        high = min(rows) - TILE_SIZE // 2
        if high < self.y + self.get_mask_rect()[1]:  # its too high so lower it
            high = self.y + self.get_mask_rect()[1]
        if high > self.y + self.height:  # the high is under the piece
            self.move_down(rows)
            return
        low = max(rows) + TILE_SIZE // 2
        if low < self.y:  # the low is above the piece
            return
        elif low > self.y + self.get_mask_rect()[3]:  # its too low so bring it up
            low = self.y + self.get_mask_rect()[3]
        # first get the pygame image as pillow image stored in the variable im
        pil_string_image = pygame.image.tostring(self.image, "RGBA", False)
        im = Image.frombytes("RGBA", (self.width, self.height), pil_string_image)
        # now define upper and lower regions to crop
        upper = (0, 0, self.width, high - self.y)
        lower = (0, low - self.y, self.width, self.height)
        # get those new regions as new images
        top = im.crop(upper)
        bottom = im.crop(lower)
        # now concatenate or combine them
        new_im = self.get_concat(top, bottom)
        # now convert back to pygame image and update the pieces image
        if new_im is not None and new_im.height != self.height:  # two images were cropped together
            size, mode = new_im.size, new_im.mode
            pygame_string_image = new_im.tobytes()
            self.image = pygame.image.fromstring(pygame_string_image, size, mode)
            self.update_dimensions()
            self.move_down(rows)
        elif new_im is None:
            self.image = None
        elif new_im.height == self.height:  # the image was unaffected by removed rows
            self.move_down(rows)

    def get_concat(self, im1, im2):  # this merges images on top of each other
        if im1.height > 10 and im2.height > 10:
            dst = Image.new('RGBA', (im1.width, im1.height + im2.height))
            dst.paste(im1, (0, 0))
            dst.paste(im2, (0, im1.height))
            return dst
        else:
            if im1.height < 10 < im2.height:
                # only im2 is part of the image aka there is no change
                return im2
            elif im2.height < 10 < im1.height:
                # only im1 is part of the image aka there is no change
                return im1
            else:
                # im1 and im2 are both none crops
                return None


#
# --------- FUNCTIONS -------------------------------------------------------
#


def remove_rows(pieces):
    ys = []
    for set_piece in pieces:
        for rect in set_piece.get_shape_rects():
            ys.append(rect.centery)
    # all y positions (rows) with ten squares
    ys.sort()
    groups = [list(j) for i, j in itertools.groupby(ys)]
    rows = [group[0] for group in groups if len(group) >= 10]
    if len(rows) > 0:  # if there are rows to be removed
        for set_piece in pieces:
            set_piece.remove_rows(rows)
    return


def create_new_piece(old_piece, pieces):
    pieces.append(old_piece)
    _new_piece = Piece()
    remove_rows(pieces)
    blits = [(set_piece.image, set_piece.get_rect()) for set_piece in pieces if
             set_piece.image is not None and pygame.mask.Mask.count(set_piece.mask) > 0]
    pieces = [set_piece for set_piece in pieces if
              set_piece.image is not None and pygame.mask.Mask.count(set_piece.mask) > 0]
    _new_piece.set_pieces = pieces
    return _new_piece, blits, pieces


def update_set_pieces(pieces):
    updated_pieces = [set_piece for set_piece in pieces if
                      set_piece.image is not None and pygame.mask.Mask.count(set_piece.mask) > 0]
    return updated_pieces


#
# -------------- MAIN LOOP ------------------------------------------------------
#


if __name__ == '__main__':  # running the game
    # setting some values that will be useful

    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption('TETRIS')

    # creating the first piece
    piece = Piece()
    set_piece_blits = []
    set_pieces = []

    # game loop
    run = True
    clock = pygame.time.Clock()
    while run:
        # regulate game speed and calculate some elapsed time for inputs
        clock.tick(FPS)
        piece.increase_time(clock.get_time())

        # check events
        for event in pygame.event.get():

            # close window
            if event.type == pygame.QUIT:
                run = False

            # for single key presses
            elif event.type == pygame.KEYDOWN:
                piece.handle_key_press(event.key)

        # check if key was pressed
        pressed = pygame.key.get_pressed()
        piece.handle_keys_down(pressed)

        # check for collisions
        coords = x1, y1, x2, y2 = piece.get_mask_rect()
        if piece.y + y2 >= HEIGHT:
            piece.y = HEIGHT - y2
            # create a new piece because it touched the bottom
            piece, set_piece_blits, set_pieces = create_new_piece(piece, set_pieces)
        else:
            # see if it has collided with other pieces from bottom
            if piece.handle_collisions():
                # if so set it down and create a new piece
                if piece.y == 0:
                    set_piece_blits = []
                    set_pieces = []
                    piece = Piece()
                else:
                    piece, set_piece_blits, set_pieces = create_new_piece(piece, set_pieces)

        # move piece
        piece.handle_movement()

        # update screen
        set_pieces = update_set_pieces(set_pieces)
        screen.blit(BACKGROUND, (0, 0))
        screen.blit(piece.image, piece.get_rect())
        screen.blits(set_piece_blits)
        pygame.display.update()

    pygame.quit()
