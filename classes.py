# python3 compatible

from random import randint
from copy import copy
import math
import pygame
from pygame.locals import *
from vector import *
import space_game
import pickle


lib = "./lib"
dict_lib = lib + "/dicts"
image_lib = lib + "/images"
G = 10 # gravity constant

class Local:
	"Retranslator."
	local_time = 0

	@staticmethod
	def show_vectors(display_surface, camera_position):
		for sprite in Ship.ships:
			position = sprite.center_r - camera_position
			display(10*sprite.v, display_surface, int(position.x), int(position.y), color=Color.GREEN)
			display(100*sprite.a, display_surface, int(position.x), int(position.y))

def display(v, surf, x=None, y=None, color=(0, 0, 255), width=2):
	if x == None:
		x = surf.get_width()//2
	if y == None:
		x = surf.get_height()//2
	pygame.draw.circle(surf, (255, 0, 0), (x, y), 2, 2)
	pygame.draw.line(surf, color, (x, y), (x + v.x, y + v.y), width)
	pygame.display.update()

class Color:
	# color =          (  R,   G,   B)
	BLACK =            (  0,   0,   0)
	WHITE =            (255, 255, 255)
	GREY =             ( 64,  64,  64)
	RED =              (255,   0,   0)
	LIGHT_RED =        (128,   0,   0)
	FADED_RED =        ( 64,   0,   0)
	YELLOW =           (255, 255,   0)
	ORANGE =           (255, 128,   0)
	BROWN =            (128, 64,    0)
	GREEN =            (  0, 255,   0)
	BLUE =             (  0,   0, 255)
	LIGHT_BLUE =       (128, 128, 255)
	VIOLET =           (128,   0, 128)
	PINK =             (255, 192, 203)

