import pygame, math, random

pygame.init()
pygame.mixer.init()

# =====================
# WINDOW
# =====================
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultimate Zombie Shooter")
clock = pygame.time.Clock()

# =====================
# AUDIO
# =====================
sounds = {
    "gunshot": pygame.mixer.Sound("gunshot.wav"),
    "grenade": pygame.mixer.Sound("grenade.wav"),
    "explosion": pygame.mixer.Sound("explosion.wav"),
    "zombie_hit": pygame.mixer.Sound("zombie_hit.wav"),
    "player_dead": pygame.mixer.Sound("player_dead.wav")
}
pygame.mixer.music.load("bg_music.mp3")
pygame.mixer.music.set_volume(1)
pygame.mixer.music.play(-1)

# =====================
# WORLD
# =====================
MAP_W, MAP_H = 2500, 2500
camera = {"x":0, "y":0}

# =====================
# PLAYER
# =====================
player = {
    "x": MAP_W//2,
    "y": MAP_H//2,
    "speed":5,
    "health":100,
    "weapon":"pistol",
    "money":0
}
crosshair = {"x": WIDTH//2, "y": HEIGHT//2}
smooth_speed = 0.2

# =====================
# WEAPONS & SHOP
# =====================
weapons = {
    "pistol":{"damage":1,"spread":3,"rate":300,"cost":0},
    "shotgun":{"damage":1,"spread":15,"rate":600,"bullets":5,"cost":15},
    "smg":{"damage":1,"spread":8,"rate":80,"cost":100},
    "sniper":{"damage":5,"spread":1,"rate":900,"cost":200},
    "grenade":{"damage":3,"spread":0,"rate":600,"cost":50}  # fixed grenade damage
}
last_shot = 0
unlocked_weapons = ["pistol"]

# =====================
# BULLETS & GRENADES
# =====================
bullets = []
grenades = []
explosions = []

# =====================
# ZOMBIES & WAVES
# =====================
zombies = []
wave = 1
shop_open = False

def spawn_wave():
    global zombies
    zombies.clear()
    for _ in range(wave*5):
        zombies.append({
            "x": random.randint(50, MAP_W-50),
            "y": random.randint(50, MAP_H-50),
            "speed": random.choice([1,2]),
            "health": random.choice([2,3])
        })
    if wave % 5 == 0:
        boss_health = 20 + (wave-1)*5
        zombies.append({"x":MAP_W//2,"y":100,"speed":1,"health":boss_health,"boss":True})

spawn_wave()

# =====================
# SHOOTING
# =====================
def shoot():
    global last_shot
    now = pygame.time.get_ticks()
    w = weapons[player["weapon"]]
    rate = w["rate"]
    bullets_per_shot = w.get("bullets",1)
    if now - last_shot < rate: return
    mx,my = crosshair["x"]+camera["x"], crosshair["y"]+camera["y"]
    dx,dy = mx-player["x"], my-player["y"]
    dist = math.hypot(dx,dy)
    if dist == 0: return
    for _ in range(bullets_per_shot):
        angle = math.atan2(dy,dx)+math.radians(random.uniform(-w["spread"],w["spread"]))
        bullets.append({"x":player["x"],"y":player["y"],"dx":math.cos(angle)*12,"dy":math.sin(angle)*12,"damage":w["damage"]})
    last_shot = now
    sounds["gunshot"].play()

# =====================
# THROW GRENADE (only if unlocked)
# =====================
def throw_grenade():
    if "grenade" not in unlocked_weapons:
        return
    mx,my = crosshair["x"]+camera["x"], crosshair["y"]+camera["y"]
    grenades.append({"x":player["x"],"y":player["y"],"target":(mx,my),"timer":60})
    sounds["grenade"].play()

# =====================
# PLAYER MOVEMENT
# =====================
def move_player(keys):
    if keys[pygame.K_w]: player["y"] -= player["speed"]
    if keys[pygame.K_s]: player["y"] += player["speed"]
    if keys[pygame.K_a]: player["x"] -= player["speed"]
    if keys[pygame.K_d]: player["x"] += player["speed"]
    player["x"] = max(0,min(player["x"],MAP_W))
    player["y"] = max(0,min(player["y"],MAP_H))

# =====================
# ZOMBIES
# =====================
def move_zombies():
    for z in zombies:
        dx,dy = player["x"]-z["x"], player["y"]-z["y"]
        dist = math.hypot(dx,dy)
        if dist != 0:
            z["x"] += dx/dist * z["speed"]
            z["y"] += dy/dist * z["speed"]
        if dist < 25:
            player["health"] -= 0.1

# =====================
# BULLETS & MONEY
# =====================
def update_bullets():
    for b in bullets[:]:
        b["x"] += b["dx"]
        b["y"] += b["dy"]
        if b["x"]<0 or b["y"]<0 or b["x"]>MAP_W or b["y"]>MAP_H:
            bullets.remove(b)
            continue
        for z in zombies[:]:
            if math.hypot(b["x"]-z["x"],b["y"]-z["y"])<18:
                z["health"] -= b["damage"]
                sounds["zombie_hit"].play()
                if b in bullets: bullets.remove(b)
                if z["health"] <= 0:
                    zombies.remove(z)
                    if "boss" in z:
                        player["money"] += 10
                    else:
                        player["money"] += 1
                break

# =====================
# GRENADES & MONEY (FIXED DAMAGE)
# =====================
def update_grenades():
    GRENADE_DAMAGE = 3  # specific damage for all zombies/boss
    for g in grenades[:]:
        g["timer"] -= 1
        if g["timer"] <= 0:
            explosions.append({"x":g["x"],"y":g["y"],"radius":100})
            grenades.remove(g)
            sounds["explosion"].play()
    for e in explosions[:]:
        for z in zombies[:]:
            if math.hypot(e["x"]-z["x"],e["y"]-z["y"]) < e["radius"]:
                z["health"] -= GRENADE_DAMAGE
                if z["health"] <= 0:
                    zombies.remove(z)
                    if "boss" in z:
                        player["money"] += 10
                    else:
                        player["money"] += 1
        e["radius"] -= 3
        if e["radius"] <= 0:
            explosions.remove(e)

# =====================
# CAMERA
# =====================
def update_camera():
    camera["x"] = player["x"]-WIDTH//2
    camera["y"] = player["y"]-HEIGHT//2
    camera["x"] = max(0,min(camera["x"],MAP_W-WIDTH))
    camera["y"] = max(0,min(camera["y"],MAP_H-HEIGHT))

# =====================
# WAVES
# =====================
def check_wave():
    global wave
    if len(zombies) == 0:
        wave += 1
        spawn_wave()

# =====================
# SHOP
# =====================
shop_buttons = []
def create_shop_buttons():
    shop_buttons.clear()
    font = pygame.font.SysFont(None,28)
    start_y = 150
    for w in weapons:
        if w=="pistol": continue
        rect = pygame.Rect(450,start_y,250,60)
        shop_buttons.append({"weapon":w,"rect":rect})
        start_y += 90
create_shop_buttons()

def draw_shop():
    screen.fill((50,50,50))
    font = pygame.font.SysFont(None,36)
    screen.blit(font.render("WEAPON SHOP",True,(255,255,0)),(500,50))
    for btn in shop_buttons:
        w = btn["weapon"]
        rect = btn["rect"]
        color = (0,200,0) if w in unlocked_weapons else (200,0,0)
        pygame.draw.rect(screen,color,rect)
        screen.blit(font.render(f"{w} - ${weapons[w]['cost']}",True,(255,255,255)),(rect.x+10,rect.y+10))
    screen.blit(font.render(f"Money: ${player['money']}",True,(255,255,255)),(10,10))
    screen.blit(font.render("Press P to exit shop",True,(255,255,255)),(10,50))

def handle_shop_click(pos):
    for btn in shop_buttons:
        if btn["rect"].collidepoint(pos):
            w = btn["weapon"]
            if w not in unlocked_weapons and player["money"] >= weapons[w]["cost"]:
                unlocked_weapons.append(w)
                player["money"] -= weapons[w]["cost"]
                print(f"{w} unlocked!")

# =====================
# DRAW GAME
# =====================
def draw_game():
    screen.fill((30,30,30))
    for x in range(0,MAP_W,100):
        pygame.draw.line(screen,(50,50,50),(x-camera["x"],0-camera["y"]),(x-camera["x"],MAP_H-camera["y"]))
    for y in range(0,MAP_H,100):
        pygame.draw.line(screen,(50,50,50),(0-camera["x"],y-camera["y"]),(MAP_W-camera["x"],y-camera["y"]))
    pygame.draw.circle(screen,(0,255,0),(int(player["x"]-camera["x"]),int(player["y"]-camera["y"])),15)
    for z in zombies:
        color = (255,0,0)
        size = 12 if "boss" not in z else 40
        if "boss" in z: color=(255,0,255)
        pygame.draw.circle(screen,color,(int(z["x"]-camera["x"]),int(z["y"]-camera["y"])),size)
    for b in bullets:
        pygame.draw.circle(screen,(255,255,255),(int(b["x"]-camera["x"]),int(b["y"]-camera["y"])),3)
    for g in grenades:
        pygame.draw.circle(screen,(255,255,0),(int(g["x"]-camera["x"]),int(g["y"]-camera["y"])),8)
    for e in explosions:
        pygame.draw.circle(screen,(255,150,0),(int(e["x"]-camera["x"]),int(e["y"]-camera["y"])),int(e["radius"]),3)
    pygame.draw.circle(screen,(255,255,255),(int(crosshair["x"]),int(crosshair["y"])),10,2)
    
    font = pygame.font.SysFont(None,28)
    pygame.draw.rect(screen,(255,0,0),(10,10,200,20))
    pygame.draw.rect(screen,(0,255,0),(10,10,2*player["health"],20))
    screen.blit(font.render(f"Wave: {wave}",True,(255,255,255)),(10,40))
    screen.blit(font.render(f"Weapon: {player['weapon']}",True,(255,255,255)),(10,70))
    screen.blit(font.render(f"Money: ${player['money']}",True,(255,255,255)),(10,100))
    screen.blit(font.render("Press P to open shop",True,(255,255,0)),(10,130))

    # GRENADE HUD
    if "grenade" in unlocked_weapons:
        screen.blit(font.render("Grenade: UNLOCKED (Press G)",True,(255,255,0)),(10,160))
    else:
        screen.blit(font.render("Grenade: LOCKED",True,(200,0,0)),(10,160))

# =====================
# GAME LOOP
# =====================
running = True
while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running=False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if shop_open:
                handle_shop_click(event.pos)
            else:
                shoot()
        if event.type == pygame.KEYDOWN:
            if event.key==pygame.K_g and not shop_open:
                throw_grenade()
            if event.key==pygame.K_p:
                shop_open = not shop_open

    if not shop_open:
        mx,my = pygame.mouse.get_pos()
        crosshair["x"] += (mx-crosshair["x"])*smooth_speed
        crosshair["y"] += (my-crosshair["y"])*smooth_speed

        keys = pygame.key.get_pressed()
        move_player(keys)
        move_zombies()
        update_bullets()
        update_grenades()
        update_camera()
        check_wave()
        if keys[pygame.K_1]: player["weapon"]="pistol"
        if keys[pygame.K_2] and "shotgun" in unlocked_weapons: player["weapon"]="shotgun"
        if keys[pygame.K_3] and "smg" in unlocked_weapons: player["weapon"]="smg"
        if keys[pygame.K_4] and "sniper" in unlocked_weapons: player["weapon"]="sniper"
        draw_game()
    else:
        draw_shop()

    if player["health"] <= 0:
        sounds["player_dead"].play()
        print("GAME OVER")
        running=False

    pygame.display.flip()

pygame.quit()