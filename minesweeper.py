'''
This program utilizes pygame to allow one to play
Minesweeper. In the future, the plan is to
implement a solver to play the game for us,
if possible. The only case in which it
would prove impossible would be when
the next correct tile is a guessing game.
'''
import pygame
import pygame_textinput
import random		#RNG for mines
import sys			#exit cmd/powershell
import os			#working directory
import ctypes		#screen resolution (size)
import re			#string manipulation (scores text files)
import math			#for rainbow background (sine calc)
import pyautogui	#autoclicker (for AI)

#constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (211, 211, 211)
GRAY = (128, 128, 128)
roygbiv = 0
BEGINNER_WIDTH, BEGINNER_HEIGHT = 9, 9
INTERMEDIATE_WIDTH, INTERMEDIATE_HEIGHT = 16, 16
EXPERT_WIDTH, EXPERT_HEIGHT = 30, 16
BEGINNER_MINES = 10
INTERMEDIATE_MINES = 40
EXPERT_MINES = 99
TILE_SIZE = 60
LEFT, RIGHT = 1, 3 #left or right click pygame
AI = False;

#---------------------------initialize pygame---------------------------#
pygame.init()	
pygame.display.set_caption('Minesweeper')
ctypes.windll.user32.SetProcessDPIAware()
true_res = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
gameDisplay = pygame.display.set_mode(true_res, pygame.FULLSCREEN)
gameDisplay.fill(WHITE)
clock = pygame.time.Clock()
display_width, display_height = pygame.display.Info().current_w, pygame.display.Info().current_h
textinput = pygame_textinput.TextInput(font_family="comicsansms",font_size=40)

#--------------------------set variables--------------------------------#
game_mode = 'expert'
face_state = 'normal'
restart, won, lost, enter_finished, paused = False, False, False, False,False
new_score = True
save_time = 0
timer, start_ms, num_clicks = 0, 0, 0
scores = []
score_name = ""
#set size of board and number of respective mines/flags
if(game_mode == 'expert'):
	board_width, board_height = EXPERT_WIDTH, EXPERT_HEIGHT
	num_bombs, num_flags = EXPERT_MINES,EXPERT_MINES
elif(game_mode == 'intermediate'):
	board_width, board_height = INTERMEDIATE_WIDTH, INTERMEDIATE_HEIGHT
	num_bombs, num_flags = INTERMEDIATE_MINES,INTERMEDIATE_MINES
elif(game_mode == 'beginner'):
	board_width, board_height = BEGINNER_WIDTH, BEGINNER_HEIGHT
	num_bombs, num_flags = BEGINNER_MINES,BEGINNER_MINES
else:
	board_width,board_height = EXPERT_WIDTH, EXPERT_HEIGHT
	num_bombs, num_flags = EXPERT_MINES,EXPERT_MINES
board_x, board_y = display_width/2- board_width/2*TILE_SIZE, display_height/2- board_height/2*TILE_SIZE

#----------------------load/scale initial images-------------------------------#
tile_normal = pygame.image.load('assets/tiles/tile_normal.png')
tile_normal = pygame.transform.scale(tile_normal, (TILE_SIZE,TILE_SIZE))
tile_flagged = pygame.image.load('assets/tiles/tile_flagged.png')
tile_flagged = pygame.transform.scale(tile_flagged, (TILE_SIZE,TILE_SIZE))
tile_pics = []
for idx in range(9):
	tile_pics.append(pygame.transform.scale(
		pygame.image.load('assets/tiles/' + str(idx) + '.png'),(TILE_SIZE,TILE_SIZE)))

bomb_x = pygame.image.load('assets/mines/bomb_x.png')
bomb_x = pygame.transform.scale(bomb_x, (TILE_SIZE,TILE_SIZE))
bomb = pygame.image.load('assets/mines/bomb.png')
bomb = pygame.transform.scale(bomb, (TILE_SIZE,TILE_SIZE))
bomb_red = pygame.image.load('assets/mines/bomb_red.png')
bomb_red = pygame.transform.scale(bomb_red, (TILE_SIZE,TILE_SIZE))