class Sprite:

	# images

	sprite_dict = {}

	sprites = []
	_sprites = []

	def __init__(self, image_path, size, radii_vector=Vector(0, 0), angle=0, velocity_vector=Vector(0, 0), acceleration_vector=Vector(0, 0), type_name="new", clear=False):
		self.image_path = image_path
		image = pygame.image.load(image_path)
		self.image = pygame.transform.smoothscale(image, size)
		self.width, self.height = size
		self.size = size
		self.r = radii_vector
		self.angle = angle
		self.v = velocity_vector
		self.a = acceleration_vector
		self.creation_time = Local.local_time
		self.type = type_name

		self.goal = None
		self.targeting = True
		self.modes = ["move", ]
		self.max_speed = None
		self.max_acceleration = None

		Sprite.sprites.append(self)
		if clear:
			Sprite._sprites.append(self)


	@staticmethod
	def create(sprite_type_name, radii_vector=Vector(0, 0), angle=0, velocity_vector=Vector(0, 0), acceleration_vector=Vector(0, 0)):
		sprite_type = Sprite.sprite_dict[type_name]
		self = Sprite(sprite_type["image_path"], sprite_type["size"], copy(radii_vector), angle, copy(velocity_vector), copy(acceleration_vector), type_name=sprite_type_name)
		self.max_speed = sprite_type["max_speed"]
		self.max_acceleration = sprite_type["max_acceleration"]
		self.type = sprite_type_name
		self.modes = sprite_type["modes"]
		return self

	def destroy(self):
		Sprite.sprites.remove(self)
		del self

	def update(self):
		for function_name in self.modes:
			self.do(function_name)()

	@staticmethod
	def update_all():
		for sprite in Sprite.sprites:
			sprite.update()

	@staticmethod
	def update_all_clear():
		for sprite in Sprite._sprites:
			sprite.update()

	@staticmethod
	def update_list(list_):
		for sprite in list_:
			sprite.update()

	def get_modes(self):
		return self.modes

	def print_modes(self): # additional
		cprint(self.modes)

	def set_modes(self, *function_names):
		"Change all commands."
		self.modes = function_names

	def reset_mode(self, function_name):
		"Change last command."
		self.modes[0] = function_name

	def do(self, function_name):
		"Using: self.do($function_name)(*args, **kwargs)."
		return getattr(self, function_name)

	def move(self):
		self.r += self.v
		self.v += self.a
		if self.v > self.max_speed > 0:
			self.v | self.max_speed
		if self.targeting and (self.goal is None) and (self.v != 0):
			self.angle = self.v.angle
		if self.targeting and (self.goal is not None):
			self.angle = (self.goal.center_r - self.center_r).angle

	def keep(self):
		"Do nothing (for player using for arrow control)."
		pass

	def fear(self, fearful_type=None, fear_range=100):
		"Make running away if fearful one is nearer than fear range."
		if fearful_type is None:
			fearful_type = "fighter-1"
		for ship in Ship.ships:
			if ship.type == fearful_type and distance(self.r, ship.r) < 2*fear_range and ship != self:
				difference_vector = self.center_r - ship.center_r
				if (difference_vector).length < (self.middle_size + ship.middle_size)/2:
					self.a = Polar(self.max_acceleration, difference_vector.angle)
		for shell in Shell.shells:
			if shell.type == fearful_type and distance(self.r, ship.r) < 2*fear_range:
				difference_vector = self.center_r - shell.center_r
				difference = difference_vector.length
				# alpha = shell.v^difference_vector
				# if (self.v.length*difference*math.cos(alpha))/shell.v.length - difference*math.math.sin(alpha) > (self.middle_size + shell.middle_size)/2:
				if difference < (self.middle_size + shell.middle_size)/2:
						self.a ^= difference_vector.angle

	def fly_round(self, goal=None, obstacles=None):
		if goal is None:
			goal = self.goal
		if goal is not None and self.storage.selen > 0:
			if obstacles is None:
				obstacles = Planet.planets
			to_goal = (goal.center_r - self.center_r)
			a, b, c = to_goal.get_line(tuple(self.center_r))
			obstacles = filter(lambda p: abs(a*p.center_r.x + b*p.center_r.y + c) < p.radii + self.height/2, obstacles)
			try:
				# obstacle to be flown round
				p = min(obstacles, key=lambda p: distance(self.center_r, p.center_r))
				to_p = p.center_r - self.center_r
				if math.sin(to_goal^to_p) > 0:
					self.a += to_goal >> 1
				else: 
					self.a += to_goal << 1
			except ValueError:
				pass

	def follow(self, goal=None):
		"Smart following the goal."
		# add flying round planets
		if goal is None:
			goal = self.goal
		if goal is not None:
			to_goal = goal.center_r - self.center_r

			K1 = 10 ** (-3) # | \\ (k)coefficients
			K2 = 10 ** (15) # | picked constants
			D1 = 2/3        # | using analogy of two forces: attracive and repulsive
			D2 = -7         # | \\ degrees
			
			if (to_goal.length != 0):
				self.a = to_goal * ( (K1 * (to_goal.length ** D1)) - (K2 * (to_goal.length ** D2)) ) # steering equation
			else:
				self.a | self.max_acceleration
			if (False or self.a.length > self.max_acceleration):
				self.a | self.max_acceleration
			if (to_goal.length < 1.5 * (goal.max_size + self.max_size)) and (self.v ^ to_goal < math.pi/12):
				self.a = to_goal >> self.max_acceleration # deviation
			if self.targeting:
				self.angle = to_goal.angle
		
	def hunt(self, goal=None):
		"Merely try to rush into the goal."
		if goal is None:
			goal = self.goal
		if goal is not None:
			to_goal = goal.center_r - self.center_r
			self.a = to_goal
			self.a | (self.max_acceleration)
			if self.targeting:
				self.angle = to_goal.angle

	def approach(self, goal):
		to_goal = goal.center_r - self.center_r
		if self.v.length*abs(math.sin(self.v ^ to_goal)) > self.max_speed/10:
			self.stop()
		else:
			self.a = Polar(self.max_acceleration, to_goal.angle)

	def turn_to(self, goal, time):
		to_goal = goal.center_r - self.center_r
		alpha = self.v ^ to_goal
		D = self.v.qlength*(math.cos(alpha) - 1) + (self.max_acceleration*time)**2 # discriminant
		if D < 0:
			D = 0
		k = self.v.length + math.sqrt(D)
		if time != 0:
			self.a = (-self.v + to_goal.with_length(k))/time
		# Local.drawings = [(self.a, self.center_r)]

	def stop(self):
		self.a = -self.v
		if self.a.length > self.max_acceleration:
			self.a | self.max_acceleration

	def is_visible(self, camera_position):
		return (-2*self.width <= self.r.x - camera_position.x <= space_game.WIDTH) and\
		(-2*self.height <= self.r.y - camera_position.y <= space_game.HEIGHT)

	def draw(self, display_surface, camera_position):
		if self.is_visible(camera_position):
			rotated_image = pygame.transform.rotate(self.image, 180/math.pi * self.angle)
			rectangle = rotated_image.get_rect()
			rectangle.center = tuple(self.center_r - camera_position)
			display_surface.blit(rotated_image, rectangle)

	@staticmethod
	def draw_all(display_surface, camera_position):
		for sprite in Sprite.sprites:
			sprite.draw(display_surface, camera_position)

	@staticmethod
	def draw_all_clear(display_surface, camera_position):
		for sprite in Sprite._sprites:
			sprite.draw(display_surface, camera_position)

	@staticmethod
	def draw_list(list_, display_surface, camera_position):
		for sprite in list_:
			sprite.draw(display_surface, camera_position)

	@staticmethod
	def reload_dependencies(sprites=sprites):
		clean()
		Sprite.sprites = sprites
		Ship.ships = [sprite for sprite in sprites if type(sprite) is Ship]
		Shell.shells = [sprite for sprite in sprites if type(sprite) is Shell]
		Planet.planets = [sprite for sprite in sprites if type(sprite) is Planet]
		Sprite._sprites = [sprite for sprite in sprites if type(sprite) is Sprite]

		Ship.enemies = [ship for ship in Ship.ships if ship.type in Ship.enemy_names]
		players = [ship for ship in Ship.ships if ship.type == "player"]
		if len(players) == 0:
			sprint("There is not players. Created new one.")
			Sprite.player = Ship.create("player", radii_vector=Vector(space_game.HALF_WIDTH, space_game.HALF_HEIGHT))
		elif len(players) == 1:
			Ship.player = players[0]
		else:
			sprint("There are more than one players in Ship.ships. Choosed random one.")
			Ship.player = players[0]
		for enemy in Ship.enemies:
			enemy.goal = Ship.player

	@staticmethod
	def reload_images(list_=sprites):
		for sprite in list_:
			image = pygame.image.load(sprite.image_path)
			sprite.image = pygame.transform.smoothscale(image, sprite.size)


	@property
	def center_r(self):
		return Vector(self.r.x + self.width/2, self.r.y + self.height/2)

	@center_r.setter
	def center_r(self, new_center_r):
		self.r = new_center_r - Vector(self.width/2, self.height/2)

	@property
	def rect(self):
		rect = self.image.get_rect()
		rect.center = self.center_r.get_int_tuple()
		return rect

	@property
	def max_size(self):
		"Return max of sprite's width and height."
		return max(self.width, self.height)

	@property
	def min_size(self):
		"Return max of sprite's width and height."
		return min(self.width, self.height)

	@property
	def middle_size(self):
		"Return middle of width and height."
		return (self.width + self.height)/2

	@property
	def diameter(self):
		return (self.height + self.width)/2

	@property
	def radii(self):
		return (self.height + self.width)/4
	
	@property
	def diagonal(self):
		"Return hypot of sprite's width and height."
		return math.hypot(self.width, self.height)


