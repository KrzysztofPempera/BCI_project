import math
import random
import multiprocessing as mp
import pygame
import pandas as pd
from pyOpenBCI import OpenBCIGanglion

import blink as blk
import filterlib as flt

from pygame import mixer

global mac_adress, SYMULACJA_SYGNALU

#######################
SYMULACJA_SYGNALU = True
#######################

mac_adress = 'd2:b4:11:81:48:ad'

def blinks_detector(quit_program, blink_det, blinks_num, blink):
    def detect_blinks(sample):
        if SYMULACJA_SYGNALU:
            smp_flted = sample
        else:
            smp = sample.channels_data[0]
            smp_flted = frt.filterIIR(smp, 0)

        brt.blink_detect(smp_flted, -38000)
        if brt.new_blink:
            if brt.blinks_num == 1:
                connected.set()
                print('CONNECTED. Speller starts detecting blinks.')
            else:
                blink_det.put(brt.blinks_num)
                blinks_num.value = brt.blinks_num
                blink.value = 1

        if quit_program.is_set():
            if not SYMULACJA_SYGNALU:
                print('Disconnect signal sent...')
                board.stop_stream()

    if __name__ == '__main__':
        clock = pygame.time.Clock()

        frt = flt.FltRealTime()
        brt = blk.BlinkRealTime()

        if SYMULACJA_SYGNALU:
            df = pd.read_csv('dane_do_symulacji/data.csv')
            for sample in df['signal']:
                if quit_program.is_set():
                    break
                detect_blinks(sample)
                clock.tick(200)
            print('KONIEC SYGNALU')
            quit_program.set()
        else:
             board = OpenBCIGanglion(mac=mac_adress)
             board.start_stream(detect_blinks)

blink_det = mp.Queue()
blink = mp.Value('i', 0)
blinks_num = mp.Value('i', 0)
connected = mp.Event()
quit_program = mp.Event()

proc_blink_det = mp.Process(
    name='proc_',
    target=blinks_detector,
    args=(quit_program, blink_det, blinks_num, blink,)
    )

# rozpoczee podprocesu
proc_blink_det.start()
print('subprocess started')

########################
###       GAME       ###
########################

# Intialize the pygame
pygame.init()

# create the screen
screen = pygame.display.set_mode((800, 600))

# Background
background = pygame.image.load('background.png')

# Sound
mixer.music.load("background.wav")
mixer.music.play(-1)

# Caption and Icon
pygame.display.set_caption("Space Invader")
icon = pygame.image.load('ufo.png')
pygame.display.set_icon(icon)

# Player
playerImg = pygame.image.load('player.png')
playerX = 420
playerY = 520
playerX_change = 2

# Enemy
enemyImg = []
enemyX = []
enemyY = []
enemyX_change = []
enemyY_change = []
num_of_enemies = 10

for i in range(num_of_enemies):
    enemyImg.append(pygame.image.load('enemy.png'))
    enemyX.append(random.randint(0, 736))
    enemyY.append(random.randint(50, 150))
    enemyX_change.append(3)
    enemyY_change.append(20)

# Bullet

# Ready - You can't see the bullet on the screen
# Fire - The bullet is currently moving

bulletImg = pygame.image.load('bullet.png')
bulletX = 0
bulletY = 480
bulletX_change = 0
bulletY_change = 10
bullet_state = "ready"

# Score

score_value = 0
font = pygame.font.Font('freesansbold.ttf', 32)

textX = 10
testY = 10

# Game Over
over_font = pygame.font.Font('freesansbold.ttf', 64)


def show_score(x, y):
    score = font.render("Score : " + str(score_value), True, (255, 255, 255))
    screen.blit(score, (x, y))


def game_over_text():
    over_text = over_font.render("GAME OVER", True, (255, 255, 255))
    screen.blit(over_text, (200, 250))


def player(x, y):
    screen.blit(playerImg, (x, y))


def enemy(x, y, i):
    screen.blit(enemyImg[i], (x, y))


def fire_bullet(x, y):
    global bullet_state
    bullet_state = "fire"
    screen.blit(bulletImg, (x + 16, y + 10))


def isCollision(enemyX, enemyY, bulletX, bulletY):
    distance = math.sqrt(math.pow(enemyX - bulletX, 2) + (math.pow(enemyY - bulletY, 2)))
    if distance < 27:
        return True
    else:
        return False


# Game Loop
running = True
while running:

    # RGB = Red, Green, Blue
    screen.fill((0, 0, 0))
    # Background Image
    screen.blit(background, (0, 0))
    # Player movement

    playerX += playerX_change
    if playerX <= 0:
        playerX_change = 2
    elif playerX >= 736:
        playerX_change = -2


    for event in pygame.event.get():
        
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                quit_program.set()
                event.type = pygame.QUIT

        # if event.type == pygame.KEYDOWN:

        #     if event.key == pygame.K_SPACE:
        #         if bullet_state is "ready":
        #             bulletSound = mixer.Sound("Space-Invaders-Pygame/laser.wav")
        #             bulletSound.play()
        #             # Get the current x cordinate of the spaceship
        #             bulletX = playerX
        #             fire_bullet(bulletX, bulletY)
    
    if blink.value == 1:
        print('BLINK!')
        blink.value = 0
        if bullet_state is "ready":
            bulletSound = mixer.Sound("laser.wav")
            bulletSound.play()
            # Get the current x cordinate of the spaceship
            bulletX = playerX
            fire_bullet(bulletX, bulletY)

    # Enemy Movement
    for i in range(num_of_enemies):

        # Game Over
        if enemyY[i] > 440:
            for j in range(num_of_enemies):
                enemyY[j] = 2000
            game_over_text()
            break

        enemyX[i] += enemyX_change[i]
        if enemyX[i] <= 0:
            enemyX_change[i] = 3
            enemyY[i] += enemyY_change[i]
        elif enemyX[i] >= 736:
            enemyX_change[i] = -3
            enemyY[i] += enemyY_change[i]

        # Collision
        collision = isCollision(enemyX[i], enemyY[i], bulletX, bulletY)
        if collision:
            explosionSound = mixer.Sound("explosion.wav")
            explosionSound.play()
            bulletY = 480
            bullet_state = "ready"
            score_value += 1
            enemyX[i] = random.randint(0, 736)
            enemyY[i] = random.randint(50, 150)

        enemy(enemyX[i], enemyY[i], i)

    # Bullet Movement
    if bulletY <= 0:
        bulletY = 480
        bullet_state = "ready"

    if bullet_state is "fire":
        fire_bullet(bulletX, bulletY)
        bulletY -= bulletY_change

    player(playerX, playerY)
    show_score(textX, testY)
    pygame.display.update()

# Zakonzenie podproceso
proc_blink_det.join()

