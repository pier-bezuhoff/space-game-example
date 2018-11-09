#!/usr/bin/env python3

import pickle
import tkinter
from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
import space_game
from classes import *

lib = "./lib"
image_lib = lib + "/images"
save_path = lib + "/saves"

exist = True

def new_game():
	print("New game!")
	root.destroy()
	clean()
	space_game.main()

def open_file():
	name = askopenfilename(initialdir=save_path, title="Choose file",
		filetypes=(("pickle dump files", "*.pickle"), ("all files", "*.*")))
	with open(name, 'rb') as file:
		 # + Effect.effects
		Sprite._sprites, Ship.ships, Shell.shells, Planet.planets, initial_time = pickle.load(file)
		Sprite.sprites = Sprite._sprites + Ship.ships + Shell.shells + Planet.planets
		Sprite.reload_images(Sprite.sprites)
	print("Game is loaded from file {}.".format(name))
	close()
	space_game.main(Sprite.sprites, initial_time)

def save_to_file():
	name = asksaveasfilename(initialdir=save_path, title="Choose directory and filename",
		filetypes=(("pickle dump files", "*.pickle"), ), initialfile="last_save")
	with open(name, 'wb') as file:
		 # + Effect.effects
		pickle.dump((Sprite._sprites, Ship.ships, Shell.shells, Planet.planets, space_game.local_time), file)
	print("Game saved to file {}.".format(name))

def set(element, element_name, setter):
	master = root
	master.geometry('{}x20+0+0'.format(space_game.WIDTH))
	entry = Entry(master)
	entry.insert(0, element)
	entry.grid(row=2)
	entry.focus_set()
	def get(event):
		element = int(entry.get())
		entry.destroy()
		master.geometry('{}x0+0+0'.format(space_game.WIDTH))
		setter(element)
		print("New {} = {}".format(element_name, element))
	entry.bind('<Return>', get)
	entry.bind('<Escape>', lambda event: entry.destroy())

def display_task():
	pass

def display_control():

	master = Toplevel() # a la Tk(), just for setting icon	
	master.bind('<Escape>', lambda event: master.destroy())
	master.wm_title("Key Bindings & Control")
	width, height = 1090, 422
	text = Text(master, width=width, height=height)
	scroll = Scrollbar(master, command=text.yview)
	text.configure(yscrollcommand=scroll.set)
	text.tag_configure("colored", foreground='#476042', font=('Tempus Sans ITC', 9, 'bold'))
	with open(lib + "/manual_ru.txt") as file:
		manual = file.read()
		# manual = manual.decode('utf-8')
	text.insert(END, manual, "colored")
	text.pack(side=LEFT)
	scroll.pack(side=RIGHT, fill=Y)
	control_icon = PhotoImage(file=image_lib + "/control_icon.gif")
	master.tk.call('wm', 'iconphoto', master._w, control_icon)
	master.geometry('{}x{}+{}+{}'.format(width, height, 400, 0))

def display_about():
	print("This is a simple example of a menu")

def close():
	# if Ship.player and Ship.player.health > 0:
	root.destroy()
	global exist
	exist = False
	# save_to_file()

# main
def main():    
	global root, exist
	exist = True
	root = Tk()	
	root.bind('<Escape>', lambda event: close(), add='+')
	root.bind('<space>', lambda event: close(), add='+')
	root.bind('<p>', lambda event: close(), add='+')
	root.bind('<Pause>', lambda event: close(), add='+')
	root.wm_title("Game menu")
	menu = Menu(root)
	root.config(menu=menu)
	file_menu = Menu(menu)
	menu.add_cascade(label="File", menu=file_menu)
	file_menu.add_command(label="New game", command=new_game)
	file_menu.add_command(label="Open...", command=open_file)
	file_menu.add_command(label="Save...", command=save_to_file)
	file_menu.add_separator()
	file_menu.add_command(label="Close menu", command=close)
	file_menu.add_command(label="Exit", command=space_game.terminate)

	option_menu = Menu(menu)
	menu.add_cascade(label="Options", menu=option_menu)

	# space_game.FPS, space_game.WIDTH, space_game.HEIGHT
	option_menu.add_command(label="Frame per second", command=lambda: set(space_game.FPS, "Frame per second", space_game.set_fps))
	option_menu.add_command(label="Window width", command=lambda: set(space_game.WIDTH, "Window width", space_game.set_width))
	option_menu.add_command(label="Window height", command=lambda: set(space_game.HEIGHT, "Window height", space_game.set_height))
	option_menu.add_command(label="Toggle debugging", command=lambda: space_game.toggle_debug_mode())

	help_menu = Menu(menu)
	menu.add_cascade(label="Help", menu=help_menu)
	help_menu.add_command(label="Current task", command=display_task)
	help_menu.add_command(label="Key bindings & control", command=display_control)
	help_menu.add_command(label="About...", command=display_about)


	root.geometry('{}x0+0+0'.format(space_game.WIDTH)) # set "[width]x[height]+[x]+[y]""
	icon = PhotoImage(file=image_lib + "/menu_icon.gif")
	root.tk.call('wm', 'iconphoto', root._w, icon)
	root.mainloop()

if __name__ == '__main__':
	main()