class Storage:
	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)

	def __iter__(self):
		return iter(self.__dict__)

	def __getitem__(self, key):
		return getattr(self, key)

	def __setitem__(self, key, value):
		setattr(self, key, value)

class Ship(Sprite):

	PLAYER_IMAGE_PATH = image_lib + "/craft.png"
	FIGHTER1_IMAGE_PATH = image_lib + "/fighter1.png"

	ship_dict = {
		"player":    {"image_path": PLAYER_IMAGE_PATH,   "size": (75, 75), "max_speed": 30, "max_acceleration": 2, "fire_period": 0.5, "health": 1000, "shell_types": ["green_rocket", ], "shooter": "shoot",			 "modes":    [ "keep", "move"]},
		"fighter-1": {"image_path": FIGHTER1_IMAGE_PATH, "size": (75, 75), "max_speed": 20, "max_acceleration": 1, "fire_period": 0.5, "health": 50,   "shell_types": ["red_rocket", ],   "shooter": "shoot_feetforward", "modes": ["fear", "follow", "fly_round", "move"]}
	}

	enemy_names = ["fighter-1", ]
	enemies = []
	player = None
	ships = []

	def __init__(self, image_path, size, radii_vector=Vector(0, 0), angle=0, velocity_vector=Vector(0, 0), acceleration_vector=Vector(0, 0),
	fire_period=-1, health=1, capacity=10, storage=None, ship_type_name="new"):
		super().__init__(image_path, size, radii_vector, angle, velocity_vector, acceleration_vector, ship_type_name)
		self.fire_period = fire_period
		self.last_fire = Local.local_time
		self.health = health
		self.max_health = health

		self.capacity = capacity
		if storage:
			self.storage = storage
		else:
			self.storage = Storage(human=1, selen=14, hydrogen=1)

		self.shell_type = None
		self.shell_types = []

		self.shooter = None
		self.shooting = False

		self.modes = ["move"]

		self.computer = False

		Ship.ships.append(self)
		if ship_type_name in Ship.enemy_names:
			Ship.enemies.append(self)
			self.computer = True
		elif ship_type_name == "player":
			Ship.player = self

	@staticmethod
	def create(ship_type_name, radii_vector=Vector(0, 0), angle=0, velocity_vector=Vector(0, 0), acceleration_vector=Vector(0, 0)):
		ship_type = Ship.ship_dict[ship_type_name]
		self = Ship(ship_type["image_path"], ship_type["size"], copy(radii_vector), angle, copy(velocity_vector), copy(acceleration_vector), ship_type["fire_period"], ship_type["health"], ship_type_name=ship_type_name)
		self.max_speed = ship_type["max_speed"]
		self.max_acceleration = ship_type["max_acceleration"]
		self.type = ship_type_name
		self.shell_types = ship_type["shell_types"]
		self.shell_type = ship_type["shell_types"][0]
		self.shooter = ship_type["shooter"]
		self.modes = ship_type["modes"]
		return self

	def destroy(self):
		Sprite.sprites.remove(self)
		Ship.ships.remove(self)
		if self in Ship.enemies:
			Ship.enemies.remove(self)
		if self == Ship.player:
			Ship.player = None
		del self

	def update(self):
		if self.computer:
			if Planet.planets:
				# <remaining time in f> = 10*FPS*h[ydrogen] > (1 + 0)*(2*v_max/a_max)
				t = self.storage.hydrogen*10*space_game.FPS
				if t*self.max_acceleration <= 1.1*(2*self.max_speed):
					self.modes = ["search_hydrogen", "move"]
				elif self.storage.selen <= 1:
					self.modes = ["search_selen", "move"]
				else:
					self.modes = ["fear", "follow", "fly_round", "move"] # TODO: generalize variants
		for function_name in self.modes:
			self.do(function_name)()
		if self.shooting and (self.shell_type is not None) and (self.storage.selen > 0) and (Local.local_time - self.last_fire >= self.fire_period):
			self.do(self.shooter)()
			self.storage.selen -= 1

	@staticmethod
	def update_all():
		for ship in Ship.ships:
			ship.update()

	@staticmethod
	def update_list(list_):
		for ship in list_:
			ship.update()

	def do(self, function_name):
		"Using: self.do($function_name)(*args, **kwargs)."
		return getattr(self, function_name)

	def move(self):
		self.storage.hydrogen -= self.a.length/(10*self.max_acceleration*space_game.FPS)
		if self.storage.hydrogen <= 0:
			self.storage.hydrogen = 0
			self.a = Vector(0, 0)
		# TODO: gravity attraction
		self.r += self.v
		self.v += self.a
		if self.v.length > self.max_speed > 0:
			self.v | self.max_speed
		if self.targeting and (self.goal is None) and (self.v.length != 0):
			self.angle = self.v.angle
		if self.targeting and (self.goal is not None):
			self.angle = (self.goal.center_r - self.center_r).angle

	def search_hydrogen(self):
		planet = min(filter(lambda p: "hydrogen" in p.resources, Planet.planets), key=lambda p: (p.center_r - self.center_r).length)
		# <remaining time in f> = 10*FPS*h[ydrogen] > (1 + 0)*(2*v_max/a_max)
		t = self.storage.hydrogen*10*space_game.FPS
		self.turn_to(planet, t)

	def search_selen(self):
		planet = min(filter(lambda p: "selen" in p.resources, Planet.planets), key=lambda p: (p.center_r - self.center_r).length)
		self.approach(planet)

	def shoot(self):
		shell_type = Shell.shell_dict[self.shell_type]
		size = shell_type["size"]
		Shell.create(self.shell_type, self.type, (self.center_r - Vector(size[0]/2, size[1]/2)), self.angle, self.v, Vector(0, 0))
		self.last_fire = Local.local_time

	# from Java project (~/Documents/Java/Java projects/SpaceGame_second_attempt/src/root/Spaceship.java)

	def runningTime(self):
		target = self.goal
		weaponSpeed = Shell.shell_dict[self.shell_type]["max_speed"]
		d = target.center_r - self.center_r
		vX = target.v.x
		vY = target.v.y
		try:
			t1 = (-(target.v**d) + math.sqrt((target.v**d)**2 - d.qlength*(target.v.qlength - weaponSpeed**2)))/(target.v.qlength - weaponSpeed**2)
			t2 = (-(target.v**d) - math.sqrt((target.v**d)**2 - d.qlength*(target.v.qlength - weaponSpeed**2)))/(target.v.qlength - weaponSpeed**2)
		except (ValueError):
			t1 = t2 = 0
		except (ZeroDivisionError):
			t1 = t2 = 0
		if (t2>0) and (t1>0):
			running_time = min(t1, t2)
		else:
			running_time = max(t1, t2)
		return running_time
	
	def shoot_feetforward(self):
		if self.goal is not None:			
			target = self.goal
			d = target.center_r - self.center_r
			angle = d.angle + (( d + (self.runningTime()*target.v)) ^ d)
			
			shell_type = Shell.shell_dict[self.shell_type]
			size = shell_type["size"]
			Shell.create(self.shell_type, self.type, (self.center_r - Vector(size[0]/2, size[1]/2)), angle, self.v, Vector(0, 0))
			self.last_fire = Local.local_time

	# end of Java's
			
	def __shoot_feetforward_(self): # FIXME: correct algorithm -- work pretty awful
		if self.goal is not None:
			shell_type = Shell.shell_dict[self.shell_type]
			shell_velocity = Vector(0, shell_type["max_speed"])
			to_goal = self.goal.center_r - self.center_r
			 # to shoot feetforward:
			feetforward_sin = math.sin(math.pi - (self.v ^ to_goal)) * self.goal.v.length/shell_velocity.length
			if abs(feetforward_sin) <= 1:
				feetforward_angle = math.asin(feetforward_sin)
			else:
				feetforward_angle = 0
				cprint("Wrong argument! math.sin($angle) = {}".format(feetforward_sin))
			
			shell_velocity ^= feetforward_angle + to_goal.angle
			outprint("Angles: {1}*math.pi + {0}*math.pi = {2}*math.pi".format(feetforward_angle/math.pi, to_goal.angle/math.pi, shell_velocity.angle/math.pi))
			size = shell_type["size"]
			Shell.create(self.shell_type, self.type, (self.center_r - Vector(size[0]/2, size[1]/2)), self.angle, hell_velocity, Vector(0, 0))
			self.last_fire = Local.local_time

	@staticmethod
	def draw_all(display_surface, camera_position):
		for ship in Ship.ships:
			ship.draw(display_surface, camera_position)

	@staticmethod
	def draw_list(list_, display_surface, camera_position):
		for ship in list_:
			ship.draw(display_surface, camera_position)

	def draw_meters(self, display_surface):
		self.draw_health_meter(display_surface)
		self.draw_weapon_meter(display_surface)
		self.draw_fuel_meter(display_surface)

	def draw_health_meter(self, display_surface): # bad-looking
		"Display health of the ship with colored column in the left side of Visible screen."
		position = Vector(15, 5)
		if self.health >= 10000: # undead
			scale = 10000
			color = Color.PINK
		elif 10000 > self.health >= 1000:
			scale = 100
			color = Color.VIOLET
		elif 1000 > self.health >= 100:
			scale = 10
			color = Color.BLUE
		elif 100 > self.health >= 20:
			scale = 1
			color = Color.GREEN
		elif 20 > self.health > 0:
			scale = 1/5.0
			color = Color.RED
		else:
			scale = 1000000000 # dead
			color = Color.RED
		cell_size = Vector(15, space_game.HEIGHT/125)
		for i in range(int(self.health/scale)): # draw red health bars
			pygame.draw.rect(display_surface, color, (position.x, position.y + 100 + i*cell_size.y, cell_size.x, cell_size.y))
		for i in range(int(self.max_health/scale)): # draw the white outlines
			pygame.draw.rect(display_surface, Color.WHITE, (position.x, position.y + 100 + i*cell_size.y, cell_size.x, cell_size.y), 1)

	def draw_weapon_meter(self, display_surface):
		position = Vector(35, 5)
		# image = pygame.image.load(Shell.shell_dict[self.shell_type]["image_path"])
		# rotated_image = pygame.transform.rotate(image, 45)
		# rectangle = rotated_image.get_rect()
		# rectangle.center = (35, 25)
		# display_surface.blit(rotated_image, rectangle)
		filled_cells = int(self.storage.selen)
		cells = max(self.capacity, filled_cells)
		cell_size = Vector(15, space_game.HEIGHT/(1.5*cells))
		for i in range(filled_cells):
			pygame.draw.rect(display_surface, Color.BROWN, (position.x, position.y + 100 + i*(cell_size.y + 1), cell_size.x, cell_size.y))
		for i in range(cells):
			pygame.draw.rect(display_surface, Color.YELLOW, (position.x, position.y + 100 + i*(cell_size.y + 1), cell_size.x, cell_size.y), 1)

	def draw_fuel_meter(self, display_surface):
		position = Vector(55, 5)
		filled_cells = self.storage.hydrogen
		cells = max(self.capacity, filled_cells)
		cell_size = Vector(15, space_game.HEIGHT/(1.5*cells))
		pygame.draw.rect(display_surface, Color.LIGHT_BLUE, (position.x, position.y + 100, cell_size.x, filled_cells*cell_size.y))
		pygame.draw.rect(display_surface, Color.BLUE, (position.x, position.y + 100, cell_size.x, cells*cell_size.y), 1)