face = pygame.image.load('assets/faces/face_' + face_state + '.png')
flags_1 = pygame.image.load('assets/numbers/9.png')
flags_10 = pygame.image.load('assets/numbers/9.png')
flags_100 = pygame.image.load('assets/numbers/0.png')
bombs_1 = pygame.image.load('assets/numbers/0.png')
bombs_10 = pygame.image.load('assets/numbers/0.png')
bombs_100 = pygame.image.load('assets/numbers/0.png')
num_size = bombs_1.get_size() #get height and width of image
face = pygame.transform.scale(face, (num_size[1],num_size[1]))

#----------------------create tile object-------------------------------#
class Tile():
	def __init__(self):
		self.bomb_count = 0
		self.image = tile_normal
		self.image_uncovered = tile_pics[self.bomb_count]
		self.is_bomb = False
		self.uncovered = False
		self.flagged = False
	def set_count(self,new_count):
		self.count = new_count
	def set_bomb(self,):
		self.is_bomb = True
		self.image_uncovered = bomb
		self.bomb_count = 9
	def set_image(self,new_img):
		self.image = new_img
	def uncover(self):
		self.uncovered = True
		self.set_image(self.image_uncovered)
	def flag(self):
		#flag if covered
		if not self.uncovered and not self.flagged:
			self.flagged = True
			self.set_image(tile_flagged)
			return True
		#unflag if already flagged
		elif self.flagged:
			self.flagged = False
			self.set_image(tile_normal)
			return False

tiles = [[Tile() for j in range(board_height)] for i in range(board_width)]

def uncover_all(x,y):
	#uncover designated tile and all surrounding non-mine squares
	global tiles
	if x > board_width-1 and y > board_height-1:
		return
	else:
		tiles[x][y].uncover()
		if tiles[x][y].bomb_count == 0:
			if(x > 0): 
				if(tiles[x-1][y].bomb_count == 0 and tiles[x-1][y].uncovered == False):
					uncover_all(x-1,y)
				tiles[x-1][y].uncover()
			if(x > 0 and y > 0): 
				if(tiles[x-1][y-1].bomb_count == 0 and tiles[x-1][y-1].uncovered == False):
					uncover_all(x-1,y-1)
				tiles[x-1][y-1].uncover()
			if(x > 0 and y < board_height-1):
				if(tiles[x-1][y+1].bomb_count == 0 and tiles[x-1][y+1].uncovered == False):
					uncover_all(x-1,y+1)
				tiles[x-1][y+1].uncover() 
			if(y > 0): 
				if(tiles[x][y-1].bomb_count == 0 and tiles[x][y-1].uncovered == False):
					uncover_all(x,y-1)
				tiles[x][y-1].uncover()
			if(y < board_height-1): 
				if(tiles[x][y+1].bomb_count == 0 and tiles[x][y+1].uncovered == False):
					uncover_all(x,y+1)
				tiles[x][y+1].uncover()
			if(x < board_width-1 and y > 0): 
				if(tiles[x+1][y-1].bomb_count == 0 and tiles[x+1][y-1].uncovered == False):
					uncover_all(x+1,y-1)
				tiles[x+1][y-1].uncover()
			if(x < board_width-1 and y < board_height-1): 
				if(tiles[x+1][y+1].bomb_count == 0 and tiles[x+1][y+1].uncovered == False):
					uncover_all(x+1,y+1)
				tiles[x+1][y+1].uncover()
			if(x < board_width-1): 
				if(tiles[x+1][y].bomb_count == 0 and tiles[x+1][y].uncovered == False):
					uncover_all(x+1,y)
				tiles[x+1][y].uncover()

def text_objects(text, font): #to help with displaying text
    textSurface = font.render(text, True, BLACK)
    return textSurface, textSurface.get_rect()

def button(msg, x, y, w, h, ic, ac, action=None): #implement a button
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    
    pygame.draw.rect(gameDisplay, ic, (x, y, w+10, h+10))

    if x+w > mouse[0] > x and y+h > mouse[1] > y:
        pygame.draw.rect(gameDisplay, ac,(x+5, y+5, w, h))
        if click[0] == 1 and action != None:
            action()
    else:
        pygame.draw.rect(gameDisplay, ic, (x, y, w, h))
    smallText = pygame.font.SysFont("comicsansms",20)
    textSurf, textRect = text_objects(msg, smallText)
    textRect.center = ( (x+(w/2)), (y+(h/2)) )
    gameDisplay.blit(textSurf, textRect)

