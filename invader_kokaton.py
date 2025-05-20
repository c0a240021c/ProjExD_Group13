import math
import os
import random
import sys
import time
import pygame as pg

WIDTH = 600  # 幅を広げる
HEIGHT = 722  # 高さも広げる
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

class Bird(pg.sprite.Sprite):
    delta = {
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }
    def __init__(self, num: int, xy: tuple[int, int]):
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)
        self.imgs = {
            (+1, 0): img,
            (-1, 0): img0,
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        # こうかとんの下端が画面下端から40px上になるように配置
        self.rect.midbottom = (xy[0], HEIGHT - 40)
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
        self.rect.move_ip(self.speed*sum_mv[0], 0)  # 横移動のみ
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], 0)
        if sum_mv[0] != 0:
            self.dire = (sum_mv[0], 0)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)

class Bomb(pg.sprite.Sprite):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird, speed=6):
        super().__init__()
        rad = random.randint(10, 50)
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = speed

    def update(self):
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class Beam(pg.sprite.Sprite):
    def __init__(self, bird: Bird):
        super().__init__()
        # ビームは常に上方向
        self.vx, self.vy = 0, -1
        angle = 90  # 上向き
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx
        self.rect.bottom = bird.rect.top  # こうかとんの頭から発射
        self.speed = 10

    def update(self):
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class Explosion(pg.sprite.Sprite):
    def __init__(self, obj: "Bomb|Enemy", life: int):
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()

class Enemy(pg.sprite.Sprite):
    def __init__(self, pos: tuple[int, int], imgs, speed):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.speed = speed
        self.direction = 1  # 1:右, -1:左

    def update(self):
        self.rect.move_ip(self.speed * self.direction, 0)
        # 画面端で反転し、画面外に出ないようにする
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.direction = -1
        elif self.rect.left < 0:
            self.rect.left = 0
            self.direction = 1

class Score:
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class Stagechange:
    def __init__(self):
        self.stage = 1
        self.enemy_speed = 1.0
        self.bomb_speed = 1.0
        self.every_imgs = [
            [pg.image.load(f"fig/alien1.png")],  # ステージ1
            [pg.image.load(f"fig/alien2.png")],  # ステージ2
            [pg.image.load(f"fig/alien3.png")],  # ステージ3
            [pg.image.load(f"fig/alien4.png")]   # ステージ4
        ]
        self.background_images = [
            pg.transform.scale(pg.image.load(f"fig/stage.jpg"), (WIDTH, HEIGHT)),  # ステージ1
            pg.transform.scale(pg.image.load(f"fig/stage1.jpg"), (WIDTH, HEIGHT)),  # ステージ2
            pg.transform.scale(pg.image.load(f"fig/stage2.jpg"), (WIDTH, HEIGHT)),  # ステージ3
            pg.transform.scale(pg.image.load(f"fig/stage3.jpg"), (WIDTH, HEIGHT))   # ステージ4
        ]

    def next_level(self):
        self.stage += 1
        self.enemy_speed *= 1.5  # 速度を1.5倍
        self.bomb_speed *= 1.2

def main():
    pg.display.set_caption("インベーダーこうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/stage.jpg")
    bg_img = pg.transform.scale(bg_img, (WIDTH, HEIGHT))
    score = Score()
    stage_change = Stagechange()

    def spawn_enemies(imgs, speed):
        emys = pg.sprite.Group()
        enemy_margin_x = 80
        enemy_margin_y = 70
        enemy_cols = 5
        enemy_rows = 3
        enemy_width = 64
        total_width = enemy_margin_x * (enemy_cols - 1) + enemy_width
        start_x = (WIDTH - total_width) // 2
        for row in range(enemy_rows):
            for col in range(enemy_cols):
                x = start_x + col * enemy_margin_x
                y = 60 + row * enemy_margin_y
                emys.add(Enemy((x, y), imgs, speed))
        return emys

    bird = Bird(3, (WIDTH//2, HEIGHT - 40))
    beams = pg.sprite.Group()
    emys = spawn_enemies(stage_change.every_imgs[0], stage_change.enemy_speed)
    bombs = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))

        # --- 敵の爆弾発射 ---
        if tmr % 30 == 0 and len(emys) > 0:
            emy = random.choice(emys.sprites())
            bombs.add(Bomb(emy, bird, speed=6*stage_change.bomb_speed))

        screen.blit(stage_change.get_bg_image(), [0, 0])

        # --- ビームと敵・爆弾の当たり判定 ---
        for beam in list(beams):
            hit_emys = pg.sprite.spritecollide(beam, emys, True)
            if hit_emys:
                beam.kill()
                continue
            hit_bombs = pg.sprite.spritecollide(beam, bombs, True)
            if hit_bombs:
                beam.kill()
                continue

        # --- 爆弾とこうかとんの当たり判定 ---
        if pg.sprite.spritecollide(bird, bombs, True):
            font = pg.font.Font(None, 120)
            text = font.render("GAME OVER", True, (255, 0, 0))
            rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(text, rect)
            pg.display.update()
            pg.time.wait(2000)
            return

        # --- 全敵撃破でステージクリア ---
        if len(emys) == 0:
            font = pg.font.Font(None, 120)
            text = font.render("GAME CLEAR", True, (0, 255, 0))
            rect = text.get_rect(center=(WIDTH//2, HEIGHT//3))
            screen.blit(text, rect)
            pg.display.update()
            pg.time.wait(2000)
            # 次のステージへ
            imgs = stage_change.next_level()
            emys = spawn_enemies(imgs, stage_change.enemy_speed)
            bombs.empty()
            beams.empty()
            tmr = 0
            continue

        emys.update()
        emys.draw(screen)
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        bombs.update()
        bombs.draw(screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