class Shell(Sprite):

	# images
	SHELL_GREEN_ROCKET_IMAGE_PATH = image_lib + "/green_rocket.png"
	SHELL_RED_ROCKET_IMAGE_PATH = image_lib + "/red_rocket.png"
	SHELL_Y_ROCKET_IMAGE_PATH = image_lib + "/y_rocket.png"
	SHELL_STANDARD_ROCKET_IMAGE_PATH = image_lib + "/rocket_shell.png"

	# TODO: add lasers
	shell_dict = {
		"green_rocket":    {"image_path": SHELL_GREEN_ROCKET_IMAGE_PATH,    "damage":  5, "max_speed":  35, "size": (59 ,10), "lifetime": 15}, 
		"red_rocket":      {"image_path": SHELL_RED_ROCKET_IMAGE_PATH,      "damage":  5, "max_speed":  35, "size": (63 ,10), "lifetime": 10},
		"Y_rocket":        {"image_path": SHELL_Y_ROCKET_IMAGE_PATH,        "damage": 15, "max_speed":  25, "size": (59 ,10), "lifetime": 20},
		"standard_rocket": {"image_path": SHELL_STANDARD_ROCKET_IMAGE_PATH, "damage":  3, "max_speed":  50, "size": (53 ,11), "lifetime": 5 },
		# "green_blaster":   {"image_path": SHELL_GREEN_BLASTER_IMAGE_PATH,   "damage":  1, "max_speed": 100, "size": (-0, -0), "lifetime": 2 },
		# "red_blaster":     {"image_path": SHELL_RED_BLASTER_IMAGE_PATH,     "damage":  1, "max_speed": 100, "size": (-0, -0), "lifetime": 2 }
	}
	shells = []
	mass = 100
	
	def __init__(self, owner_type, image_path, size, radii_vector=Vector(0, 0), angle=0, velocity_vector=Vector(0, 0), acceleration_vector=Vector(0, 0), damage=0, duration=-1, type_name="new"):
		super().__init__(image_path, size, radii_vector, angle, velocity_vector, acceleration_vector, type_name)
		self.owner_type = owner_type
		self.damage = damage
		self.duration = duration
		
		Shell.shells.append(self)

	@staticmethod
	def create(shell_type_name, owner_type, radii_vector=Vector(0, 0), angle=0, velocity_vector=Vector(0, 0), acceleration_vector=Vector(0, 0)):
		"Create shell of the type with the owner type, radii_vector, angle, speed direction and acceleration."
		shell_type = Shell.shell_dict[shell_type_name]
		self = Shell(owner_type, shell_type["image_path"], shell_type["size"], radii_vector, angle, copy(velocity_vector), acceleration_vector, shell_type["damage"], shell_type["lifetime"], shell_type_name)
		self.max_speed = shell_type["max_speed"]
		self.v = Polar(self.max_speed, self.angle)
		return self

	def destroy(self):
		Sprite.sprites.remove(self)
		Shell.shells.remove(self)
		del self

	def update(self):
		if self.duration > Local.local_time - self.creation_time:
			self.move()
		else:
			self.destroy()

	@staticmethod
	def update_all():
		for shell in Shell.shells:
			shell.update()

	def move(self):
		"Move shell."
		self.r += self.v
		self.v += self.a
		if self.max_speed > 0 and self.v.length > self.max_speed:
			self.v | self.max_speed
		self.a = vector_sum(*[(p.center_r - self.center_r)*(Shell.mass*G*p.mass/((p.center_r - self.center_r).length**3)) for p in Planet.planets])
		self.angle = self.v.angle

	@staticmethod
	def draw_all(display_surface, camera_position):
		for shell in Shell.shells:
			shell.draw(display_surface, camera_position)



