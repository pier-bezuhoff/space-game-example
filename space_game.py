#!/usr/bin/env python3

from random import randint
from time import time
from sys import exit
from math import sin, cos, tan, pi
import pygame # you should 'pip' pygame ('$ pip3 install pygame')
from pygame.locals import *
import menu
from classes import *
from vector import *

DEBUG = False

lib = "./lib"
image_lib = lib + "/images"

FPS = 25
GAME_ICON_IMAGE = pygame.image.load(image_lib + "/game_icon.png")
WIDTH = 1366
HEIGHT = 716
DIAGONAL = Vector(WIDTH, HEIGHT)
# CAMERA_SLACK = min(WIDTH, HEIGHT)//5
BACKGROUND_COLOR = Color.BLACK
BASIC_FONT_NAME = 'FreeSansBold.ttf'

ARROW_ACCELERATION = 2

STAR_DENSITY = 80

PLAY_IMAGE = pygame.image.load(image_lib + "/play.png")
PLAY_SIZE = (100, 100)
PAUSE_IMAGE = pygame.image.load(image_lib + "/pause.png")
PAUSE_SIZE = (100, 100)
def main(sprites=[], initial_time=0): # maybe, without parameters?
	"Main outer function for the game."
	global FPS_CLOCK, DISPLAY_SURFACE, BASIC_FONT
	# preparing defaults
	pygame.init()
	FPS_CLOCK = pygame.time.Clock()
	pygame.display.set_icon(GAME_ICON_IMAGE)
	DISPLAY_SURFACE = pygame.display.set_mode((WIDTH, HEIGHT), HWSURFACE|DOUBLEBUF|RESIZABLE)
	pygame.display.set_caption('Space Combat')
	BASIC_FONT = pygame.font.Font(lib + '/' + BASIC_FONT_NAME, 32)
	# creating initials/loading save
	clean()
	if not sprites :
		Ship.create("player", radii_vector=Vector(WIDTH//2, HEIGHT//2))
		Ship.player.storage = Storage(human=2, selen=20, hydrogen=7.5)
		enemy = Ship.create("fighter-1", radii_vector=Vector(randint(0, WIDTH), randint(0, HEIGHT)))
		enemy.goal = Ship.player
		enemy.shooting = True
		Planet.create("earth", Vector(1, 1))
	else:
		Sprite.reload_dependencies(sprites)
		Sprite.reload_images()
	run_game(initial_time)

def run_game(initial_time=0):
	"Function for game iterating."

	global start_time, local_time, pause_time, surfaces, surface_positions

	# camera_position.x and camera_position.y are the top left of where the camera_position view is
	camera_position = Vector(0, 0)

	 # player motion controlers
	mouse_control = False
	mouse_steering = False

	start_time = time() - initial_time
	local_time = initial_time # time settings
	Local.local_time = initial_time # translate time to module 'classes'
	pause_time = 0
	last_menu_time = 0

	# start off with some random star images on the screen
	for i in range(10):
		new_star(camera_position, place='in')

	# effects
	# surface = pygame.transform.smoothscale($image, $size)
	# surface.set_alpha(100)

	while True: # main game loop
		collide() # detect collisions (from module classes)
		# updating
		local_time = time() - start_time - pause_time
		Local.local_time = local_time # translate time to module 'classes'
		# Effect.update_all()
		Planet.update_all()
		Shell.update_all()
		Ship.update_all()

		if Ship.player.health <= 0:
			outprint("Your spaceship was destroyed!", 0, HEIGHT//3)
			Ship.player.destroy()
			pause()

		if mouse_control:
			x, y = pygame.mouse.get_pos()
			Ship.player.a ^= (Vector(x, y) - DIAGONAL/2).angle
		if mouse_steering:
			x, y = pygame.mouse.get_pos()
			Ship.player.angle = (Vector(x, y) - DIAGONAL/2).angle

		# go through all the stars and see if any need to be deleted
		for star in Star.stars[:]:
			if not is_active(camera_position, star):
				star.destroy()
		
		# add more stars if we don't have enough
		while len(Star.stars) < STAR_DENSITY:
			new_star(camera_position)

		# adjust camera_position if beyond the "camera_position slack" circle
		screen_center = Vector(camera_position.x + WIDTH//2, camera_position.y + HEIGHT//2) # screen center vector
		local_position =  Ship.player.center_r - screen_center # vector from the screen center to the  center of player's ship
		# if local_position > CAMERA_SLACK + 0:
		# camera_position += local_position.decreased(CAMERA_SLACK)
		camera_position += local_position

		# drawing
		DISPLAY_SURFACE.fill(BACKGROUND_COLOR)
		Star.draw_all(DISPLAY_SURFACE, camera_position)
		# Effect.draw_all(alpha-surface, camera_position)
		Planet.draw_all(DISPLAY_SURFACE, camera_position)
		Shell.draw_all(DISPLAY_SURFACE, camera_position)
		Ship.draw_all(DISPLAY_SURFACE, camera_position)
		draw_map(DISPLAY_SURFACE, camera_position)
		# out_rect = pygame.Rect(int(player.r.x) - camera_position.x, |
		#                        int(player.r.y) - camera_position.y, |
		#                        player.width,                        | mesh for blackhole (?!)
		#                        player.height)                       |
		# DISPLAY_SURFACE.blit(player.image, out_rect)                |
		Ship.player.draw_meters(DISPLAY_SURFACE)
		if DEBUG:
			Local.show_vectors(DISPLAY_SURFACE, camera_position)
		
		# event handling loop
		for event in pygame.event.get():

			if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
				terminate()

			elif event.type == KEYDOWN:
				if event.key in (K_UP, K_DOWN, K_LEFT, K_RIGHT, K_RSHIFT, K_RCTRL):
					Ship.player.a | ARROW_ACCELERATION
					Ship.player.reset_mode("keep")
				if event.key == K_UP: Ship.player.a ^= pi/2
				elif event.key == K_DOWN: Ship.player.a ^= - pi/2
				elif event.key == K_LEFT: Ship.player.a ^= pi
				elif event.key == K_RIGHT: Ship.player.a ^= 0
				elif event.key == K_RSHIFT: Ship.player.a ^= Ship.player.angle
				elif event.key == K_RCTRL: Ship.player.stop()
				elif event.key == K_o: Ship.player.shooting = not Ship.player.shooting
				elif event.key == K_TAB: Ship.player.shooting = True
				elif event.key in (K_p, K_SPACE, K_BREAK, K_PAUSE, K_MENU): pause()

			elif event.type == KEYUP:
				if event.key in (K_UP, K_DOWN, K_LEFT, K_RIGHT, K_RSHIFT, K_RCTRL):
					Ship.player.reset_mode("keep")
					Ship.player.a | 0
				elif event.key == K_TAB: Ship.player.shooting = False
				elif event.key == K_SLASH: change_debug_mode()
				elif event.key == K_f: Ship.player.reset_mode("follow")
				elif event.key == K_a: Ship.player.reset_mode("keep")
				elif event.key == K_h: Ship.player.reset_mode("hunt")
				elif event.key == K_s: Ship.player.reset_mode("stop")
				elif event.key == K_e:
					enemy = Ship.create("fighter-1", radii_vector=camera_position + Vector(randint(0, WIDTH), randint(0, HEIGHT)))
					enemy.goal = Ship.player
					enemy.shooting = True
				elif event.key == K_g:
					if (len(Ship.enemies) >= 1) and ((Ship.player.goal == None) or (Ship.player.goal == Ship.enemies[0])):
						Ship.player.goal = Ship.enemies[-1]
					elif len(Ship.enemies) > 1:
						Ship.player.goal = Ship.enemies[Ship.enemies.index(Ship.player.goal) - 1]
				elif event.key == K_c: Ship.player.goal = None
				elif event.key == K_t: Ship.player.targeting = not Ship.player.targeting
			
			elif event.type == MOUSEBUTTONDOWN:
				x, y = event.pos
				if event.button == 1:
					Ship.player.a = Polar(ARROW_ACCELERATION, (Vector(x, y) - DIAGONAL/2).angle)
					mouse_control = True
				elif event.button == 2:
					string = "There "
					if len(Ship.enemies) == 0:
						string += "is no enemies."
					elif len(Ship.enemies) == 1:
						string += "is 1 enemy..."
					else:
						string += "are {} enemies...".format(len(Ship.enemies))
					string = str(Ship.enemies[0].storage.hydrogen)
					outprint("Hello, player!" + string, x - WIDTH//2, y - HEIGHT//2)
				elif event.button == 3:
					Ship.player.angle = (Vector(x, y) - DIAGONAL/2).angle
					mouse_steering = True
					last_targeting = Ship.player.targeting
					Ship.player.targeting = False
					
			elif event.type == MOUSEBUTTONUP:
				if event.button == 1:
					Ship.player.a | 0
					mouse_control = False
				elif event.button == 3:
					mouse_steering = False
					Ship.player.targeting = last_targeting
			
			elif event.type == MOUSEMOTION:
				if mouse_control:
					x, y = event.pos
					Ship.player.a ^= (Vector(x, y) - DIAGONAL/2).angle
				if mouse_steering:
					x, y = event.pos
					Ship.player.angle = (Vector(x, y) - DIAGONAL/2).angle

		pygame.display.update()			
		FPS_CLOCK.tick(FPS)



def pause(intertime=FPS):
	global pause_time, last_menu_time
	start = time()
	pause_surface = pygame.transform.smoothscale(PAUSE_IMAGE, PAUSE_SIZE)
	pause_surface = pause_surface.convert_alpha()
	pause_position = (WIDTH//2 - PAUSE_SIZE[0]//2, HEIGHT//2 - PAUSE_SIZE[1]//2)
	DISPLAY_SURFACE.blit(pause_surface, pause_position)
	pygame.display.update()
	menu.main()
	inside = True
	while inside:
		FPS_CLOCK.tick(intertime)
		for event in pygame.event.get():
			if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
				pass # terminate()
			elif (event.type == KEYUP) and (event.key in (K_p, K_SPACE, K_BREAK, K_PAUSE, K_MENU)):
				inside = False
				if menu.exist:
					menu.close()
	if Ship.player is None or (Ship.player.health <= 0):
		terminate()
	end = time()
	pause_time += end - start
	last_menu_time = end

def new_star(camera_position, place="out"): # place = "in"/"out" visible screen (but anyway in Active Area).
	"Create new star in or out of the visible screen."
	star = Star()
	if place == 'out':
		position = get_random_off_camera_position(camera_position, star)
		star.r = Vector(position[0], position[1])
	elif place == 'in':
		position = get_random_in_camera_position(camera_position, star)
		star.r = Vector(position[0], position[1])
	star.rect = pygame.Rect( (star.r.x, star.r.y, star.width, star.height) )
	return star

def draw_map(display_surface, camera_position): # TODO: to complete
	"Draw map of Active Area, and other on border in TOP RIGHT corner. TR:[O]LL"
	scale = 1.0/5  # could be changed
	horizontal_size = int(WIDTH * scale)
	vertical_size = int(HEIGHT * scale)
	down_shift = 32 # '32' is (smth like) letter height # HEIGHT//20 # could NOT be changed 
	outprint("Map", WIDTH//2 - horizontal_size//2, 15 - HEIGHT//2, color = Color.WHITE) # '15' is letter sensative constant
	pygame.draw.rect(display_surface, Color.GREY,
		pygame.Rect(WIDTH - horizontal_size, down_shift, horizontal_size, vertical_size), 1)
	# outprint('.', WIDTH//2 - horizontal_size//2, vertical_size//2 - HEIGHT//2 + down_shift, color = GREEN)
	screen_center = Vector(camera_position.x + WIDTH//2, camera_position.y + HEIGHT//2)
	map_center = Vector(WIDTH - horizontal_size//2, vertical_size//2 + down_shift)
	pygame.draw.circle(display_surface, Color.GREEN, map_center.get_int_tuple(), 2)
	for enemy in Ship.enemies:
		to_enemy = enemy.center_r - screen_center
		if is_visible(camera_position, enemy):
			enemy_position = scale*to_enemy + map_center
			pygame.draw.circle(display_surface, Color.RED, enemy_position.get_int_tuple(), 2)
		else:
			# set (red) color tone with account of distance
			if is_active(camera_position, enemy):
				red_tone = Color.RED
			elif not is_active(camera_position, enemy) and to_enemy.length < 5 * max(WIDTH, HEIGHT):
				red_tone = Color.LIGHT_RED
			else:
				red_tone = Color.FADED_RED
			angle = to_enemy.angle
			w = horizontal_size//2
			h = vertical_size//2
			# draw point (enemy) on map rectangle border (4 cases)
			if (sin(angle) != 0) and ((cos(angle) == 0) or (1.0*w/h >= abs(1.0/tan(angle)))):
				if abs(angle) == pi/2:
					x_shift = 0
				else:
					x_shift = h/tan(angle)
				if angle > 0:
					circle_position = ( int(map_center.x + x_shift), int(map_center.y - h) )
				else:
					circle_position = ( int(map_center.x - x_shift), int(map_center.y + h) )
			else:
				y_shift = w * tan(angle)
				if cos(angle) > 0:
					circle_position = ( int(map_center.x + w), int(map_center.y - y_shift) )
				else:
					circle_position = ( int(map_center.x - w), int(map_center.y + y_shift) )   
			pygame.draw.circle(display_surface, red_tone, circle_position, 2)

def is_active(camera_position, obj):
	"Check whether object 'obj' is out of the Active Area ( 3 width x 3 height)."
	# Return False if camera_position_x and camera_position_y are more than
	# a half-window length beyond the edge of the window.
	left_edge = camera_position.x - WIDTH
	top_edge = camera_position.y - HEIGHT
	bounds_rectangle = pygame.Rect(left_edge, top_edge, WIDTH * 3, HEIGHT * 3)
	object_rectangle = pygame.Rect(obj.r.x, obj.r.y, obj.width, obj.height)
	return bounds_rectangle.colliderect(object_rectangle)

def is_visible(camera_position, obj):
	"Check whether object 'obj' is in visible screen (probably, not entire)."
	return (camera_position.x - obj.width < obj.r.x < camera_position.x + WIDTH) and\
		(camera_position.y - obj.height < obj.r.y < camera_position.y + HEIGHT)

def get_random_off_camera_position(camera_position, obj):
	"Return random x and y of postion out of visible screen but in Active Area."
	# create a Rect of the camera_position view
	camera_position_rectangle = pygame.Rect(camera_position.x, camera_position.y, WIDTH, HEIGHT)
	while True:
		x = randint(int(camera_position.x - WIDTH), int(camera_position.x + 2*WIDTH))
		y = randint(int(camera_position.y - HEIGHT), int(camera_position.y + 2*HEIGHT))
		# create a Rect object with the random coordinates and use colliderect()
		# to make sure the right edge isn't in the camera_position view.
		obj_rectangle = pygame.Rect(x, y, obj.width, obj.height)
		if not obj_rectangle.colliderect(camera_position_rectangle):
			return x, y

def get_random_in_camera_position(camera_position, obj):
	"Return random x and y of postion in the visible screen."
	# create a Rect of the camera_position view
	camera_position_rectangle = pygame.Rect(camera_position.x, camera_position.y, WIDTH, HEIGHT)
	x = randint(camera_position.x, camera_position.x + WIDTH - obj.width)
	y = randint(camera_position.y, camera_position.y + HEIGHT - obj.height)
	return x, y

def outprint(input_string, x=0, y=0, color=Color.RED, font=None):
	"Additional. Print input string in the center of Visible screen in RED."
	if font == None:
		font = BASIC_FONT
	printing_surface = font.render(input_string, True, color)
	printing_rectangle = printing_surface.get_rect()
	printing_rectangle.center = (x + WIDTH//2, y + HEIGHT//2)
	DISPLAY_SURFACE.blit(printing_surface, printing_rectangle)

def set_width(new_width):
	global WIDTH
	WIDTH = new_width

def set_height(new_height):
	global HEIGHT
	HEIGHT = new_height

def set_fps(new_FPS):
	global FPS
	FPS = new_FPS

def toggle_debug_mode():
	global DEBUG
	DEBUG = not DEBUG

def terminate():
	"Stop the program."
	sprint("Closed.") # from vector
	pygame.quit()
	exit() # from sys


if __name__ == '__main__':
	main()
