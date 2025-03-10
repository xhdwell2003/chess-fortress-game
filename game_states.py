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
        self.space.gravity = (0, 50)  # 重力
        self.space.damping = 0.95  # 阻尼
        
        # 创建地面
        self.create_ground()
        
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
        
        # 绘制玩家可用的棋子类型
        chess_types = [
            ("军棋(1)", ChessPieceType.MILITARY_CHESS, (40, 40)),
            ("象棋(2)", ChessPieceType.CHINESE_CHESS, (100, 40)),
            ("围棋(3)", ChessPieceType.GO_CHESS, (160, 40))
        ]
        
        for i, (name, chess_type, pos) in enumerate(chess_types):
            # 绘制棋子示例
            if chess_type == ChessPieceType.MILITARY_CHESS:
                # 军棋是圆形
                pygame.draw.circle(screen, (255, 0, 0), pos, 15)
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
                
            # 绘制名称
            text = self.small_font.render(name, True, (0, 0, 0))
            screen.blit(text, (pos[0]-20, pos[1]+20))
            
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
            ChessPiece.draw_at_body_position(screen, self.drag_piece, self.selected_chess_type)
            
        # 显示棋子数量
        pieces_count = len(current_model.pieces)
        count_text = self.small_font.render(f"当前棋子数量: {pieces_count}", True, (0, 0, 0))
        screen.blit(count_text, (20, self.screen_height - 30))
        
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
        self.space.gravity = (0, 50)  # 重力
        self.space.damping = 0.95  # 阻尼
        
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
        # 创建一个新棋子用于拖动
        self.drag_piece = ChessPiece(x, y, self.space, self.selected_chess_type)
        
        # 设置拖动偏移
        self.drag_offset = (0, 0)
        
        # 设置拖动状态
        self.dragging = True
        
        print(f"开始拖动棋子，初始位置: ({x}, {y}), 类型: {self.selected_chess_type.name}")
        
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
            if self.drag_piece in self.space.bodies:
                print("从物理空间移除临时棋子")
                if self.drag_piece.shape in self.space.shapes:
                    self.space.remove(self.drag_piece.shape)
                self.space.remove(self.drag_piece)
            self.dragging = False
            self.drag_piece = None
            return
        
        print(f"拖放完成，位置: {mouse_pos}")
        
        # 获取当前玩家模型
        current_model = self.player1_model if self.current_player == 1 else self.player2_model
        
        # 核心改变：创建一个全新的静态棋子替代当前拖动棋子
        x, y = mouse_pos
        new_piece = ChessPiece(x, y, self.space, self.selected_chess_type)
        new_piece.body.position = (x, y)
        
        # 为棋子设置物理属性
        new_piece.body.velocity = (0, 0)  # 确保初始速度为零
        print(f"棋子初始位置: {new_piece.body.position}, 初始速度: {new_piece.body.velocity}")
        
        # 把棋子添加到当前玩家的模型中
        current_model.add_piece(new_piece)
        print(f"添加棋子到玩家{self.current_player}模型，当前模型棋子数: {len(current_model.pieces)}")
        
        # 如果拖动中的临时棋子还在物理空间中，移除它
        if self.drag_piece and self.drag_piece in self.space.bodies:
            if hasattr(self.drag_piece, 'shape') and self.drag_piece.shape in self.space.shapes:
                self.space.remove(self.drag_piece.shape)
            self.space.remove(self.drag_piece)
            print("移除临时拖动棋子")
        
        # 重置拖动状态
        self.dragging = False
        self.drag_piece = None
        
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