class Planet(Sprite):

	# images
	EARTH_IMAGE_PATH = image_lib + "/earth.png"
	MOON_IMAGE_PATH =  image_lib + "/moon.png"
	SUN_IMAGE_PATH =   image_lib + "/sun.png"

	planet_dict = {
		"earth": {"image_path": EARTH_IMAGE_PATH, "size": (300, 300), "mass": 100,  "distance": 0, "speed": Vector(0, 0), "resources": ["human", "selen", "hydrogen"]},
		"moon":  {"image_path": MOON_IMAGE_PATH,  "size": (0, 0),     "mass": 0,    "distance": 0, "speed": Vector(0, 0), "resources": ["selen"]},
		"sun":   {"image_path": SUN_IMAGE_PATH,   "size": (700, 700), "mass": 1000, "distance": 0, "speed": Vector(0, 0), "resources": ["hydrogen"]}
	}
	planets = []

	def __init__(self, image_path, size, mass, radii_vector=Vector(0, 0), velocity_vector=Vector(0, 0), resources=[], name="Custom"):
		super().__init__(image_path, size, radii_vector, 0, velocity_vector, Vector(0, 0), name)
		self.mass = mass
		self.resources = resources # + capacity, production rate
		self.name = name
		Planet.planets.append(self)

	@staticmethod
	def create(name, radii_vector, velocity_vector=None):
		planet = Planet.planet_dict[name]
		if not velocity_vector:
			velocity_vector = planet["speed"]
		Planet(planet["image_path"], planet["size"], planet["mass"], radii_vector, velocity_vector, planet["resources"], name)

	def destroy(self):
		Sprite.sprites.remove(self)
		Planet.planets.remove(self)
		del self

	def update(self):
		self.move()

	@staticmethod
	def update_all():
		for planet in Planet.planets:
			planet.update()

	def move(self):
		self.r += self.v
		self.v += self.a
		# + attraction

	def draw(self, display_surface, camera_position):
		if (-self.width <= self.r.x - camera_position.x <= space_game.WIDTH) and\
		(-self.height <= self.r.y - camera_position.y <= space_game.HEIGHT):
			rectangle = self.image.get_rect()
			rectangle.center = tuple(self.center_r - camera_position)
			display_surface.blit(self.image, rectangle)

	@staticmethod
	def draw_all(display_surface, camera_position):
		for planet in Planet.planets:
			planet.draw(display_surface, camera_position)




