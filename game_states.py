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
        self.space.gravity = (0, 50)  # 极小的重力，几乎接近零
        self.space.damping = 0.95  # 非常高的阻尼，减少振动和移动
        
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
        
        # 拖放功能相关变量
        self.dragging = False
        self.drag_piece = None
        self.drag_offset = (0, 0)
        
        # 游戏界面设置
        self.draw_options = pymunk.pygame_util.DrawOptions(pygame.Surface((1, 1)))
        
        # 初始化支持中文的字体
        try:
            # 使用arialunicode字体，这个字体在系统中支持中文
            self.font = pygame.font.SysFont("arialunicode", 28, bold=True)  # 增大字体并设置为粗体提高可读性
        except:
            # 如果上述字体不可用，尝试使用系统默认字体
            font_default = pygame.font.get_default_font()
            self.font = pygame.font.Font(font_default, 28)
        
        # 棋子选择
        self.selected_chess_type = ChessPieceType.MILITARY_CHESS
        
        # 调试选项
        self.debug_draw = False  # 是否启用调试绘制
        
    def create_ground(self):
        """创建地面和边界"""
        # 地面
        ground_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        ground_shape = pymunk.Segment(ground_body, (0, self.screen_height - 50), 
                                      (self.screen_width, self.screen_height - 50), 5)
        ground_shape.friction = 1.0  # 最大摩擦力，防止滑动
        ground_shape.elasticity = 0.1  # 很低的弹性，防止弹跳
        self.space.add(ground_body, ground_shape)
        
        # 左边界
        left_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        left_shape = pymunk.Segment(left_body, (0, 0), (0, self.screen_height), 5)
        left_shape.friction = 1.0
        left_shape.elasticity = 0.1
        self.space.add(left_body, left_shape)
        
        # 右边界
        right_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        right_shape = pymunk.Segment(right_body, (self.screen_width, 0), 
                                    (self.screen_width, self.screen_height), 5)
        right_shape.friction = 1.0
        right_shape.elasticity = 0.1
        self.space.add(right_body, right_shape)
        
    def update(self, dt):
        """更新游戏状态"""
        # 使用固定的物理步长，避免物理模拟中的不稳定性
        step_dt = 1/120.0  # 固定步长为120FPS
        steps = int(dt / step_dt) + 1
        for _ in range(steps):
            self.space.step(step_dt)
        
        # 确保所有棋子都在屏幕内
        self.keep_pieces_in_bounds()
        
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
                
    def keep_pieces_in_bounds(self):
        """确保所有棋子都在屏幕边界内"""
        # 定义边界
        margin = 20
        left_bound = margin
        right_bound = self.screen_width - margin
        top_bound = margin
        bottom_bound = self.screen_height - margin
        
        # 检查所有棋子
        for model in [self.player1_model, self.player2_model]:
            for piece in model.pieces:
                if hasattr(piece, 'body') and hasattr(piece.body, 'position'):
                    x, y = piece.body.position
                    
                    # 检查是否超出边界
                    if x < left_bound:
                        piece.body.position = (left_bound, y)
                        piece.body.velocity = (0, piece.body.velocity.y)
                    elif x > right_bound:
                        piece.body.position = (right_bound, y)
                        piece.body.velocity = (0, piece.body.velocity.y)
                        
                    if y < top_bound:
                        piece.body.position = (x, top_bound)
                        piece.body.velocity = (piece.body.velocity.x, 0)
                    elif y > bottom_bound:
                        piece.body.position = (x, bottom_bound)
                        piece.body.velocity = (piece.body.velocity.x, 0)
                        
                    # 如果速度太小，直接停止移动
                    velocity_length = piece.body.velocity.length
                    if velocity_length < 5:
                        piece.body.velocity = (0, 0)
                        piece.body.angular_velocity = 0
        
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
                        # 创建并开始拖动一个新棋子
                        x, y = mouse_pos
                        
                        # 确保不会在地面下方放置棋子
                        if y < self.screen_height - 70:
                            # 如果已经在拖动，确保先停止当前拖动
                            if self.dragging:
                                print("警告：开始新拖动前先结束之前的拖动")
                                self.stop_dragging()
                                
                            self.start_dragging(x, y)
                            print(f"开始拖动{self.selected_chess_type.name}棋子")
                        
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
            if event.button == 1:
                if self.dragging and (self.current_state == GameState.BUILDING_MODEL_P1 or 
                                   self.current_state == GameState.BUILDING_MODEL_P2):
                    # 放置拖动中的棋子
                    self.stop_dragging()
                
                elif self.charging and self.current_state == GameState.BATTLE:
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
        
        elif event.type == pygame.MOUSEMOTION:
            # 如果正在拖动棋子，更新棋子位置
            if self.dragging and self.drag_piece:
                mouse_pos = pygame.mouse.get_pos()
                self.drag_piece.body.position = (mouse_pos[0] - self.drag_offset[0], 
                                               mouse_pos[1] - self.drag_offset[1])
        
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
            # 添加调试绘制切换
            elif event.key == pygame.K_d:
                self.debug_draw = not self.debug_draw
                print(f"{'启用' if self.debug_draw else '禁用'}调试绘制")
            # 添加旋转控制 - 方向键旋转当前拖动的棋子
            elif self.dragging and self.drag_piece:
                rotation_step = 15  # 每次旋转15度
                if event.key == pygame.K_LEFT:
                    self.drag_piece.body.angle += math.radians(rotation_step)
                    print(f"棋子逆时针旋转 {rotation_step} 度")
                elif event.key == pygame.K_RIGHT:
                    self.drag_piece.body.angle -= math.radians(rotation_step)
                    print(f"棋子顺时针旋转 {rotation_step} 度")
                
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
            # 显示棋子数量
            pieces_count = len(self.player1_model.pieces)
            count_text = self.font.render(f"当前棋子数量: {pieces_count}", True, (0, 0, 0))
            screen.blit(count_text, (20, self.screen_height - 60))
        elif self.current_state == GameState.BUILDING_MODEL_P2:
            self.draw_building_phase(screen, "玩家2")
            # 显示棋子数量
            pieces_count = len(self.player2_model.pieces)
            count_text = self.font.render(f"当前棋子数量: {pieces_count}", True, (0, 0, 0))
            screen.blit(count_text, (20, self.screen_height - 60))
        elif self.current_state == GameState.BATTLE:
            self.draw_battle_phase(screen)
        elif self.current_state == GameState.GAME_OVER:
            self.draw_game_over(screen)
            
        # 在任何状态下都显示调试信息和快捷键提示
        debug_info = self.font.render(f"当前状态: {self.current_state.name}", True, (100, 100, 100))
        screen.blit(debug_info, (10, self.screen_height - 30))
        
        # 调试绘制模式提示
        debug_text = self.font.render("按D键切换调试绘制" if not self.debug_draw else "调试模式开启 (按D关闭)", True, (255, 0, 0) if self.debug_draw else (100, 100, 100))
        screen.blit(debug_text, (self.screen_width - debug_text.get_width() - 10, self.screen_height - 30))
        
        if self.current_state != GameState.BATTLE:
            debug_hint = self.font.render("按B键直接进入战斗模式", True, (100, 100, 100))
            screen.blit(debug_hint, (self.screen_width - debug_hint.get_width() - 10, self.screen_height - 60))
            
        # 如果启用了调试绘制，绘制所有物理对象
        if self.debug_draw:
            try:
                # 创建新的DrawOptions实例
                draw_options = pymunk.pygame_util.DrawOptions(screen)
                # 设置绘制选项
                draw_options.flags = pymunk.pygame_util.DrawOptions.DRAW_SHAPES | pymunk.pygame_util.DrawOptions.DRAW_COLLISION_POINTS
                # 绘制整个物理空间
                self.space.debug_draw(draw_options)
            except Exception as e:
                print(f"调试绘制出错: {e}")
            
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
        
        # 绘制拖放提示
        drag_hint = self.font.render("点击并拖动来搭建棋子", True, (0, 0, 255))
        screen.blit(drag_hint, (20, 140))
        
        # 如果正在拖动，显示旋转提示
        if self.dragging:
            rotate_hint = self.font.render("使用左右方向键旋转棋子", True, (255, 0, 0))
            screen.blit(rotate_hint, (20, 180))
            
            # 显示当前拖放位置
            pos_text = self.font.render(f"位置: ({int(self.drag_piece.body.position.x)}, {int(self.drag_piece.body.position.y)})", True, (255, 0, 0))
            screen.blit(pos_text, (20, 210))
        
        # 绘制保存提示
        save_hint = self.font.render("按 S 键保存模型并继续", True, (0, 0, 255))
        screen.blit(save_hint, (self.screen_width - save_hint.get_width() - 20, 60))
        
        # 如果是玩家2的建模阶段，显示"进入战斗"按钮
        if player_name == "玩家2":
            pygame.draw.rect(screen, (255, 100, 100), (self.screen_width - 150, 100, 130, 40))
            battle_text = self.font.render("进入战斗", True, (255, 255, 255))
            screen.blit(battle_text, (self.screen_width - 150 + (130 - battle_text.get_width()) // 2, 
                                   100 + (40 - battle_text.get_height()) // 2))
        
        # 显示已放置棋子的数量和位置信息
        current_model = self.player1_model if player_name == "玩家1" else self.player2_model
        pieces_count = len(current_model.pieces)
        
        # 在底部显示棋子计数
        count_text = self.font.render(f"已放置棋子数量: {pieces_count}", True, (0, 0, 0))
        screen.blit(count_text, (self.screen_width // 2 - count_text.get_width() // 2, self.screen_height - 80))
        
        # 手动绘制每个棋子，确保它们被绘制到屏幕上
        for i, piece in enumerate(current_model.pieces):
            try:
                # 先绘制位置指示线，帮助调试
                if hasattr(piece, 'body') and hasattr(piece.body, 'position'):
                    x, y = int(piece.body.position.x), int(piece.body.position.y)
                    # 垂直指示线到地面
                    pygame.draw.line(screen, (200, 200, 200), (x, y), (x, self.screen_height - 50), 1)
                    # 坐标文本
                    if i < 10:  # 只显示前10个棋子的坐标，避免屏幕拥挤
                        pos_label = self.font.render(f"#{i+1}", True, (100, 100, 100))
                        screen.blit(pos_label, (x - 10, y - 30))
                
                # 绘制棋子
                piece.draw(screen, self.draw_options)
            except Exception as e:
                print(f"绘制棋子 #{i+1} 失败: {e}")
                # 备用方案：如果正常绘制失败，使用简单形状
                if hasattr(piece, 'body') and hasattr(piece.body, 'position'):
                    x, y = int(piece.body.position.x), int(piece.body.position.y)
                    pygame.draw.circle(screen, (255, 0, 0), (x, y), 20)
            
        # 最后绘制正在拖动的棋子，确保它在最上层
        if self.dragging and self.drag_piece:
            # 绘制半透明指示线至地面
            ground_y = self.screen_height - 50
            pos_x = int(self.drag_piece.body.position.x)
            pos_y = int(self.drag_piece.body.position.y)
            pygame.draw.line(screen, (200, 200, 200, 128), (pos_x, pos_y), (pos_x, ground_y), 1)
            
            # 绘制棋子
            try:
                self.drag_piece.draw(screen, self.draw_options)
            except Exception as e:
                print(f"绘制拖动中的棋子出错: {e}")
                # 如果正常绘制失败，尝试直接绘制一个圆形
                pygame.draw.circle(screen, (255, 0, 0), (pos_x, pos_y), 20)
            
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
        self.space.gravity = (0, 50)  # 极小的重力
        self.space.damping = 0.95  # 非常高的阻尼
        
        # 重新创建地面
        self.create_ground()
        
        # 重置玩家模型
        self.player1_model = ChessModel(1)
        self.player2_model = ChessModel(2)
        
        # 重置游戏状态
        self.current_state = GameState.MAIN_MENU
        self.active_player = 1
        self.projectile = None
        
        # 重置拖放状态
        self.dragging = False
        self.drag_piece = None
        self.drag_offset = (0, 0)
        
        print("游戏重置，返回主菜单")

    def prepare_battle_phase(self):
        """准备战斗阶段，重新定位棋子模型并添加引导提示"""
        print("准备战斗阶段...")
        print(f"玩家1模型棋子数: {len(self.player1_model.pieces)}")
        print(f"玩家2模型棋子数: {len(self.player2_model.pieces)}")
        
        # 确保我们不在拖动状态
        self.dragging = False
        self.drag_piece = None
        
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

    def start_dragging(self, x, y):
        """开始拖动一个新棋子"""
        print("=== 开始创建新棋子 ===")
        
        # 确保位置在有效范围内
        if x < 50:
            x = 50
        elif x > self.screen_width - 50:
            x = self.screen_width - 50
            
        if y < 100:
            y = 100
        elif y > self.screen_height - 100:
            y = self.screen_height - 100
        
        # 创建新棋子，但不立即添加到物理空间
        radius = 20  # 基础半径
        chess_type = self.selected_chess_type
        print(f"正在创建类型为 {chess_type.name} 的棋子在位置 ({x}, {y})")
        
        # 确保物理空间存在
        if not hasattr(self, 'space') or self.space is None:
            self.space = pymunk.Space()
            self.space.gravity = (0, 300)
            self.space.damping = 0.85
            print("警告：物理空间不存在，已重新创建")
            
        # 临时创建棋子，但不添加到物理空间
        piece = ChessPiece(x, y, chess_type, self.space, radius=radius, auto_add_to_space=False)
        
        # 手动添加棋子物理对象到空间
        try:
            piece.body.body_type = pymunk.Body.KINEMATIC
            piece.body.velocity = (0, 0)
            
            # 确保棋子没有之前添加过
            try:
                piece.remove_from_space()
            except:
                pass
                
            self.space.add(piece.body, piece.shape)
            print(f"棋子物理对象已添加到空间，当前body类型: {piece.body.body_type}")
        except Exception as e:
            print(f"添加棋子到物理空间失败: {e}")
        
        # 设置拖动状态
        self.dragging = True
        self.drag_piece = piece
        
        # 设置偏移量为0（鼠标点正好在棋子中心）
        self.drag_offset = (0, 0)
        
        print(f"棋子创建成功，类型: {chess_type.name}, 位置: ({x}, {y})")
        
    def stop_dragging(self):
        """停止拖动并放置棋子"""
        if not self.dragging or self.drag_piece is None:
            print("警告：试图停止拖动，但没有正在拖动的棋子")
            return
            
        print("=== 停止拖动并放置棋子 ===")
        
        try:
            # 确保棋子在有效位置（不低于地面）
            y_pos = self.drag_piece.body.position.y
            if y_pos > self.screen_height - 70:  # 如果太靠近地面
                y_pos = self.screen_height - 100  # 向上调整一点
                self.drag_piece.body.position = (self.drag_piece.body.position.x, y_pos)
                
            # 确保棋子不在空中悬浮太高
            if y_pos < 100:
                y_pos = 100
                self.drag_piece.body.position = (self.drag_piece.body.position.x, y_pos)
            
            # 确保不会超出左右边界
            x_pos = self.drag_piece.body.position.x
            if x_pos < 50:
                x_pos = 50
            elif x_pos > self.screen_width - 50:
                x_pos = self.screen_width - 50
                
            self.drag_piece.body.position = (x_pos, y_pos)
            print(f"棋子位置已调整至 ({x_pos}, {y_pos})")
            
            # 获取当前玩家模型
            current_model = self.player1_model if self.current_state == GameState.BUILDING_MODEL_P1 else self.player2_model
            
            # 核心改变：创建一个全新的静态棋子替代当前拖动棋子
            # 这样可以确保棋子不会受物理影响而消失
            new_piece = ChessPiece(
                x_pos, y_pos, 
                self.drag_piece.chess_type,
                self.space,
                radius=20,
                mass=20.0,  # 使用更大的质量
                auto_add_to_space=False
            )
            
            # 复制旋转角度
            new_piece.body.angle = self.drag_piece.body.angle
            
            # 先移除旧棋子
            try:
                self.space.remove(self.drag_piece.body, self.drag_piece.shape)
                print("移除拖动棋子成功")
            except Exception as e:
                print(f"移除拖动棋子失败: {e}")
            
            # 添加新棋子到物理空间
            new_piece.body.velocity = (0, -10)  # 小的向上速度
            new_piece.body.angular_velocity = 0  # 无旋转
            
            try:
                self.space.add(new_piece.body, new_piece.shape)
                print("新棋子已添加到物理空间")
                
                # 将新棋子设为动态
                new_piece.body.body_type = pymunk.Body.DYNAMIC
                
                # 添加到模型中
                current_model.add_piece(new_piece)
                print(f"新棋子已添加到模型，当前模型棋子数: {len(current_model.pieces)}")
                
                # 打印新棋子信息
                print(f"新棋子已放置在 ({int(x_pos)}, {int(y_pos)}), 类型: {new_piece.shape_type}")
            except Exception as e:
                print(f"添加新棋子到物理空间或模型失败: {e}")
            
        except Exception as e:
            print(f"放置棋子过程中出错: {e}")
            
        # 重置拖动状态
        self.dragging = False
        self.drag_piece = None
        self.drag_offset = (0, 0)
        
        # 最终验证
        current_model = self.player1_model if self.current_state == GameState.BUILDING_MODEL_P1 else self.player2_model
        print(f"拖放完成后当前模型棋子数: {len(current_model.pieces)}") 