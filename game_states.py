from enum import Enum
import pygame
import pymunk
import pymunk.pygame_util
import math
from game_objects import ChessPiece, ChessPieceType, Projectile, ChessModel
import sys

# 游戏状态枚举
class GameState(Enum):
    MAIN_MENU = 0
    BUILDING_PHASE = 1
    BATTLE = 3
    GAME_OVER = 4
    RULES = 5

# 游戏管理类
class GameManager:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_state = GameState.MAIN_MENU
        
        # 初始化物理空间
        self.space = pymunk.Space()
        self.space.gravity = (0, 200)  # 进一步增加重力
        self.space.damping = 0.85  # 进一步减小阻尼，使物体运动更流畅
        
        # 创建地面
        self.create_ground()
        
        # 设置碰撞处理
        # 为围棋和地面设置特殊的碰撞处理
        self.space.add_collision_handler(3, 0).begin = self.go_chess_ground_collision_handler
        
        # 玩家模型
        self.player1_model = ChessModel(1)
        self.player2_model = ChessModel(2)
        
        # 当前活动玩家
        self.current_player = 1
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
        self.is_dragging_existing_piece = False
        
        # 游戏胜利者
        self.winner = None
        
        # 游戏界面设置
        self.draw_options = pymunk.pygame_util.DrawOptions(pygame.Surface((1, 1)))
        
        # 初始化支持中文的字体
        try:
            # 使用arialunicode字体，这个字体在系统中支持中文
            self.font = pygame.font.SysFont("arialunicode", 18, bold=False)  # 减小字体并取消粗体
            self.small_font = pygame.font.SysFont("arialunicode", 14, bold=False)  # 更小的字体用于标签等
        except:
            # 如果上述字体不可用，尝试使用系统默认字体
            font_default = pygame.font.get_default_font()
            self.font = pygame.font.Font(font_default, 18)
            self.small_font = pygame.font.Font(font_default, 14)
        
        # 棋子选择
        self.selected_chess_type = ChessPieceType.MILITARY_CHESS
        
        # 棋子数量限制
        self.max_chess_counts = {
            ChessPieceType.MILITARY_CHESS: 5,  # 军棋最大5个
            ChessPieceType.CHINESE_CHESS: 1,   # 象棋最大1个
            ChessPieceType.GO_CHESS: 3         # 围棋最大3个
        }
        # 当前玩家已放置的棋子数量
        self.player1_chess_counts = {
            ChessPieceType.MILITARY_CHESS: 0,
            ChessPieceType.CHINESE_CHESS: 0,
            ChessPieceType.GO_CHESS: 0
        }
        self.player2_chess_counts = {
            ChessPieceType.MILITARY_CHESS: 0,
            ChessPieceType.CHINESE_CHESS: 0,
            ChessPieceType.GO_CHESS: 0
        }
        
        # 提示信息
        self.tip_message = ""
        self.tip_timer = 0
        self.tip_duration = 3000  # 提示显示时间（毫秒）
        
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
        ground_shape.collision_type = 0  # 地面碰撞类型
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
        
    def go_chess_ground_collision_handler(self, arbiter, space, data):
        """围棋与地面的碰撞处理函数"""
        # 获取碰撞的围棋棋子
        go_chess_shape = arbiter.shapes[0]
        ground_shape = arbiter.shapes[1]
        
        # 确保围棋不会穿过地面
        if hasattr(go_chess_shape, 'body'):
            # 获取围棋的位置
            pos = go_chess_shape.body.position
            # 如果围棋位置低于地面，将其拉回地面上方
            if pos.y > self.screen_height - 70:  # 地面位置上方20像素
                go_chess_shape.body.position = pymunk.Vec2d(pos.x, self.screen_height - 70)
                go_chess_shape.body.velocity = pymunk.Vec2d(go_chess_shape.body.velocity.x, 0)
                print("围棋碰撞地面，已调整位置")
        
        # 返回True表示允许碰撞继续处理
        return True
        
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
                
        # 检查提示信息是否过期
        if self.tip_message and pygame.time.get_ticks() - self.tip_timer >= self.tip_duration:
            self.tip_message = ""
        
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
                        
                    # 特殊处理围棋棋子，防止穿过地面
                    if hasattr(piece, 'chess_type') and piece.chess_type == ChessPieceType.GO_CHESS:
                        # 地面位置
                        ground_y = self.screen_height - 50
                        # 如果围棋位置低于地面，将其拉回地面上方
                        if y > ground_y - 20:  # 地面位置上方20像素
                            piece.body.position = (x, ground_y - 20)
                            piece.body.velocity = (piece.body.velocity.x, min(0, piece.body.velocity.y))
                            # 增加一个向上的小力，帮助棋子弹起
                            if piece.body.velocity.y > 0:
                                piece.body.velocity = (piece.body.velocity.x, -50)
                    
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
                    # 主菜单的点击处理由draw_main_menu方法处理
                    pass
                        
                elif self.current_state == GameState.BUILDING_PHASE:
                    # 检查玩家2的"进入战斗"按钮
                    if (self.current_player == 2 and 
                        self.screen_width - 120 <= mouse_pos[0] <= self.screen_width - 20 and
                        70 <= mouse_pos[1] <= 100):
                        # 设置战斗状态
                        self.current_state = GameState.BATTLE
                        self.active_player = 1
                        self.prepare_battle_phase()
                        print("进入战斗阶段")
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
                if self.dragging and self.current_state == GameState.BUILDING_PHASE:
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
                # 考虑拖动偏移
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
            elif event.key == pygame.K_s and self.current_state == GameState.BUILDING_PHASE:
                # 保存当前模型并切换玩家
                if self.current_player == 1:
                    print("玩家1完成建造，切换到玩家2")
                    self.current_player = 2
                else:
                    print("玩家2完成建造，准备进入战斗阶段")
                    self.current_state = GameState.BATTLE
                    # 初始化战斗阶段
                    self.active_player = 1  # 确保玩家1先攻击
                    self.prepare_battle_phase()
                    print("进入战斗阶段")
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
        """绘制游戏场景"""
        # 清除屏幕
        screen.fill((200, 200, 200))
        
        # 根据游戏状态绘制不同内容
        if self.current_state == GameState.MAIN_MENU:
            self.draw_main_menu(screen)
        elif self.current_state == GameState.BUILDING_PHASE:
            player_name = "玩家1" if self.current_player == 1 else "玩家2"
            self.draw_building_phase(screen, player_name)
        elif self.current_state == GameState.BATTLE:
            self.draw_battle_phase(screen)
        elif self.current_state == GameState.GAME_OVER:
            self.draw_game_over(screen)
        elif self.current_state == GameState.RULES:
            self.draw_rules(screen)
            
        # 在任何状态下都显示调试信息和快捷键提示
        debug_info = self.small_font.render(f"当前状态: {self.current_state.name}", True, (100, 100, 100))
        screen.blit(debug_info, (10, self.screen_height - 20))
        
        # 调试绘制模式提示
        debug_text = self.small_font.render("按D键切换调试绘制" if not self.debug_draw else "调试模式开启 (按D关闭)", True, (255, 0, 0) if self.debug_draw else (100, 100, 100))
        screen.blit(debug_text, (self.screen_width - debug_text.get_width() - 10, self.screen_height - 20))
        
        if self.current_state != GameState.BATTLE:
            debug_hint = self.small_font.render("按B键直接进入战斗模式", True, (100, 100, 100))
            screen.blit(debug_hint, (self.screen_width - debug_hint.get_width() - 10, self.screen_height - 40))
            
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
        """绘制游戏主菜单"""
        screen.fill((50, 50, 50))  # 深灰色背景
        
        # 游戏标题
        title = self.font.render("棋子堡垒", True, (255, 255, 255))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 50))
        
        # 创建开始游戏按钮
        pygame.draw.rect(screen, (100, 100, 255), (self.screen_width // 2 - 80, 150, 160, 40))
        start_text = self.small_font.render("开始游戏", True, (255, 255, 255))
        screen.blit(start_text, (self.screen_width // 2 - start_text.get_width() // 2, 158))
        
        # 创建游戏规则按钮
        pygame.draw.rect(screen, (100, 100, 255), (self.screen_width // 2 - 80, 210, 160, 40))
        rules_text = self.small_font.render("游戏规则", True, (255, 255, 255))
        screen.blit(rules_text, (self.screen_width // 2 - rules_text.get_width() // 2, 218))
        
        # 创建退出游戏按钮
        pygame.draw.rect(screen, (100, 100, 255), (self.screen_width // 2 - 80, 270, 160, 40))
        exit_text = self.small_font.render("退出游戏", True, (255, 255, 255))
        screen.blit(exit_text, (self.screen_width // 2 - exit_text.get_width() // 2, 278))
        
        # 检测鼠标点击
        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            # 开始游戏按钮
            if (self.screen_width // 2 - 80 <= mouse_pos[0] <= self.screen_width // 2 + 80 and 
                150 <= mouse_pos[1] <= 190):
                self.current_state = GameState.BUILDING_PHASE
                self.current_player = 1
                
            # 游戏规则按钮
            elif (self.screen_width // 2 - 80 <= mouse_pos[0] <= self.screen_width // 2 + 80 and 
                 210 <= mouse_pos[1] <= 250):
                self.current_state = GameState.RULES
                
            # 退出游戏按钮
            elif (self.screen_width // 2 - 80 <= mouse_pos[0] <= self.screen_width // 2 + 80 and 
                 270 <= mouse_pos[1] <= 310):
                pygame.quit()
                sys.exit()
        
    def draw_building_phase(self, screen, player_name):
        """绘制建造阶段界面"""
        # 绘制玩家标题
        title = self.font.render(f"{player_name}建造阶段", True, (0, 0, 0))
        screen.blit(title, (self.screen_width // 2 - 80, 10))
        
        # 获取当前玩家的棋子计数
        current_chess_counts = self.player1_chess_counts if self.current_player == 1 else self.player2_chess_counts
        
        # 绘制玩家可用的棋子类型
        chess_types = [
            ("军棋(1)", ChessPieceType.MILITARY_CHESS, (40, 40)),
            ("象棋(2)", ChessPieceType.CHINESE_CHESS, (100, 40)),
            ("围棋(3)", ChessPieceType.GO_CHESS, (160, 40))
        ]
        
        for i, (name, chess_type, pos) in enumerate(chess_types):
            # 绘制棋子示例
            if chess_type == ChessPieceType.MILITARY_CHESS:
                # 军棋是长方形
                pygame.draw.rect(screen, (255, 0, 0), (pos[0]-18, pos[1]-11, 36, 22))
            elif chess_type == ChessPieceType.CHINESE_CHESS:
                # 象棋是方形
                pygame.draw.rect(screen, (0, 255, 0), (pos[0]-15, pos[1]-15, 30, 30))
            else:
                # 围棋是三角形
                points = [
                    (pos[0], pos[1]-15),
                    (pos[0]-15, pos[1]+15),
                    (pos[0]+15, pos[1]+15)
                ]
                pygame.draw.polygon(screen, (0, 0, 255), points)
                
            # 绘制名称和剩余数量
            text = self.small_font.render(name, True, (0, 0, 0))
            screen.blit(text, (pos[0]-20, pos[1]+20))
            
            # 显示剩余数量
            remaining = self.max_chess_counts[chess_type] - current_chess_counts[chess_type]
            count_text = self.small_font.render(f"剩余: {remaining}/{self.max_chess_counts[chess_type]}", True, 
                                              (0, 0, 0) if remaining > 0 else (255, 0, 0))
            screen.blit(count_text, (pos[0]-20, pos[1]+35))
            
        # 显示当前选择的棋子类型
        selected_text = self.small_font.render(f"当前选择: {self.selected_chess_type.name}", True, (0, 0, 0))
        screen.blit(selected_text, (20, 80))
        
        # 绘制提示文本
        hint1 = self.small_font.render("拖放棋子到画面中以建造堡垒", True, (0, 0, 0))
        screen.blit(hint1, (20, 100))
        
        hint2 = self.small_font.render("按S键结束当前玩家建造并切换", True, (0, 0, 0))
        screen.blit(hint2, (20, 120))
        
        # 如果是玩家2，显示进入战斗的按钮
        if self.current_player == 2:
            pygame.draw.rect(screen, (255, 100, 100), 
                           (self.screen_width - 120, 70, 100, 30))
            battle_text = self.small_font.render("进入战斗", True, (0, 0, 0))
            screen.blit(battle_text, (self.screen_width - 100, 78))
        
        # 绘制地面
        pygame.draw.line(screen, (0, 0, 0), 
                        (0, self.screen_height - 50), 
                        (self.screen_width, self.screen_height - 50), 5)
                        
        # 绘制玩家棋子
        current_model = self.player1_model if self.current_player == 1 else self.player2_model
        for piece in current_model.pieces:
            piece.draw(screen)
            
        # 如果正在拖动棋子，绘制它
        if self.dragging and self.drag_piece:
            ChessPiece.draw_at_body_position(screen, self.drag_piece, self.drag_piece.chess_type)
            
        # 显示棋子数量
        pieces_count = len(current_model.pieces)
        count_text = self.small_font.render(f"当前棋子数量: {pieces_count}", True, (0, 0, 0))
        screen.blit(count_text, (20, self.screen_height - 30))
        
        # 显示提示信息
        if self.tip_message and pygame.time.get_ticks() - self.tip_timer < self.tip_duration:
            # 创建半透明背景
            tip_surface = pygame.Surface((self.screen_width, 40), pygame.SRCALPHA)
            tip_surface.fill((0, 0, 0, 180))  # 黑色半透明背景
            screen.blit(tip_surface, (0, self.screen_height // 2 - 20))
            
            # 显示提示文本
            tip_text = self.font.render(self.tip_message, True, (255, 255, 255))
            screen.blit(tip_text, (self.screen_width // 2 - tip_text.get_width() // 2, 
                                  self.screen_height // 2 - tip_text.get_height() // 2))
        
    def draw_battle_phase(self, screen):
        """绘制战斗阶段"""
        # 绘制标题
        title = self.font.render(f"玩家{self.active_player}的回合", True, (0, 0, 0))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 10))
        
        # 绘制战斗指导信息
        if not self.charging and not self.projectile:
            guide_text1 = self.font.render("点击鼠标左键开始充能，松开发射笔芯攻击对方模型", True, (0, 0, 255))
            screen.blit(guide_text1, (self.screen_width // 2 - guide_text1.get_width() // 2, 40))
            
            guide_text2 = self.font.render("玩家轮流攻击，直到一方模型散架", True, (0, 0, 255))
            screen.blit(guide_text2, (self.screen_width // 2 - guide_text2.get_width() // 2, 60))
            
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
            
            pygame.draw.rect(screen, (200, 200, 200), (30, 40, 150, 15))
            pygame.draw.rect(screen, (255, 0, 0), (30, 40, int(150 * charge_percent), 15))
            
            charge_text = self.font.render(f"力度: {int(charge_percent * 100)}%", True, (0, 0, 0))
            screen.blit(charge_text, (190, 38))

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
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, self.screen_height // 2 - 60))
        
        # 绘制游戏结果描述
        if self.winner == 1:
            result_text = "玩家1的棋子堡垒坚固稳定，成功击溃了对手的防线!"
        else:
            result_text = "玩家2的棋子堡垒坚固稳定，成功击溃了对手的防线!"
            
        result = self.font.render(result_text, True, (255, 255, 255))
        screen.blit(result, (self.screen_width // 2 - result.get_width() // 2, self.screen_height // 2 - 20))
        
        # 绘制返回主菜单按钮
        pygame.draw.rect(screen, (100, 100, 255), (self.screen_width // 2 - 80, self.screen_height // 2 + 30, 160, 40))
        menu_text = self.font.render("返回主菜单", True, (255, 255, 255))
        screen.blit(menu_text, (self.screen_width // 2 - menu_text.get_width() // 2, 
                              self.screen_height // 2 + 30 + (40 - menu_text.get_height()) // 2))
        
        # 检查点击返回主菜单
        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            if (self.screen_width // 2 - 80 <= mouse_pos[0] <= self.screen_width // 2 + 80 and 
                self.screen_height // 2 + 30 <= mouse_pos[1] <= self.screen_height // 2 + 70):
                self.reset_game()
                
    def reset_game(self):
        """重置游戏到初始状态"""
        # 清除所有物理对象
        self.space = pymunk.Space()
        self.space.gravity = (0, 200)  # 进一步增加重力
        self.space.damping = 0.85  # 进一步减小阻尼，使物体运动更流畅
        
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
        self.is_dragging_existing_piece = False
        
        # 重置棋子计数
        self.player1_chess_counts = {
            ChessPieceType.MILITARY_CHESS: 0,
            ChessPieceType.CHINESE_CHESS: 0,
            ChessPieceType.GO_CHESS: 0
        }
        self.player2_chess_counts = {
            ChessPieceType.MILITARY_CHESS: 0,
            ChessPieceType.CHINESE_CHESS: 0,
            ChessPieceType.GO_CHESS: 0
        }
        
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
        """开始拖动一个棋子，如果点击在已有棋子上则移动该棋子，否则创建新棋子"""
        # 获取当前玩家模型
        current_model = self.player1_model if self.current_player == 1 else self.player2_model
        current_chess_counts = self.player1_chess_counts if self.current_player == 1 else self.player2_chess_counts
        
        # 检查是否点击在已有棋子上
        clicked_piece = None
        for piece in current_model.pieces:
            if hasattr(piece, 'body') and hasattr(piece.body, 'position'):
                # 根据棋子类型计算点击检测范围
                px, py = piece.body.position
                if piece.chess_type == ChessPieceType.MILITARY_CHESS:
                    # 军棋（长方形）
                    width, height = piece.radius*2.5, piece.radius*1.5
                    if (px - width/2 <= x <= px + width/2 and 
                        py - height/2 <= y <= py + height/2):
                        clicked_piece = piece
                        break
                elif piece.chess_type == ChessPieceType.CHINESE_CHESS:
                    # 象棋（方形）
                    size = piece.radius*2
                    if (px - size/2 <= x <= px + size/2 and 
                        py - size/2 <= y <= py + size/2):
                        clicked_piece = piece
                        break
                elif piece.chess_type == ChessPieceType.GO_CHESS:
                    # 围棋（三角形）- 简化为圆形检测
                    if ((x - px)**2 + (y - py)**2 <= piece.radius**2):
                        clicked_piece = piece
                        break
        
        if clicked_piece:
            # 如果点击在已有棋子上，设置为拖动该棋子
            print(f"开始拖动已有棋子，位置: ({x}, {y}), 类型: {clicked_piece.chess_type.name}")
            
            # 从模型中移除该棋子（暂时）
            current_model.pieces.remove(clicked_piece)
            
            # 从计数中减去该棋子（暂时）
            current_chess_counts[clicked_piece.chess_type] -= 1
            
            # 设置为当前拖动的棋子
            self.drag_piece = clicked_piece
            
            # 计算拖动偏移（鼠标位置与棋子中心的差值）
            self.drag_offset = (x - clicked_piece.body.position.x, y - clicked_piece.body.position.y)
            
            # 设置拖动状态
            self.dragging = True
            self.is_dragging_existing_piece = True
        else:
            # 如果点击在空白处，检查是否达到该类型棋子的数量限制
            if current_chess_counts[self.selected_chess_type] >= self.max_chess_counts[self.selected_chess_type]:
                print(f"{self.selected_chess_type.name}已达到最大数量限制({self.max_chess_counts[self.selected_chess_type]}个)")
                # 设置提示信息
                chess_type_names = {
                    ChessPieceType.MILITARY_CHESS: "军棋",
                    ChessPieceType.CHINESE_CHESS: "象棋",
                    ChessPieceType.GO_CHESS: "围棋"
                }
                self.tip_message = f"{chess_type_names[self.selected_chess_type]}棋子已经达到上限。"
                self.tip_timer = pygame.time.get_ticks()
                return
            
            # 创建一个新棋子
            self.drag_piece = ChessPiece(x, y, self.space, self.selected_chess_type)
            
            # 设置拖动偏移
            self.drag_offset = (0, 0)
            
            # 设置拖动状态
            self.dragging = True
            self.is_dragging_existing_piece = False
            
            print(f"开始拖动新棋子，初始位置: ({x}, {y}), 类型: {self.selected_chess_type.name}")

    def stop_dragging(self):
        """结束棋子拖动操作，放置当前拖动中的棋子"""
        print("尝试放置棋子...")
        
        if not self.dragging or not self.drag_piece:
            print("警告：尝试停止已经不存在的拖动操作")
            self.dragging = False
            self.drag_piece = None
            return
            
        # 获取拖放位置
        mouse_pos = pygame.mouse.get_pos()
        
        # 检查是否位于游戏区域内
        if mouse_pos[1] >= self.screen_height - 50:
            # 如果拖到了底部区域，放弃放置该棋子
            print("棋子拖放到底部区域外，放弃放置")
            try:
                if hasattr(self.drag_piece, 'shape') and self.drag_piece.shape in self.space.shapes:
                    self.space.remove(self.drag_piece.shape)
                if self.drag_piece in self.space.bodies:
                    self.space.remove(self.drag_piece.body)
            except Exception as e:
                print(f"移除临时棋子时出错: {e}")
            
            # 如果是拖动已有棋子，需要将其重新添加到模型中
            if hasattr(self, 'is_dragging_existing_piece') and self.is_dragging_existing_piece:
                current_model = self.player1_model if self.current_player == 1 else self.player2_model
                current_model.add_piece(self.drag_piece)
                print(f"已有棋子拖放失败，重新添加到模型中")
            
            self.dragging = False
            self.drag_piece = None
            return
        
        print(f"拖放完成，位置: {mouse_pos}")
        
        # 获取当前玩家模型
        current_model = self.player1_model if self.current_player == 1 else self.player2_model
        current_chess_counts = self.player1_chess_counts if self.current_player == 1 else self.player2_chess_counts
        
        # 区分处理拖动已有棋子和放置新棋子的情况
        if hasattr(self, 'is_dragging_existing_piece') and self.is_dragging_existing_piece:
            # 处理拖动已有棋子的情况
            try:
                # 更新棋子位置
                x, y = mouse_pos
                # 考虑拖动偏移
                adjusted_x = x - self.drag_offset[0]
                adjusted_y = y - self.drag_offset[1]
                
                # 确保位置有效
                if math.isnan(adjusted_x) or math.isnan(adjusted_y):
                    print("警告：检测到无效的棋子位置，重置为鼠标位置")
                    adjusted_x, adjusted_y = x, y
                
                self.drag_piece.body.position = pymunk.Vec2d(adjusted_x, adjusted_y)
                # 设置一个更大的初始向下速度，帮助棋子更快下落
                self.drag_piece.body.velocity = (0, 5.0)
                # 确保棋子处于动态状态
                self.drag_piece.body.body_type = pymunk.Body.DYNAMIC
                
                print(f"已有棋子位置已更新: {self.drag_piece.body.position}")
                
                # 将棋子重新添加到模型中
                current_model.add_piece(self.drag_piece)
                # 更新棋子计数
                current_chess_counts[self.drag_piece.chess_type] += 1
                
                print(f"已有棋子已重新添加到玩家{self.current_player}模型中")
            except Exception as e:
                print(f"更新已有棋子位置时出错: {e}")
                # 出错时也要将棋子重新添加到模型中
                current_model.add_piece(self.drag_piece)
                # 更新棋子计数
                current_chess_counts[self.drag_piece.chess_type] += 1
        else:
            # 处理放置新棋子的情况
            try:
                # 创建一个全新的棋子替代当前拖动棋子
                x, y = mouse_pos
                new_piece = ChessPiece(x, y, self.space, self.selected_chess_type)
                
                # 确保棋子的物理属性正确设置
                # 设置一个更大的初始向下速度，帮助棋子更快下落
                new_piece.body.velocity = (0, 5.0)
                # 确保棋子处于动态状态
                new_piece.body.body_type = pymunk.Body.DYNAMIC
                
                # 确保棋子位置有效（防止NaN值）
                if math.isnan(new_piece.body.position.x) or math.isnan(new_piece.body.position.y):
                    print("警告：检测到无效的棋子位置，重置为鼠标位置")
                    new_piece.body.position = pymunk.Vec2d(x, y)
                
                print(f"新棋子初始位置: {new_piece.body.position}, 初始速度: {new_piece.body.velocity}")
                
                # 把棋子添加到当前玩家的模型中
                current_model.add_piece(new_piece)
                # 更新棋子计数
                current_chess_counts[self.selected_chess_type] += 1
                
                print(f"添加新棋子到玩家{self.current_player}模型，当前模型棋子数: {len(current_model.pieces)}")
                
                # 移除拖动中的临时棋子
                try:
                    if hasattr(self.drag_piece, 'shape') and self.drag_piece.shape in self.space.shapes:
                        self.space.remove(self.drag_piece.shape)
                    if hasattr(self.drag_piece, 'body') and self.drag_piece.body in self.space.bodies:
                        self.space.remove(self.drag_piece.body)
                    print("移除临时拖动棋子")
                except Exception as e:
                    print(f"移除临时拖动棋子时出错: {e}")
            except Exception as e:
                print(f"创建新棋子时出错: {e}")
        
        # 重置拖动状态
        self.dragging = False
        self.drag_piece = None
        self.is_dragging_existing_piece = False
        
        # 最终验证
        current_model = self.player1_model if self.current_player == 1 else self.player2_model
        print(f"拖放完成后当前模型棋子数: {len(current_model.pieces)}")

    def draw_rules(self, screen):
        """绘制游戏规则页面"""
        screen.fill((50, 50, 50))  # 深灰色背景
        
        # 标题
        title = self.font.render("游戏规则", True, (255, 255, 255))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 30))
        
        # 规则内容
        rules = [
            "1. 游戏分为建造和战斗两个阶段",
            "2. 建造阶段：玩家轮流放置棋子，建造自己的堡垒",
            "3. 每个玩家最多可以放置12个棋子",
            "4. 棋子种类：兵(圆形)、车(方形)、马(三角形)",
            "5. 战斗阶段：玩家通过调整发射力度攻击对方堡垒",
            "6. 当任一方堡垒的棋子全部被击落，游戏结束",
            "7. 剩余棋子较多的玩家获胜"
        ]
        
        y_pos = 80
        for rule in rules:
            rule_text = self.small_font.render(rule, True, (255, 255, 255))
            screen.blit(rule_text, (self.screen_width // 2 - 150, y_pos))
            y_pos += 30
        
        # 返回按钮
        pygame.draw.rect(screen, (100, 100, 255), (self.screen_width // 2 - 60, 350, 120, 40))
        back_text = self.small_font.render("返回", True, (255, 255, 255))
        screen.blit(back_text, (self.screen_width // 2 - back_text.get_width() // 2, 358))
        
        # 检测鼠标点击
        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            if (self.screen_width // 2 - 60 <= mouse_pos[0] <= self.screen_width // 2 + 60 and 
                350 <= mouse_pos[1] <= 390):
                self.current_state = GameState.MAIN_MENU 