class Star:

	STAR_IMAGE_PATH = image_lib + "/star.png"
	star_image = pygame.image.load(STAR_IMAGE_PATH)
	star_images = []
	for i in range(1, 5):
		star_images.append(pygame.transform.smoothscale(star_image, (5*i, 5*i)))

	stars = []

	def __init__(self, radii_vector=Vector(0, 0), angle=0):
		self.image = Star.star_images[randint(0, len(Star.star_images) - 1)]
		self.width  = self.image.get_width()
		self.height = self.image.get_height()

		self.rect = None
		
		Star.stars.append(self)

	def destroy(self):
		Star.stars.remove(self)
		del self

	def draw(self, display_surface, camera_position):
		rectangle = self.image.get_rect()
		rectangle.center = tuple(self.r - camera_position)
		display_surface.blit(self.image, rectangle)

	@staticmethod
	def draw_all(display_surface, camera_position):
		for star in Star.stars:
			star.draw(display_surface, camera_position)



class Effect:

	effects = []

	def __init__(self, radii_vector, duration, type_name="Unknown"):
		self.r = radii_vector
		self.creation_time = Local.local_time
		self.duration = duration
		self.type = type_name
		self.sprites = []
		
	@staticmethod	
	def create(radii_vector, type_name, **kwargs):
		self = None
		if type_name == "ship-ship collision":
			1
		elif type_name == "shell-ship collision":
			1
		elif type_name == "ship-planet collision":
			1
		elif type_name == "ship annihilation":
			1
		elif type_name == "shell-planet collision":
			1
		elif type_name == "shell annihilation":
			1
		elif type_name == "planet-planet collision":
			1
		return self

	def destroy(self):
		Effect.effects.remove(self)
		del self

	def update(self):
		for sprite in self.sprites:
			sprite.update()
		if not self.sprites:
			self.destroy()

	@staticmethod
	def update_all():
		for effect in Effect.effects:
			effect.update()

	def draw(self, display_surface, camera_position):
		for sprite in self.sprites:
			sprite.draw(display_surface, camera_position)

	@staticmethod
	def draw_all(display_surface, camera_position):
		for effect in Effect.effects:
			effect.draw(display_surface, camera_position)
	
	# TODO: fill