def bubblesort(scores,names):
	#swap elements: slow, but easy to visualize w/names
	#consider using dictionary or hashmap
	for iter_num in range(len(scores)-1,0,-1):
		for idx in range(iter_num):
			if scores[idx] > scores[idx+1]:
				temp_score = scores[idx]
				temp_name = names[idx]
				scores[idx] = scores[idx+1]
				names[idx] = names[idx+1]
				scores[idx+1] = temp_score
				names[idx+1] = temp_name

def init_mines(x,y):
	#randomize mine placement, avoid duplicates
	global tiles, num_bombs, board_height, board_width
	previous_xy = []
	previous_xy.append([x,y])
	for b in range(num_bombs):
		randx = random.randint(0,board_width-1)
		randy = random.randint(0,board_height-1)
		#avoid duplicate mines
		while [randx,randy] in previous_xy:
			randx = random.randint(0,board_width-1)
			randy = random.randint(0,board_height-1)
		previous_xy.append([randx, randy])
		tiles[randx][randy].set_bomb()

	#update bomb_count for each tile
	for c in range(board_height):
		for r in range(board_width):
			count_mines(r,c)

def count_mines(r,c):
	#count number of mines in adjacent tiles
	global tiles, tile_pics
	if not tiles[r][c].is_bomb: #bomb count not needed
		tiles[r][c].bomb_count = 0 #just in case
		if(r > 0): 
			if(tiles[r-1][c].is_bomb):
				tiles[r][c].bomb_count += 1 #left
		if(r > 0 and c > 0): 
			if(tiles[r-1][c-1].is_bomb):
				tiles[r][c].bomb_count += 1 #upleft
		if(r > 0 and c < board_height-1): 
			if(tiles[r-1][c+1].is_bomb):
				tiles[r][c].bomb_count += 1 #downleft
		if(c > 0): 
			if(tiles[r][c-1].is_bomb):
				tiles[r][c].bomb_count += 1 #up
		if(c < board_height-1): 
			if(tiles[r][c+1].is_bomb):
				tiles[r][c].bomb_count += 1 #down
		if(r < board_width-1 and c > 0): 
			if(tiles[r+1][c-1].is_bomb):
				tiles[r][c].bomb_count += 1 #upright
		if(r < board_width-1 and c < board_height-1): 
			if(tiles[r+1][c+1].is_bomb):
				tiles[r][c].bomb_count += 1 #downright
		if(r < board_width-1): 
			if(tiles[r+1][c].is_bomb):
				tiles[r][c].bomb_count += 1 #right
		if tiles[r][c].bomb_count < 9:
			tiles[r][c].image_uncovered = tile_pics[tiles[r][c].bomb_count] #update


def display_settings():
	#to be implemented later: change game mode, etc.
	gameDisplay.fill(WHITE)

def display_scores():
	#clear screen (fill WHITE), display scores, when button pressed,
	#undo clear screen, remove scoreboard text
	gameDisplay.fill(WHITE)
	f = open('assets/scores/scores_' + game_mode + '.txt')
	scores_font = pygame.font.SysFont('comicsansms',12)
	TitleSurf, TitleRect = text_objects(f.read(), scores_font)
	TitleRect.center = (display_width/2, 50)
	gameDisplay.blit(TitleSurf, TitleRect)

def zoom_in():
	global TILE_SIZE, restart
	gameDisplay.fill(WHITE)
	TILE_SIZE += 5
	restart = True
	reload_images()
	game_restart()

def zoom_out():
	global TILE_SIZE, restart
	gameDisplay.fill(WHITE)
	if TILE_SIZE > 5:
		TILE_SIZE -= 5
	restart = True
	reload_images()
	game_restart()

