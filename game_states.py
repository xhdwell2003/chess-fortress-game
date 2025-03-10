from enum import Enum
import pygame
import pymunk
import pymunk.pygame_util
import math
from game_objects import ChessPiece, ChessPieceType, Projectile, ChessModel

# 游戏状态枚举
class GameState(Enum):
    MAIN_MENU = 0
    BUILDING_MODEL_P1 = 1
    BUILDING_MODEL_P2 = 2
    BATTLE = 3
    GAME_OVER = 4

# 游戏管理类
class GameManager:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_state = GameState.MAIN_MENU
        
        # 初始化物理空间
        self.space = pymunk.Space()
        self.space.gravity = (0, 900)  # 设置重力
        
        # 创建地面
        self.create_ground()
        
        # 玩家模型
        self.player1_model = ChessModel(1)
        self.player2_model = ChessModel(2)
        
        # 当前活动玩家
        self.active_player = 1
        
        # 弹射物
        self.projectile = None
        
        # 弹射力度和方向
        self.shoot_strength = 0
        self.charging = False
        self.max_strength = 2000
        
        # 游戏界面设置
        self.draw_options = pymunk.pygame_util.DrawOptions(pygame.Surface((1, 1)))
        
        # 初始化支持中文的字体
        try:
            # 使用arialunicode字体，这个字体在系统中支持中文
            self.font = pygame.font.SysFont("arialunicode", 24)
        except:
            # 如果上述字体不可用，尝试使用系统默认字体
            font_default = pygame.font.get_default_font()
            self.font = pygame.font.Font(font_default, 24)
        
        # 棋子选择
        self.selected_chess_type = ChessPieceType.MILITARY_CHESS
        
    def create_ground(self):
        """创建地面和边界"""
        # 地面
        ground_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        ground_shape = pymunk.Segment(ground_body, (0, self.screen_height - 50), 
                                      (self.screen_width, self.screen_height - 50), 5)
        ground_shape.friction = 0.9
        ground_shape.elasticity = 0.5
        self.space.add(ground_body, ground_shape)
        
        # 左边界
        left_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        left_shape = pymunk.Segment(left_body, (0, 0), (0, self.screen_height), 5)
        left_shape.friction = 0.5
        left_shape.elasticity = 0.5
        self.space.add(left_body, left_shape)
        
        # 右边界
        right_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        right_shape = pymunk.Segment(right_body, (self.screen_width, 0), 
                                    (self.screen_width, self.screen_height), 5)
        right_shape.friction = 0.5
        right_shape.elasticity = 0.5
        self.space.add(right_body, right_shape)
        
    def update(self, dt):
        """更新游戏状态"""
        self.space.step(dt)
        
        # 在战斗状态下检查胜负
        if self.current_state == GameState.BATTLE:
            if self.player1_model.is_destroyed():
                print("玩家1模型被摧毁，玩家2获胜")
                self.current_state = GameState.GAME_OVER
                self.winner = 2
            elif self.player2_model.is_destroyed():
                print("玩家2模型被摧毁，玩家1获胜")
                self.current_state = GameState.GAME_OVER
                self.winner = 1
                
    def handle_event(self, event):
        """处理游戏事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                mouse_pos = pygame.mouse.get_pos()
                
                # 根据当前状态处理点击事件
                if self.current_state == GameState.MAIN_MENU:
                    # 检查开始游戏按钮
                    if 300 <= mouse_pos[0] <= 500 and 250 <= mouse_pos[1] <= 300:
                        self.current_state = GameState.BUILDING_MODEL_P1
                        print("进入玩家1建模阶段")
                    # 检查加载模型按钮
                    elif 300 <= mouse_pos[0] <= 500 and 350 <= mouse_pos[1] <= 400:
                        self.load_models()
                        self.current_state = GameState.BATTLE
                        print("加载模型并进入战斗阶段")
                        self.prepare_battle_phase()
                        
                elif self.current_state == GameState.BUILDING_MODEL_P1 or self.current_state == GameState.BUILDING_MODEL_P2:
                    # 检查玩家2的"进入战斗"按钮
                    if (self.current_state == GameState.BUILDING_MODEL_P2 and 
                        self.screen_width - 150 <= mouse_pos[0] <= self.screen_width - 20 and
                        100 <= mouse_pos[1] <= 140):
                        # 先保存玩家2的模型
                        self.player2_model.save("player2_model")
                        print("点击进入战斗按钮，玩家2模型已保存")
                        # 设置战斗状态
                        self.current_state = GameState.BATTLE
                        self.active_player = 1
                        self.prepare_battle_phase()
                        print("通过按钮直接进入战斗阶段")
                    else:
                        # 添加棋子
                        self.add_chess_piece(mouse_pos[0], mouse_pos[1])
                    
                elif self.current_state == GameState.BATTLE:
                    # 开始充能
                    self.charging = True
                    self.shoot_strength = 0
                    print(f"玩家{self.active_player}开始充能")
                    
                    # 创建弹射物
                    if self.active_player == 1:
                        self.projectile = Projectile(150, self.screen_height - 150, self.space)
                    else:
                        self.projectile = Projectile(self.screen_width - 150, self.screen_height - 150, self.space)
                    
                # 如果是游戏结束状态，检查是否点击了返回主菜单
                elif self.current_state == GameState.GAME_OVER:
                    if (self.screen_width // 2 - 100 <= mouse_pos[0] <= self.screen_width // 2 + 100 and 
                        self.screen_height // 2 + 50 <= mouse_pos[1] <= self.screen_height // 2 + 100):
                        self.reset_game()
                        print("游戏重置，返回主菜单")
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.charging and self.current_state == GameState.BATTLE:
                # 结束充能，发射弹射物
                self.charging = False
                mouse_pos = pygame.mouse.get_pos()
                
                # 计算发射方向
                if self.projectile:
                    dx = mouse_pos[0] - self.projectile.body.position.x
                    dy = mouse_pos[1] - self.projectile.body.position.y
                    angle = math.atan2(dy, dx)
                    
                    # 发射方向向量
                    dir_x = math.cos(angle)
                    dir_y = math.sin(angle)
                    
                    # 应用冲量发射弹射物
                    strength = min(self.shoot_strength, self.max_strength)
                    self.projectile.apply_impulse(pymunk.Vec2d(dir_x, dir_y), strength)
                    
                    # 切换玩家
                    self.active_player = 2 if self.active_player == 1 else 1
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.selected_chess_type = ChessPieceType.MILITARY_CHESS
                print("选择军棋")
            elif event.key == pygame.K_2:
                self.selected_chess_type = ChessPieceType.CHINESE_CHESS
                print("选择中国象棋")
            elif event.key == pygame.K_3:
                self.selected_chess_type = ChessPieceType.GO_CHESS
                print("选择围棋")
            elif event.key == pygame.K_s and (self.current_state == GameState.BUILDING_MODEL_P1 or 
                                            self.current_state == GameState.BUILDING_MODEL_P2):
                # 保存当前模型
                if self.current_state == GameState.BUILDING_MODEL_P1:
                    self.player1_model.save("player1_model")
                    self.current_state = GameState.BUILDING_MODEL_P2
                    print("玩家1模型已保存，进入玩家2建模阶段")
                else:
                    self.player2_model.save("player2_model")
                    print("玩家2模型已保存，准备进入战斗阶段")
                    self.current_state = GameState.BATTLE
                    # 初始化战斗阶段
                    self.active_player = 1  # 确保玩家1先攻击
                    self.prepare_battle_phase()  # 添加新方法准备战斗阶段
                    print(f"当前游戏状态: {self.current_state}, 活动玩家: {self.active_player}")
            # 添加键盘快捷键进入战斗模式（用于调试）
            elif event.key == pygame.K_b and self.current_state != GameState.BATTLE:
                print("使用快捷键强制进入战斗阶段")
                self.current_state = GameState.BATTLE
                self.active_player = 1
                self.prepare_battle_phase()
                
    def add_chess_piece(self, x, y):
        """添加棋子到当前玩家的模型中"""
        current_model = self.player1_model if self.current_state == GameState.BUILDING_MODEL_P1 else self.player2_model
        piece = ChessPiece(x, y, self.selected_chess_type, self.space)
        current_model.add_piece(piece)
        
    def load_models(self):
        """加载已保存的模型"""
        self.player1_model = ChessModel.load("player1_model", self.space) or ChessModel(1)
        self.player2_model = ChessModel.load("player2_model", self.space) or ChessModel(2)
        
    def draw(self, screen):
        """绘制游戏"""
        screen.fill((255, 255, 255))  # 白色背景
        
        # 绘制地面
        pygame.draw.line(screen, (0, 0, 0), 
                        (0, self.screen_height - 50), 
                        (self.screen_width, self.screen_height - 50), 5)
        
        # 根据当前状态绘制不同界面
        if self.current_state == GameState.MAIN_MENU:
            self.draw_main_menu(screen)
        elif self.current_state == GameState.BUILDING_MODEL_P1:
            self.draw_building_phase(screen, "玩家1")
        elif self.current_state == GameState.BUILDING_MODEL_P2:
            self.draw_building_phase(screen, "玩家2")
        elif self.current_state == GameState.BATTLE:
            self.draw_battle_phase(screen)
        elif self.current_state == GameState.GAME_OVER:
            self.draw_game_over(screen)
            
        # 在任何状态下都显示调试信息和快捷键提示
        debug_info = self.font.render(f"当前状态: {self.current_state.name}", True, (100, 100, 100))
        screen.blit(debug_info, (10, self.screen_height - 30))
        
        if self.current_state != GameState.BATTLE:
            debug_hint = self.font.render("按B键直接进入战斗模式", True, (100, 100, 100))
            screen.blit(debug_hint, (self.screen_width - debug_hint.get_width() - 10, self.screen_height - 30))
            
    def draw_main_menu(self, screen):
        """绘制主菜单"""
        title = self.font.render("棋子堡垒对战游戏", True, (0, 0, 0))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 150))
        
        # 开始游戏按钮
        pygame.draw.rect(screen, (100, 100, 255), (300, 250, 200, 50))
        start_text = self.font.render("开始游戏", True, (255, 255, 255))
        screen.blit(start_text, (400 - start_text.get_width() // 2, 275 - start_text.get_height() // 2))
        
        # 加载模型按钮
        pygame.draw.rect(screen, (100, 255, 100), (300, 350, 200, 50))
        load_text = self.font.render("加载模型", True, (0, 0, 0))
        screen.blit(load_text, (400 - load_text.get_width() // 2, 375 - load_text.get_height() // 2))
        
    def draw_building_phase(self, screen, player_name):
        """绘制建模阶段"""
        # 绘制标题
        title = self.font.render(f"{player_name} 建造阶段", True, (0, 0, 0))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 20))
        
        # 绘制棋子选择提示
        chess_hint = self.font.render("按 1-3 键选择棋子类型: 1=军棋, 2=象棋, 3=围棋", True, (0, 0, 0))
        screen.blit(chess_hint, (20, 60))
        
        # 显示当前选择的棋子类型
        current_chess = self.font.render(f"当前棋子: {self.selected_chess_type.name}", True, (0, 0, 255))
        screen.blit(current_chess, (20, 100))
        
        # 绘制保存提示
        save_hint = self.font.render("按 S 键保存模型并继续", True, (0, 0, 255))
        screen.blit(save_hint, (self.screen_width - save_hint.get_width() - 20, 60))
        
        # 如果是玩家2的建模阶段，显示"进入战斗"按钮
        if player_name == "玩家2":
            pygame.draw.rect(screen, (255, 100, 100), (self.screen_width - 150, 100, 130, 40))
            battle_text = self.font.render("进入战斗", True, (255, 255, 255))
            screen.blit(battle_text, (self.screen_width - 150 + (130 - battle_text.get_width()) // 2, 
                                   100 + (40 - battle_text.get_height()) // 2))
        
        # 绘制已添加的棋子
        current_model = self.player1_model if player_name == "玩家1" else self.player2_model
        for piece in current_model.pieces:
            piece.draw(screen, self.draw_options)
            
    def draw_battle_phase(self, screen):
        """绘制战斗阶段"""
        # 绘制标题
        title = self.font.render(f"玩家{self.active_player}的回合", True, (0, 0, 0))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 20))
        
        # 绘制战斗指导信息
        if not self.charging and not self.projectile:
            guide_text1 = self.font.render("点击鼠标左键开始充能，松开发射笔芯攻击对方模型", True, (0, 0, 255))
            screen.blit(guide_text1, (self.screen_width // 2 - guide_text1.get_width() // 2, 60))
            
            guide_text2 = self.font.render("玩家轮流攻击，直到一方模型散架", True, (0, 0, 255))
            screen.blit(guide_text2, (self.screen_width // 2 - guide_text2.get_width() // 2, 90))
            
            # 绘制起始点提示
            start_x = 150 if self.active_player == 1 else self.screen_width - 150
            pygame.draw.circle(screen, (0, 255, 0), (int(start_x), int(self.screen_height - 150)), 15)
            pygame.draw.circle(screen, (0, 0, 0), (int(start_x), int(self.screen_height - 150)), 15, 2)
        
        # 绘制两个玩家的模型
        for piece in self.player1_model.pieces:
            piece.draw(screen, self.draw_options)
            
        for piece in self.player2_model.pieces:
            piece.draw(screen, self.draw_options)
            
        # 绘制弹射物
        if self.projectile:
            self.projectile.draw(screen, self.draw_options)
            
        # 如果正在充能，绘制充能条
        if self.charging:
            self.shoot_strength = min(self.shoot_strength + 50, self.max_strength)
            charge_percent = self.shoot_strength / self.max_strength
            
            pygame.draw.rect(screen, (200, 200, 200), (50, 50, 200, 20))
            pygame.draw.rect(screen, (255, 0, 0), (50, 50, int(200 * charge_percent), 20))
            
            charge_text = self.font.render(f"力度: {int(charge_percent * 100)}%", True, (0, 0, 0))
            screen.blit(charge_text, (260, 50))

            # 绘制方向指示线
            if self.projectile:
                mouse_pos = pygame.mouse.get_pos()
                pygame.draw.line(screen, (255, 0, 0), 
                              (int(self.projectile.body.position.x), int(self.projectile.body.position.y)),
                              mouse_pos, 2)
            
    def draw_game_over(self, screen):
        """绘制游戏结束界面"""
        # 绘制半透明背景
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # 半透明黑色背景
        screen.blit(overlay, (0, 0))
        
        # 绘制胜利标题
        title = self.font.render(f"游戏结束! 玩家{self.winner}获胜!", True, (255, 255, 255))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, self.screen_height // 2 - 80))
        
        # 绘制游戏结果描述
        if self.winner == 1:
            result_text = "玩家1的棋子堡垒坚固稳定，成功击溃了对手的防线!"
        else:
            result_text = "玩家2的棋子堡垒坚固稳定，成功击溃了对手的防线!"
            
        result = self.font.render(result_text, True, (255, 255, 255))
        screen.blit(result, (self.screen_width // 2 - result.get_width() // 2, self.screen_height // 2 - 30))
        
        # 绘制返回主菜单按钮
        pygame.draw.rect(screen, (100, 100, 255), (self.screen_width // 2 - 100, self.screen_height // 2 + 50, 200, 50))
        menu_text = self.font.render("返回主菜单", True, (255, 255, 255))
        screen.blit(menu_text, (self.screen_width // 2 - menu_text.get_width() // 2, 
                              self.screen_height // 2 + 50 + (50 - menu_text.get_height()) // 2))
        
        # 检查点击返回主菜单
        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            if (self.screen_width // 2 - 100 <= mouse_pos[0] <= self.screen_width // 2 + 100 and 
                self.screen_height // 2 + 50 <= mouse_pos[1] <= self.screen_height // 2 + 100):
                self.reset_game()
                
    def reset_game(self):
        """重置游戏到初始状态"""
        # 清除所有物理对象
        self.space = pymunk.Space()
        self.space.gravity = (0, 900)
        
        # 重新创建地面
        self.create_ground()
        
        # 重置玩家模型
        self.player1_model = ChessModel(1)
        self.player2_model = ChessModel(2)
        
        # 重置游戏状态
        self.current_state = GameState.MAIN_MENU
        self.active_player = 1
        self.projectile = None 

    def prepare_battle_phase(self):
        """准备战斗阶段，重新定位棋子模型并添加引导提示"""
        print("准备战斗阶段...")
        print(f"玩家1模型棋子数: {len(self.player1_model.pieces)}")
        print(f"玩家2模型棋子数: {len(self.player2_model.pieces)}")
        
        # 重新定位玩家1的模型到左侧
        offset_x1 = 200
        for piece in self.player1_model.pieces:
            if piece.body.position.x > self.screen_width / 2:
                piece.body.position = piece.body.position.x - offset_x1, piece.body.position.y
                
        # 重新定位玩家2的模型到右侧
        offset_x2 = 200
        for piece in self.player2_model.pieces:
            if piece.body.position.x < self.screen_width / 2:
                piece.body.position = piece.body.position.x + offset_x2, piece.body.position.y

        # 清除任何现有的弹射物
        self.projectile = None
        self.charging = False
        self.shoot_strength = 0
        print("战斗阶段准备完毕") 