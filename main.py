import math
import random
from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

# Recommended Android target resolution. The game adapts to the device size.
Window.clearcolor = (0.05, 0.05, 0.05, 1)

class ZombieSurvivalGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.MAP_W, self.MAP_H = 2500, 2500
        self.camera = {"x": 0, "y": 0}

        self.player = {
            "x": self.MAP_W // 2,
            "y": self.MAP_H // 2,
            "speed": 5,
            "health": 100,
            "weapon": "pistol",
            "money": 0,
        }

        self.crosshair = {"x": Window.width / 2, "y": Window.height / 2}
        self.smooth_speed = 0.2

        self.weapons = {
            "pistol": {"damage": 1, "spread": 3, "rate": 0.3, "cost": 0},
            "shotgun": {"damage": 1, "spread": 15, "rate": 0.6, "bullets": 5, "cost": 15},
            "smg": {"damage": 1, "spread": 8, "rate": 0.08, "cost": 100},
            "sniper": {"damage": 5, "spread": 1, "rate": 0.9, "cost": 200},
            "grenade": {"damage": 3, "spread": 0, "rate": 0.6, "cost": 50},
        }
        self.last_shot = 0.0
        self.unlocked_weapons = ["pistol"]

        self.bullets = []
        self.grenades = []
        self.explosions = []
        self.zombies = []
        self.wave = 1
        self.shop_open = False
        self.move_dir = {"up": False, "down": False, "left": False, "right": False}

        self.sounds = {}
        self.load_sounds()
        self.spawn_wave()

        self.ui_layout = FloatLayout(size=self.size, pos=self.pos)
        self.add_widget(self.ui_layout)
        self.create_ui()

        Clock.schedule_interval(self.update, 1 / 60.0)
        self.bind(size=self.on_size, pos=self.on_size)

    def on_size(self, *args):
        self.ui_layout.size = self.size
        self.ui_layout.pos = self.pos

    def load_sounds(self):
        for name, filename in [
            ("gunshot", "gunshot.wav"),
            ("grenade", "grenade.wav"),
            ("explosion", "explosion.wav"),
            ("zombie_hit", "zombie_hit.wav"),
            ("player_dead", "player_dead.wav"),
        ]:
            sound = SoundLoader.load(filename)
            if sound:
                self.sounds[name] = sound

        bg = SoundLoader.load("bg_music.mp3")
        if bg:
            bg.loop = True
            bg.volume = 1.0
            bg.play()

    def play_sound(self, name):
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def spawn_wave(self):
        self.zombies.clear()
        for _ in range(self.wave * 5):
            self.zombies.append({
                "x": random.randint(50, self.MAP_W - 50),
                "y": random.randint(50, self.MAP_H - 50),
                "speed": random.choice([1, 2]),
                "health": random.choice([2, 3]),
            })
        if self.wave % 5 == 0:
            boss_health = 20 + (self.wave - 1) * 5
            self.zombies.append({"x": self.MAP_W // 2, "y": 100, "speed": 1, "health": boss_health, "boss": True})

    def create_ui(self):
        self.health_label = Label(text="Health: 100", size_hint=(0.2, 0.06), pos_hint={"x": 0.02, "y": 0.9})
        self.wave_label = Label(text="Wave: 1", size_hint=(0.2, 0.06), pos_hint={"x": 0.35, "y": 0.9})
        self.money_label = Label(text="Money: $0", size_hint=(0.3, 0.06), pos_hint={"x": 0.68, "y": 0.9})
        self.status_label = Label(text="Tap to aim and fire", size_hint=(0.6, 0.06), pos_hint={"x": 0.2, "y": 0.82})

        self.ui_layout.add_widget(self.health_label)
        self.ui_layout.add_widget(self.wave_label)
        self.ui_layout.add_widget(self.money_label)
        self.ui_layout.add_widget(self.status_label)

        self.btn_up = Button(text="↑", size_hint=(0.14, 0.14), pos_hint={"x": 0.02, "y": 0.02})
        self.btn_down = Button(text="↓", size_hint=(0.14, 0.14), pos_hint={"x": 0.02, "y": 0.18})
        self.btn_left = Button(text="←", size_hint=(0.14, 0.14), pos_hint={"x": 0.17, "y": 0.1})
        self.btn_right = Button(text="→", size_hint=(0.14, 0.14), pos_hint={"x": 0.32, "y": 0.1})
        self.btn_shoot = Button(text="FIRE", size_hint=(0.22, 0.16), pos_hint={"x": 0.68, "y": 0.02})
        self.btn_grenade = Button(text="GRENADE", size_hint=(0.22, 0.12), pos_hint={"x": 0.68, "y": 0.21})
        self.btn_shop = Button(text="SHOP", size_hint=(0.22, 0.12), pos_hint={"x": 0.68, "y": 0.36})

        self.btn_up.bind(on_press=lambda _: self.set_move("up", True), on_release=lambda _: self.set_move("up", False))
        self.btn_down.bind(on_press=lambda _: self.set_move("down", True), on_release=lambda _: self.set_move("down", False))
        self.btn_left.bind(on_press=lambda _: self.set_move("left", True), on_release=lambda _: self.set_move("left", False))
        self.btn_right.bind(on_press=lambda _: self.set_move("right", True), on_release=lambda _: self.set_move("right", False))
        self.btn_shoot.bind(on_press=lambda _: self.shoot())
        self.btn_grenade.bind(on_press=lambda _: self.throw_grenade())
        self.btn_shop.bind(on_press=lambda _: self.toggle_shop())

        self.ui_layout.add_widget(self.btn_up)
        self.ui_layout.add_widget(self.btn_down)
        self.ui_layout.add_widget(self.btn_left)
        self.ui_layout.add_widget(self.btn_right)
        self.ui_layout.add_widget(self.btn_shoot)
        self.ui_layout.add_widget(self.btn_grenade)
        self.ui_layout.add_widget(self.btn_shop)

        self.weapon_buttons = {}
        weapons = ["pistol", "shotgun", "smg", "sniper"]
        for index, weapon in enumerate(weapons):
            button = Button(
                text=weapon.upper(),
                size_hint=(0.23, 0.08),
                pos_hint={"x": 0.02 + 0.24 * index, "y": 0.74},
            )
            button.bind(on_press=lambda btn, name=weapon: self.select_weapon(name))
            self.ui_layout.add_widget(button)
            self.weapon_buttons[weapon] = button

        self.shop_panel = FloatLayout(size_hint=(0.9, 0.75), pos_hint={"x": 0.05, "y": 0.125})
        self.shop_panel_canvas = Widget()
        self.shop_panel.add_widget(self.shop_panel_canvas)
        self.shop_panel.opacity = 0
        self.shop_panel.disabled = True
        self.ui_layout.add_widget(self.shop_panel)

        title = Label(text="WEAPON SHOP", font_size=24, size_hint=(0.6, 0.1), pos_hint={"x": 0.2, "y": 0.82})
        self.shop_panel.add_widget(title)

        for idx, weapon in enumerate(self.weapons):
            if weapon == "pistol":
                continue
            btn = Button(
                text=f"{weapon.title()} - ${self.weapons[weapon]['cost']}",
                size_hint=(0.42, 0.1),
                pos_hint={"x": 0.05 + (idx - 1) % 2 * 0.47, "y": 0.58 - ((idx - 1) // 2) * 0.18},
            )
            btn.bind(on_press=lambda btn, name=weapon: self.purchase_weapon(name))
            self.shop_panel.add_widget(btn)

        close_btn = Button(text="CLOSE", size_hint=(0.3, 0.1), pos_hint={"x": 0.35, "y": 0.05})
        close_btn.bind(on_press=lambda _: self.toggle_shop())
        self.shop_panel.add_widget(close_btn)

    def set_move(self, direction, active):
        self.move_dir[direction] = active

    def select_weapon(self, weapon):
        if weapon in self.unlocked_weapons:
            self.player["weapon"] = weapon
            self.status_label.text = f"Selected {weapon.upper()}"

    def purchase_weapon(self, weapon):
        if weapon in self.unlocked_weapons:
            return
        cost = self.weapons[weapon]["cost"]
        if self.player["money"] >= cost:
            self.player["money"] -= cost
            self.unlocked_weapons.append(weapon)
            self.status_label.text = f"{weapon.title()} unlocked!"
        else:
            self.status_label.text = "Not enough money"

    def toggle_shop(self):
        self.shop_open = not self.shop_open
        self.shop_panel.opacity = 1 if self.shop_open else 0
        self.shop_panel.disabled = not self.shop_open
        self.status_label.text = "Shop open" if self.shop_open else "Tap to aim and fire"

    def on_touch_down(self, touch):
        if self.shop_open:
            return super().on_touch_down(touch)

        if any(child.collide_point(*touch.pos) for child in self.ui_layout.children if isinstance(child, Button)):
            return super().on_touch_down(touch)

        self.crosshair["x"], self.crosshair["y"] = touch.pos
        self.shoot()
        return True

    def on_touch_move(self, touch):
        if self.shop_open:
            return super().on_touch_move(touch)
        self.crosshair["x"], self.crosshair["y"] = touch.pos
        return True

    def shoot(self):
        if self.shop_open:
            return
        current = Clock.get_boottime()
        weapon = self.weapons[self.player["weapon"]]
        if current - self.last_shot < weapon["rate"]:
            return

        mx, my = self.crosshair["x"] + self.camera["x"], self.crosshair["y"] + self.camera["y"]
        dx, dy = mx - self.player["x"], my - self.player["y"]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return

        shots = weapon.get("bullets", 1)
        for _ in range(shots):
            angle = math.atan2(dy, dx) + math.radians(random.uniform(-weapon["spread"], weapon["spread"]))
            self.bullets.append({
                "x": self.player["x"],
                "y": self.player["y"],
                "dx": math.cos(angle) * 1200,
                "dy": math.sin(angle) * 1200,
                "damage": weapon["damage"],
            })
        self.last_shot = current
        self.play_sound("gunshot")

    def throw_grenade(self):
        if self.shop_open or "grenade" not in self.unlocked_weapons:
            return
        mx, my = self.crosshair["x"] + self.camera["x"], self.crosshair["y"] + self.camera["y"]
        self.grenades.append({"x": self.player["x"], "y": self.player["y"], "target": (mx, my), "timer": 60})
        self.play_sound("grenade")

    def move_player(self, dt):
        speed = self.player["speed"] * 60 * dt
        if self.move_dir["up"]:
            self.player["y"] += speed
        if self.move_dir["down"]:
            self.player["y"] -= speed
        if self.move_dir["left"]:
            self.player["x"] -= speed
        if self.move_dir["right"]:
            self.player["x"] += speed
        self.player["x"] = max(0, min(self.player["x"], self.MAP_W))
        self.player["y"] = max(0, min(self.player["y"], self.MAP_H))

    def move_zombies(self, dt):
        for z in list(self.zombies):
            dx, dy = self.player["x"] - z["x"], self.player["y"] - z["y"]
            dist = math.hypot(dx, dy)
            if dist != 0:
                speed = z["speed"] * 50 * dt
                z["x"] += dx / dist * speed
                z["y"] += dy / dist * speed
            if dist < 25:
                self.player["health"] -= 0.2 * dt * 60

    def update_bullets(self, dt):
        for b in list(self.bullets):
            b["x"] += b["dx"] * dt
            b["y"] += b["dy"] * dt
            if b["x"] < 0 or b["y"] < 0 or b["x"] > self.MAP_W or b["y"] > self.MAP_H:
                self.bullets.remove(b)
                continue
            for z in list(self.zombies):
                if math.hypot(b["x"] - z["x"], b["y"] - z["y"]) < 18:
                    z["health"] -= b["damage"]
                    self.play_sound("zombie_hit")
                    if b in self.bullets:
                        self.bullets.remove(b)
                    if z["health"] <= 0:
                        self.zombies.remove(z)
                        self.player["money"] += 10 if z.get("boss") else 1
                    break

    def update_grenades(self):
        for g in list(self.grenades):
            g["timer"] -= 1
            if g["timer"] <= 0:
                self.explosions.append({"x": g["x"], "y": g["y"], "radius": 100})
                self.grenades.remove(g)
                self.play_sound("explosion")
        for e in list(self.explosions):
            for z in list(self.zombies):
                if math.hypot(e["x"] - z["x"], e["y"] - z["y"]) < e["radius"]:
                    z["health"] -= 3
                    if z["health"] <= 0:
                        self.zombies.remove(z)
                        self.player["money"] += 10 if z.get("boss") else 1
            e["radius"] -= 3
            if e["radius"] <= 0:
                self.explosions.remove(e)

    def update_camera(self):
        width, height = self.width, self.height
        self.camera["x"] = self.player["x"] - width / 2
        self.camera["y"] = self.player["y"] - height / 2
        self.camera["x"] = max(0, min(self.camera["x"], self.MAP_W - width))
        self.camera["y"] = max(0, min(self.camera["y"], self.MAP_H - height))

    def check_wave(self):
        if not self.zombies:
            self.wave += 1
            self.spawn_wave()

    def update(self, dt):
        if self.player["health"] <= 0:
            self.status_label.text = "GAME OVER"
            return

        if not self.shop_open:
            self.move_player(dt)
            self.move_zombies(dt)
            self.update_bullets(dt)
            self.update_grenades()
            self.update_camera()
            self.check_wave()

        self.update_ui()
        self.draw_game()

    def update_ui(self):
        self.health_label.text = f"Health: {int(self.player['health'])}"
        self.wave_label.text = f"Wave: {self.wave}"
        self.money_label.text = f"Money: ${self.player['money']}"
        for weapon, button in self.weapon_buttons.items():
            button.disabled = weapon not in self.unlocked_weapons
            if self.player["weapon"] == weapon:
                button.background_color = (0.2, 0.8, 0.2, 1)
            else:
                button.background_color = (1, 1, 1, 1)

    def draw_game(self):
        self.canvas.clear()
        with self.canvas:
            Color(0.12, 0.12, 0.12)
            Rectangle(pos=self.pos, size=self.size)

            width, height = self.width, self.height
            Color(0.2, 0.2, 0.2)
            for x in range(0, self.MAP_W, 100):
                Line(points=[x - self.camera["x"], 0 - self.camera["y"], x - self.camera["x"], self.MAP_H - self.camera["y"]], width=1)
            for y in range(0, self.MAP_H, 100):
                Line(points=[0 - self.camera["x"], y - self.camera["y"], self.MAP_W - self.camera["x"], y - self.camera["y"]], width=1)

            Color(0, 1, 0)
            Ellipse(pos=(self.player["x"] - self.camera["x"] - 15, self.player["y"] - self.camera["y"] - 15), size=(30, 30))

            for z in self.zombies:
                Color(1, 0, 1 if z.get("boss") else 0, 1)
                size = 40 if z.get("boss") else 12
                Ellipse(pos=(z["x"] - self.camera["x"] - size / 2, z["y"] - self.camera["y"] - size / 2), size=(size, size))

            Color(1, 1, 1)
            for b in self.bullets:
                Ellipse(pos=(b["x"] - self.camera["x"] - 3, b["y"] - self.camera["y"] - 3), size=(6, 6))

            Color(1, 1, 0)
            for g in self.grenades:
                Ellipse(pos=(g["x"] - self.camera["x"] - 8, g["y"] - self.camera["y"] - 8), size=(16, 16))

            Color(1, 0.6, 0)
            for e in self.explosions:
                Line(circle=(e["x"] - self.camera["x"], e["y"] - self.camera["y"], e["radius"]), width=2)

            Color(1, 1, 1)
            Line(circle=(self.crosshair["x"], self.crosshair["y"], 12), width=2)
            Line(circle=(self.crosshair["x"], self.crosshair["y"], 18), width=1)

            Color(1, 0, 0)
            Line(points=[10, self.height - 30, 10 + 2 * self.player["health"], self.height - 30], width=8)

class ZombieSurvivalApp(App):
    def build(self):
        root = FloatLayout()
        game = ZombieSurvivalGame(size=Window.size)
        root.add_widget(game)
        return root

if __name__ == "__main__":
    ZombieSurvivalApp().run()