def reload_images():
	global TILE_SIZE, tile_normal, tile_flagged, tile_pics, board_x, board_y, tiles
	global bomb, bomb_red, bomb_x

	board_x, board_y = display_width/2- board_width/2*TILE_SIZE, display_height/2- board_height/2*TILE_SIZE
	#load/scale zoomed images
	tile_normal = pygame.image.load('assets/tiles/tile_normal.png')
	tile_normal = pygame.transform.scale(tile_normal, (TILE_SIZE,TILE_SIZE))
	tile_flagged = pygame.image.load('assets/tiles/tile_flagged.png')
	tile_flagged = pygame.transform.scale(tile_flagged, (TILE_SIZE,TILE_SIZE))
	for row in tiles:
		for tile in row:
			tile.set_image(tile_normal)
	tile_pics = []
	for idx in range(8):
		tile_pics.append(pygame.transform.scale(
			pygame.image.load('assets/tiles/' + str(idx) + '.png'),(TILE_SIZE,TILE_SIZE)))
		tile_pics[idx] = pygame.transform.scale(tile_pics[idx],(TILE_SIZE,TILE_SIZE))
	bomb_x = pygame.image.load('assets/mines/bomb_x.png')
	bomb_x = pygame.transform.scale(bomb_x, (TILE_SIZE,TILE_SIZE))
	bomb = pygame.image.load('assets/mines/bomb.png')
	bomb = pygame.transform.scale(bomb, (TILE_SIZE,TILE_SIZE))
	bomb_red = pygame.image.load('assets/mines/bomb_red.png')
	bomb_red = pygame.transform.scale(bomb_red, (TILE_SIZE,TILE_SIZE))

def save_scores():
	#write new high score in correct location
	global won,new_score,scores
	if won and new_score:
		new_score = False #prevent duplicate
		scores = []
		names = []
		header = []
		f = open('assets/scores/scores_' + game_mode + '.txt', 'r+')

		#separate header and scores
		line_count = 0
		for line in f:
			if line_count != 0 and line_count != 1:
				line = "".join(line.split()) #remove WHITE space ('\n')
				if line != '':
					names.append(re.sub(r'[0-9]+','',line)) #remove all digits
					scores.append(int(re.sub(r'[^0-9]','',line))) #remove everything but digits
			else:	
				header.append(line)
			line_count += 1

		scores.append(timer)
		names.append(score_name)
		#scores.sort()
		bubblesort(scores,names)
		
		#write entire file again, starting at position 0
		f.seek(0)
		for line_idx in range(len(header)):
			f.write(header[line_idx])
		for line_idx in range(len(scores)):
			#last element -> new line needed
			f.write("\n" + names[line_idx] + "\t" + str(scores[line_idx]))

def game_over():
	global display_width, display_height
	gameDisplay.fill(WHITE)
	if lost:
		game_over_font = pygame.font.SysFont('comicsansms',40)
		GameOverSurf, GameOverRect = text_objects("You lost. Click face or press R to restart.", game_over_font)
		GameOverRect.center = (display_width/2, display_height-200)
		gameDisplay.blit(GameOverSurf, GameOverRect)

def game_restart():
	#restart for new game
	global tiles,restart,won,enter_finished,lost,face_state,face,timer,num_clicks,num_flags,num_bombs
	global game_mode,score_name,display_width,display_height,new_score
	lost, won, enter_finished = False, False, False
	new_score = True
	face_state = 'normal'
	face = pygame.image.load('assets/faces/face_' + face_state + '.png')
	timer,num_clicks = 0,0
	num_flags = num_bombs
	score_name = ""
	if restart:
		for row in tiles:
			for tile in row:
				tile.uncovered = False #set all tiles to covered state
				tile.is_bomb = False
				tile.flagged = False
				tile.bomb_count = 0
				tile.set_image(tile_normal)
		#clear won/lost text
		game_restart_font = pygame.font.SysFont('comicsansms',40)
		gameDisplay.fill(WHITE)
		GameRestSurf, GameRestRect = text_objects("Game Restarted.", game_restart_font)
		GameRestRect.center = (display_width/2, display_height-200)
		gameDisplay.blit(GameRestSurf,GameRestRect)
	game_loop(game_mode,AI)

def game_pause():
	global paused,timer,save_time
	while paused:
		save_time = timer
		gameDisplay.fill(WHITE) #clear screen, tell user to unpause
		pauseText = pygame.font.SysFont("comicsansms",100)
		pauseSurf, pauseRect = text_objects("Paused", pauseText)
		pauseRect.center = (display_width/2,display_height/2)
		gameDisplay.blit(pauseSurf,pauseRect)
		timer = timer
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()
		button("Continue", display_width/2-210, display_height/2+200, 200, 50, GRAY, LIGHT_GRAY, game_unpause)
		button("Quit", display_width/2+10, display_height/2+200, 200, 50, GRAY, LIGHT_GRAY, game_quit)
		pygame.display.update()
		clock.tick(30) 

def game_unpause():
	global paused, game_mode
	paused = False
	timer = save_time
	game_loop(game_mode,AI)

def game_quit():
	pygame.display.quit()
	pygame.quit()
	sys.exit()

