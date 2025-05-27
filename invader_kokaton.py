import pygame as pg

class Wall(pg.sprite.Sprite):
    """ 壁クラス """
    
    def __init__(self, x, y, width=80, height=16):
        super().__init__()
        self.image = pg.Surface((width, height))
        self.image.fill((180, 180, 180))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def update(self):
        pass
import math
import os
import random
import sys
import time
from typing import Sequence
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

    def update(self, key_lst: Sequence[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
        self.rect.move_ip(self.speed*sum_mv[0], 0)  # 横移動のみ
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], 0)
        if sum_mv[0] != 0:
            if sum_mv[0] > 0:
                self.dire = (+1, 0)
            else:
                self.dire = (-1, 0)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)

class Bomb(pg.sprite.Sprite):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird, speed=6):
        super().__init__()
        # 爆弾画像を使用（ランダムなサイズで拡大縮小、下側を進行方向に回転、上下反転）
        orig_img = pg.image.load("fig/bomb.png")
        orig_img = pg.transform.flip(orig_img, False, True)  # 上下反転
        dx, dy = calc_orientation(emy.rect, bird.rect)
        angle = math.degrees(math.atan2(dy, dx)) + 90
        scale = random.uniform(0.15, 0.5)  # ランダムな倍率（小さめ～標準）
        img = pg.transform.rotozoom(orig_img, -angle, scale)
        self.image = img
        self.rect = self.image.get_rect()
        self.vx, self.vy = dx, dy
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

class FireBeam(pg.sprite.Sprite):
    def __init__(self, bird: Bird):
        super().__init__()
        self.vx, self.vy = 0, -1
        angle = 90  # 上向き
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/fire.png"), angle, 1.0)
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx
        self.rect.bottom = bird.rect.top
        self.speed = 10

    def update(self):
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class Tougarasi(pg.sprite.Sprite):
    def __init__(self, bird: Bird):
        super().__init__()
        self.image = pg.image.load(f"fig/tougarasi.png")
        self.rect = self.image.get_rect()
        exsitaitem = random.randint(0,600)
        self.rect.bottomright = (exsitaitem, HEIGHT - 40)
    
    def update(self, screen: pg.Surface):
        screen.blit(self.image, self.rect)

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
class Stagechange:
    """
    ステージの値を上げていく
    敵の速度を挙げていく
    弾速を上げていく
    ステージごとの背景画像と敵の画像のリスト
    ステージのインデックスがリストの中にあればそれを返しなければ一番最後の画像を返す、敵の画像も同様
    """
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

    def get_bg_image(self):
        idx = self.stage - 1
        if 0 <= idx < len(self.background_images):
            return self.background_images[idx]
        else:
            return self.background_images[-1]

    def next_stage(self):
        self.stage += 1
        self.enemy_speed *= 1.5  # 速度を1.5倍
        self.bomb_speed *= 1.2
        idx = self.stage - 1
        if 0 <= idx < len(self.every_imgs):
            return self.every_imgs[idx]
        else:
            return self.every_imgs[-1]

