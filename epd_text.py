from PIL import ImageFont, ImageDraw, Image
import logging

from waveshare_epd import epd2in13_V4

#write text to e-ink display utilizing https://github.com/waveshareteam/e-Paper
#currently only for 2.13 inch display

#so weirdly, this is flipped
#but it has to be in THIS order for it to work in the image functions
#but to access height, we need to read 1, and width, 0
IMAGE_SIZE = (epd2in13_V4.EPD_HEIGHT, epd2in13_V4.EPD_WIDTH)
DISPLAY_DIMENSIONS = {'x': epd2in13_V4.EPD_HEIGHT, 'y': epd2in13_V4.EPD_WIDTH}
BACKGROUND_COLOR = 255
IMAGE_MODE = '1'
CENTER_Y = DISPLAY_DIMENSIONS['y'] // 2
CENTER_X = DISPLAY_DIMENSIONS['x'] // 2

logger = logging.getLogger(__name__)

def loadLinePositions(line_count, line_offset=0, margin_y=0):
    #calculate the positions of each line for text
    line_positions = []
    line_size = (DISPLAY_DIMENSIONS['y'] - (2 * margin_y)) // line_count

    position = margin_y
    line = 0
    while line < line_count:
        line_positions.append(position)
        position += line_size + line_offset
        line += 1

    return line_positions, line_size

def get_text_center_position(text, font=None):
    #returns the position to display text at for it to be centered
    image = Image.new(IMAGE_MODE, IMAGE_SIZE, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    _, _, w, h = draw.textbbox((0, 0), text, font=font)
    center = (CENTER_X - (w // 2), CENTER_Y - (h // 2))

    return center

def get_horizontal_text_center_position(text, font=None):
    return get_text_center_position(text, font)[0]

def get_vertical_text_center_position(text, font=None):
    return get_text_center_position(text, font)[1]

def get_text_right_justify_position(text, margin=0, font=None):
    #returns the position to display text at for it to be against the right side
    image = Image.new(IMAGE_MODE, IMAGE_SIZE, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    _, _, w, _ = draw.textbbox((0, 0), text, font=font)
    position = DISPLAY_DIMENSIONS['x'] - margin - w

    return position

class epd_text:
    def __init__(self, line_count, line_offset=0, margin_x=0, margin_y=0, font_file=None, font_size=None):
        self.line_positions, self.line_size = loadLinePositions(line_count)
        self.line_count = len(self.line_positions)

        if self.line_count % 2 == 0:
            self.middle_line = self.line_count // 2
        else:
            self.middle_line = (self.line_count // 2) + 1

        self.line_offset = line_offset
        self.margin_x = margin_x
        self.margin_y = margin_y

        logging.debug(f'IMAGE SIZE: {IMAGE_SIZE}')
        logging.debug(f'CENTER Y: {CENTER_Y}')
        logging.debug(f'CENTER X: {CENTER_X}')
        logging.debug(f'LINE COUNT: {self.line_count}')
        logging.debug(f'MIDDLE LINE: {self.middle_line}')
        logging.debug(f'LINE OFFSET: {self.line_offset}')
        logging.debug(f'MARGIN X: {self.margin_x}')
        logging.debug(f'MARGIN Y: {self.margin_y}')
        logging.debug(f'LINE SIZE: {self.line_size}')
        logging.debug(f'LINE_POSITIONS: {self.line_positions}')

        self.font = None
        if font_file:
            self.load_font(font_file, font_size)

        #initialize epd
        logging.info('Initializing E-Ink Display...')
        self.epd = epd2in13_V4.EPD()
        
        #self.epd.init()
        self.epd.init_fast()
        #self.clear()
        
        #draw initial image
        self.new_image()
        self.write_text('***E INK DISPLAY IS INITIALIZED***', center=True)
        self.update()

    def load_font(self, font_file, font_size):
        logging.info(f"FONT FILE: {font_file}")
        logging.info(f'FONT SIZE: {font_size}')
        self.font = ImageFont.truetype(font_file, font_size)

    def new_image(self):
        self.image = Image.new(IMAGE_MODE, IMAGE_SIZE, BACKGROUND_COLOR)
        self.image_draw = ImageDraw.Draw(self.image)

    def set_line_text(self, line, text, position=0, center=False, right_justify=False):
        if line >= self.line_count:
            logging.warning(f'Line [{line}] is above line count {self.line_count}.')
            return
        elif line < 0:
            logging.warning(f'Line [{line}] is invalid.')
            return
        
        position += self.margin_x

        if right_justify:
            position = get_text_right_justify_position(text, self.margin_x, font=self.font)

        if center:
            position = get_horizontal_text_center_position(text, font=self.font)

        logging.debug(f'Writing text [{text}] at position [{position}] to line [{line}]...')
        self.image_draw.text((position, self.line_positions[line]), text, font=self.font)

    def write_text(self, text, position=(0,0), center=False):
        #write text to screen directly
        position = (position[0] + self.margin_x, position[1])
        if center:
            position = get_text_center_position(text, self.font)
        
        logging.debug(f'Writing text [{text}] at position [{position}]...')
        self.image_draw.text(position, text, font=self.font)

    def clear(self):
        logging.debug('Clearing E-Ink Display...')
        self.epd.Clear()

    def update(self, partial=False, base=False):
        logging.debug('Updating E-Ink Display...')

        if partial:
            self.epd.displayPartial(self.epd.getbuffer(self.image))
        else:
            if base:
                self.epd.displayPartBaseImage(self.epd.getbuffer(self.image))
            else:
                self.epd.display_fast(self.epd.getbuffer(self.image))
                self.epd.display(self.epd.getbuffer(self.image))
            
    def show_line_test_page(self):
        self.new_image()

        for i in range(self.line_count):
            self.set_line_text(i, f'LINE {i} - OFFSET {self.line_positions[i]}')
        
        self.update()