def rainbow_bg():
	#rainbow background
	global roygbiv,won,lost,paused
	if not won and not lost and not paused:
		roygbiv += 0.002
		r = int(127*math.sin(math.pi * roygbiv)+127)
		g = int(127*math.sin(math.pi * (roygbiv + 1/3))+127)
		b = int(127*math.sin(math.pi * (roygbiv + 2/3))+127)
		gameDisplay.fill(pygame.Color(r,g,b))

def game_loop(game_mode,ai):
	#play game in loop
	global tiles,lost,won,paused,restart,start_ms,num_clicks,num_flags,num_bombs,face_state,enter_finished,timer;
	global display_height,display_width,new_score,score_name;
	
	#default tiles
	if restart:
		restart = False
		for row in tiles:
			for tile in row:
				tile.set_image(tile_normal)
				tile.is_bomb = False
				tile.uncovered = False

	while not paused:
		
		events = pygame.event.get()
		for event in events:
			rainbow_bg()
			#set up buttons,text,variables before gameplay
			if not lost and not won:
				face_state = 'normal'
				face = pygame.image.load('assets/faces/face_' + face_state + '.png')
				button("Settings", display_width/2-430, 70, 200, 50, GRAY, LIGHT_GRAY, display_settings)
				button("Scores", display_width/2-210, 70, 200, 50, GRAY, LIGHT_GRAY, display_scores)
				button("Zoom In", display_width/2+10, 70, 200, 50, GRAY, LIGHT_GRAY, zoom_in)
				button("Zoom Out", display_width/2+230, 70, 200, 50, GRAY, LIGHT_GRAY, zoom_out)
				button("Quit", display_width/2-100, display_height-100, 200, 50, GRAY, LIGHT_GRAY, game_quit)
			
			title_font = pygame.font.Font(os.getcwd() + '/assets/mines.ttf',40)
			TitleSurf, TitleRect = text_objects("Minesweeper", title_font)
			TitleRect.center = (display_width/2, 30)
			gameDisplay.blit(TitleSurf, TitleRect)

			if event.type == pygame.MOUSEBUTTONDOWN:
				click_x, click_y = event.pos
				#if click in tile array, start timer
				if click_x > board_x and click_x < board_x + TILE_SIZE * board_width:
					if (click_y > board_y and click_y < board_y + TILE_SIZE * board_height
						and not won and not lost):
						face_state = 'surprised'
						face = pygame.image.load('assets/faces/face_' + face_state + '.png')
						num_clicks += 1
						idx_x = int((click_x - board_x) // TILE_SIZE) #0->board_width-1
						idx_y = int((click_y - board_y) // TILE_SIZE) #0->board_height-1
						if(num_clicks == 1):
							start_ms = pygame.time.get_ticks() #start timer on 1st click
							#initialize after click -> first click is never a mine
							init_mines(idx_x,idx_y)
						#left click = uncover
						if event.button == LEFT:
							tiles[idx_x][idx_y].flagged = False
							if(not tiles[idx_x][idx_y].is_bomb):
								#tiles[idx_x][idx_y].uncover()
								uncover_all(idx_x,idx_y)
							else:
								tiles[idx_x][idx_y].image_uncovered = bomb_red
								lost = True
								face_state = 'unhappy'
								for row in tiles:
									for tile in row:
										if tile.flagged and not tile.is_bomb:
											tile.set_image(bomb_x)
										if tile.is_bomb:
											tile.uncover()
						#right click = flag
						elif event.button == RIGHT:
							flag_yn = tiles[idx_x][idx_y].flag() #flag, uncover
							if flag_yn and num_flags > 0:
								num_flags -= 1
							elif num_flags < num_bombs:
								num_flags += 1

						uncover_count = 0 #if all tiles (not bombs) uncovered, won = True
						for row in tiles:
							for tile in row:
								if tile.uncovered:
									uncover_count += 1
						if uncover_count == board_height*board_width-num_bombs:
							won = True
							new_score = True
							face_state = 'happy'
						if lost:
							game_over()
				#click face to restart game
				if (click_x > board_x+TILE_SIZE*board_width/2-num_size[1]/2 
					and click_x < board_x+TILE_SIZE*board_width/2-num_size[1]/2+num_size[1]
					and click_y >board_y-1.5*num_size[1]
					and click_y < board_y-1.5*num_size[1]+num_size[1]):
					restart = True
					game_restart()

			if event.type == pygame.KEYDOWN:
				if not won:
					if event.key == pygame.K_p: #pause
						paused = True
						game_pause()
						print('paused')
						game_pause()
					if event.key == pygame.K_q: #quit
						game_quit()
					if event.key == pygame.K_r: #restart
						restart = True
						game_restart()
					if event.key == pygame.K_i: #zoom in
						zoom_in()
					if event.key == pygame.K_o: #zoom out
						zoom_out()
					if event.key == pygame.K_a: #uncover
						pyautogui.click(button='left')
					if event.key == pygame.K_s: #flag
						pyautogui.click(button='right')

			#display tile images
			if not won:
				tile_x, tile_y = board_x, board_y
				for h in range(board_height):
					tile_x = board_x
					for w in range(board_width):
						gameDisplay.blit(tiles[w][h].image, (tile_x, tile_y))
						tile_x += TILE_SIZE
					tile_y += TILE_SIZE

		#enter name for score
		if won and not enter_finished:
			gameDisplay.fill(WHITE)
			enterText = pygame.font.SysFont("comicsansms",40)
			enterSurf, enterRect = text_objects("You Won with " + str(timer) + " Seconds!", enterText)
			enterRect.center = (display_width/2,display_height/2-50)
			gameDisplay.blit(enterSurf,enterRect)
			enterSurf, enterRect = text_objects("Enter Name:", enterText)
			enterRect.center = (display_width/2,display_height/2)
			gameDisplay.blit(enterSurf,enterRect)
		if textinput.update(events):
			score_name = textinput.get_text() #save on return
			enter_finished = True #consider saving score here
			save_scores()
			won = False
		if won:
			gameDisplay.blit(textinput.get_surface(), (display_width/2-110, display_height/2+25))


		else:
			if start_ms != 0:
				if not lost and not won and not paused:
					timer = (pygame.time.get_ticks() - start_ms)//1000 #update timer
				else:
					pass
				#load images, zeros added to avoid index out of bounds-i.e. str(timer) 1 char long
				str_timer = str(timer)
				if num_flags >= 0:
					str_flags = str(num_flags)
				if timer < 10:
					str_timer = '00' + str_timer
				elif timer < 100:
					str_timer = '0' + str_timer
				if num_flags < 100:
					str_flags = '0' + str_flags
				elif num_flags < 10:
					str_flags = '00' + str_flags
					
				#find which image to display where (7-seg displays/faces)
				bombs_1 = pygame.image.load('assets/numbers/' + str_timer[len(str_timer)-1] + '.png')
				bombs_10 = pygame.image.load('assets/numbers/' + str_timer[len(str_timer)-2] + '.png')
				bombs_100 = pygame.image.load('assets/numbers/' + str_timer[len(str_timer)-3] + '.png')
				flags_1 = pygame.image.load('assets/numbers/' + str_flags[len(str_flags)-1] + '.png')
				flags_10 = pygame.image.load('assets/numbers/' + str_flags[len(str_flags)-2] + '.png')
				#flags_100 always "0" since number of bombs is always less than 100
				if not won:
					gameDisplay.blit(bombs_1,
						(board_x+TILE_SIZE*board_width-num_size[0], board_y-1.5*num_size[1]))
					gameDisplay.blit(bombs_10,
						(board_x+TILE_SIZE*board_width-num_size[0]-39, board_y-1.5*num_size[1]))
					gameDisplay.blit(bombs_100,
						(board_x+TILE_SIZE*board_width-num_size[0]-2*39, board_y-1.5*num_size[1]))
					gameDisplay.blit(flags_100,(board_x, board_y-1.5*num_size[1]))
					gameDisplay.blit(flags_10,(board_x+num_size[0], board_y-1.5*num_size[1]))
					gameDisplay.blit(flags_1,(board_x+2*num_size[0], board_y-1.5*num_size[1]))

				face = pygame.image.load('assets/faces/face_' + face_state + '.png')
				face = pygame.transform.scale(face, (num_size[1],num_size[1]))
				if not won:
					gameDisplay.blit(face,(board_x+TILE_SIZE*board_width/2-num_size[1]/2,board_y-1.5*num_size[1]))

		pygame.display.update()
		clock.tick(30)

game_loop(game_mode=game_mode, ai=False)