def main():
    # --- 壁グループの作成 ---
    walls = pg.sprite.Group()
    wall_width = 80
    wall_height = 16
    wall_gap = 40
    base_y = HEIGHT - 140  # こうかとんの少し上
    wall_xs = [WIDTH//4 - wall_width//2, WIDTH//2 - wall_width//2, 3*WIDTH//4 - wall_width//2]
    # 2段分配置
    for i in range(2):
        for x in wall_xs:
            walls.add(Wall(x, base_y - i*(wall_height+8), wall_width, wall_height))
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
    emys = pg.sprite.Group()
    bombs = pg.sprite.Group()
    bombs = pg.sprite.Group()  # 爆弾グループを追加
    tougarasi = pg.sprite.Group()

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
            # emys.add(Enemy((x, y)))
    emys = spawn_enemies(stage_change.every_imgs[0], stage_change.enemy_speed)
    bombs = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()
    start_time = time.time()  # 経過時間計測用
    fire_mode = False
    fire_start = 0
    fire_duration = 200  # 4秒(50fps×4)
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if fire_mode:
                    beams.add(FireBeam(bird))
                else:
                    beams.add(Beam(bird))

        # --- とうがらし出現 ---
        if tmr % 200 == 0:
            tougarasi.add(Tougarasi(bird))
        # --- とうがらし取得判定 ---
        for t in list(tougarasi):
            if bird.rect.colliderect(t.rect):
                tougarasi.remove(t)
                fire_mode = True
                fire_start = tmr
        # --- fireモード時間管理 ---
        if fire_mode and tmr - fire_start > fire_duration:
            fire_mode = False

        # --- 敵の爆弾発射（モードごとの間隔で） ---
        if tmr % bomb_interval == 0 and len(emys) > 0:
            emy = random.choice(emys.sprites())
            bombs.add(Bomb(emy, bird, bomb_speed))
        # --- 敵の爆弾発射 ---
        if tmr % 30 == 0 and len(emys) > 0:
            emy = random.choice(emys.sprites())
            bombs.add(Bomb(emy, bird, speed=6*stage_change.bomb_speed))

        screen.blit(stage_change.get_bg_image(), [0, 0])


        # --- ビームと敵・爆弾・壁の当たり判定 ---
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

            # 壁との当たり判定
            hit_walls = pg.sprite.spritecollide(beam, walls, True)
            if hit_walls:
                beam.kill()
                continue




        # --- 爆弾と壁の当たり判定 ---
        for bomb in list(bombs):
            hit_walls = pg.sprite.spritecollide(bomb, walls, True)
            if hit_walls:
                bomb.kill()

        

        # # --- 爆弾とこうかとんの当たり判定 ---
        if pg.sprite.spritecollide(bird, bombs, True):

        
            # GAME OVER表示
            font = pg.font.Font(None, 120)
            text = font.render("GAME OVER", True, (255, 0, 0))
            rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 40))
            elapsed_time = time.time() - start_time
            screen.blit(text, rect)
            font_time = pg.font.Font(None, 60)
            time_txt = font_time.render(f"Time: {elapsed_time:.1f}s", True, (255,255,255))
            rect_time = time_txt.get_rect(center=(WIDTH//2, HEIGHT//2 + 40))
            screen.blit(time_txt, rect_time)
            pg.display.update()
            pg.time.wait(2200)  # 2.2秒表示
            return  # ゲーム終了
            
    
        walls.draw(screen)
        # --- 経過時間の計算と表示（小数1桁まで） ---
        elapsed_time = time.time() - start_time
        font_time = pg.font.Font(None, 40)
        time_txt = font_time.render(f"Time: {elapsed_time:.1f}s", True, (255,255,255))
        screen.blit(time_txt, (10, 10))
        
        # --- 全敵撃破でステージクリア ---
        if len(emys) == 0:
            font = pg.font.Font(None, 120) #フォントのオブジェクトを作成
            text = font.render("GAME CLEAR", True, (0, 255, 0)) #ジャギングなしのgame clearの文字を作成
            rect = text.get_rect(center=(WIDTH//2, HEIGHT//3)) # 文字の位置を取得する
            screen.blit(text, rect) #textをrectの位置に書く

            pg.display.update() #画面に表示する
            pg.time.wait(2000) # 二秒待つ
            # 次のステージへ
            imgs = stage_change.next_stage() #新しい画像を表示
            emys = spawn_enemies(imgs, stage_change.enemy_speed) #次のimgsをspawn_enemiesに渡してemysに入れる
            bombs.empty() #爆弾を空にしている
            beams.empty() #ビームを空にしている
            tmr = 0 #タイマーをゼロに
            # 壁を復活させる
            walls.empty()
            for i in range(2):
                for x in wall_xs:
                    walls.add(Wall(x, base_y - i*(wall_height+8), wall_width, wall_height))
            continue

        emys.update()
        emys.draw(screen)
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        bombs.update()
        bombs.draw(screen)
        tougarasi.update(screen)
        tougarasi.draw(screen)
        score.update(screen)
        
        pg.display.update()
        tmr += 1
        clock.tick(50)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