def collide():
	"Detect collisions."
	for ship in Ship.ships[:]:
		ship_croped_rect = (ship.rect[0] + 1,  ship.rect[1] + 1, ship.rect[2] - 1, ship.rect[3] - 1)
		# ship-planet
		for planet in Planet.planets:
			from_planet = ship.center_r - planet.center_r
			difference = planet.radii - from_planet.length # + ship.min_size)
			if difference > 0:
				ship.center_r = planet.center_r + from_planet.with_length(planet.radii)
				# ship.v *= 0.5
				ship.v = from_planet.with_length(int(0.3*ship.v.length))
				for resource in ship.storage:
					if resource in planet.resources and ship.storage[resource] < ship.capacity:
						ship.storage[resource] = ship.capacity
		# # ship-ship
		# for _ship in Ship.ships[:]:
		# 	to_this = ship.center_r - _ship.center_r
		# 	difference = ship.min_size + _ship.min_size - to_this.length
		# 	if difference > 0:
		# 		# crash!
		# ship-shell
		for shell in Shell.shells[:]:
			if (shell.owner_type != ship.type) and shell.rect.colliderect(ship_croped_rect):
				ship.health -= shell.damage
				if (ship.health <= 0) and ship in Ship.enemies:
					if ship == Ship.player.goal:
						Ship.player.goal = None
					ship.destroy() # TODO: generate annihilation effect
				shell.destroy()
				break

	for planet in Planet.planets:
		# # planet-planet
		# for _planet in Planet.planets:
		# 	if planet is not _planet:
		# 		to_this = planet.center_r - _planet.center_r
		# 		difference = planet.radii + _planet.radii - to_this.length
		# 		if difference > 0:
		# 			# momentum!
		# planet-shell
		for shell in Shell.shells[:]:
			if (planet.center_r - shell.center_r).length < planet.radii + shell.min_size:
				shell.destroy()

def clean():
	Sprite.sprites = []
	Ship.ships = []
	Ship.enemies = []
	Ship.player = None
	Shell.shells = []
	Planet.planets = []
	Effect.effects = []
	Star.stars = []
	Local.local_time = 0

def cprint(*args): # Y
	string = ", ".join([str(arg) for arg in args])
	print(string)

def sprint(arg): # Y
	print(str(arg))