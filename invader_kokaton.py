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
        rad = random.randint(8, 18)  # 小さめに
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
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    def __init__(self, pos: tuple[int, int]):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos

    def update(self):
        pass  # 動かさない

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

def mode_select(screen):
    title_font = pg.font.SysFont(["Meiryo", "MS Gothic", "Yu Gothic", "Arial Unicode MS"], 36)
    font = pg.font.SysFont(["Meiryo", "MS Gothic", "Yu Gothic", "Arial Unicode MS"], 56)
    small_font = pg.font.SysFont(["Meiryo", "MS Gothic", "Yu Gothic", "Arial Unicode MS"], 28)
    modes = [
        ("EASY", (0, 255, 0), "初心者向け"),
        ("NORMAL", (255, 165, 0), "敵の攻撃が速く・強くなります"),
        ("HARD", (255, 0, 0), "さらに敵の攻撃が速く・強くなります")
    ]
    rects = []
    while True:
        screen.fill((0, 0, 0))
        # タイトル
        title = title_font.render("モードを選択してください", True, (255, 255, 255))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        for i, (label, color, desc_text) in enumerate(modes):
            y = 290 + i*150  
            desc = small_font.render(desc_text, True, (200, 200, 200))
            screen.blit(desc, (WIDTH//2 - desc.get_width()//2, y - 70))
            text = font.render(label, True, color)
            rect = text.get_rect(center=(WIDTH//2, y))
            screen.blit(text, rect)
            rects.append((rect, label))
        pg.display.update()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for rect, label in rects:
                    if rect.collidepoint(mx, my):
                        return label.lower()
        rects.clear()

def main():
    pg.display.set_caption("インベーダーこうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))

    # --- モードセレクト ---
    mode = mode_select(screen)
    # モードごとのパラメータ設定
    if mode == "easy":
        bomb_interval = 120   
        bomb_speed = 5       
    elif mode == "normal":
        bomb_interval = 60  
        bomb_speed = 8        
    elif mode == "hard":
        bomb_interval = 30    
        bomb_speed = 10     

    bg_img = pg.image.load(f"fig/stage.jpg")
    bg_img = pg.transform.scale(bg_img, (WIDTH, HEIGHT))
    score = Score()

    bird = Bird(3, (WIDTH//2, HEIGHT - 40))
    beams = pg.sprite.Group()
    emys = pg.sprite.Group()
    bombs = pg.sprite.Group()

    # 敵を中央寄せで5体×3列配置
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
            emys.add(Enemy((x, y)))

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))

        # --- 敵の爆弾発射（モードごとの間隔で） ---
        if tmr % bomb_interval == 0 and len(emys) > 0:
            emy = random.choice(emys.sprites())
            bombs.add(Bomb(emy, bird, bomb_speed))

        screen.blit(bg_img, [0, 0])

        # --- ビームと敵・爆弾の当たり判定 ---
        for beam in list(beams):
            hit_emys = pg.sprite.spritecollide(beam, emys, True)
            if hit_emys:
                beam.kill()
                score.value += 10  #スコアが10上がる
                continue
            hit_bombs = pg.sprite.spritecollide(beam, bombs, True)
            if hit_bombs:
                beam.kill()
                score.value += 1  #スコアが１上がる
                continue  # このビームは消えたので次へ

        # --- 爆弾とこうかとんの当たり判定 ---
        if pg.sprite.spritecollide(bird, bombs, True):
            font = pg.font.Font(None, 120)
            text = font.render("GAME OVER", True, (255, 0, 0))
            rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(text, rect)
            pg.display.update()
            pg.time.wait(2000)
            return

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
