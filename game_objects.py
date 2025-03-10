import pygame
import pymunk
import pymunk.pygame_util
from enum import Enum
import pickle
import os

# 定义棋子类型
class ChessPieceType(Enum):
    MILITARY_CHESS = 1  # 军棋
    CHINESE_CHESS = 2   # 中国象棋
    GO_CHESS = 3        # 围棋

# 棋子基类
class ChessPiece:
    def __init__(self, x, y, chess_type, space, radius=20, mass=1.0):
        self.chess_type = chess_type
        self.body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
        self.body.position = x, y
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 0.8
        self.shape.friction = 0.5
        
        # 设置不同类型棋子的颜色和物理属性
        if chess_type == ChessPieceType.MILITARY_CHESS:
            self.color = (0, 150, 0)  # 绿色
            self.shape.elasticity = 0.7
            self.shape.friction = 0.6
            self.radius = radius * 1.2
        elif chess_type == ChessPieceType.CHINESE_CHESS:
            self.color = (150, 0, 0)  # 红色
            self.shape.elasticity = 0.8
            self.shape.friction = 0.5
            self.radius = radius
        else:  # GO_CHESS
            self.color = (0, 0, 0) if pygame.time.get_ticks() % 2 == 0 else (255, 255, 255)  # 黑色或白色
            self.shape.elasticity = 0.9
            self.shape.friction = 0.4
            self.radius = radius * 0.8
            
        space.add(self.body, self.shape)
        
    def draw(self, screen, draw_options):
        # 绘制棋子主体
        pygame.draw.circle(screen, self.color, 
                          (int(self.body.position.x), int(self.body.position.y)), 
                          int(self.radius))
        
        # 绘制棋子边缘
        pygame.draw.circle(screen, (50, 50, 50), 
                          (int(self.body.position.x), int(self.body.position.y)), 
                          int(self.radius), 2)

# 弹射物（圆珠笔芯）
class Projectile:
    def __init__(self, x, y, space, radius=5, mass=0.5):
        self.body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
        self.body.position = x, y
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 0.95
        self.shape.friction = 0.2
        self.color = (0, 0, 255)  # 蓝色
        self.radius = radius
        space.add(self.body, self.shape)
        
    def apply_impulse(self, direction, strength):
        """施加冲量以发射弹射物"""
        self.body.apply_impulse_at_local_point(direction * strength)
        
    def draw(self, screen, draw_options):
        pygame.draw.circle(screen, self.color, 
                          (int(self.body.position.x), int(self.body.position.y)), 
                          self.radius)

# 模型/堡垒类
class ChessModel:
    def __init__(self, player_id):
        self.pieces = []
        self.player_id = player_id
        
    def add_piece(self, piece):
        self.pieces.append(piece)
        
    def is_destroyed(self):
        """检查模型是否被完全摧毁（所有棋子都散落在地面以上一定高度）"""
        if not self.pieces:  # 如果没有棋子，认为模型已摧毁
            return True
            
        # 计算初始完好的棋子数量
        ground_y = 500  # 假设500是地面位置
        initial_total = len(self.pieces)
        fallen_count = 0
        
        for piece in self.pieces:
            # 检查棋子是否已掉落或靠近地面
            if piece.body.position.y > ground_y - 50:
                fallen_count += 1
                
        # 如果超过70%的棋子已散落，则认为模型已被摧毁
        destruction_percent = fallen_count / initial_total
        return destruction_percent > 0.7
    
    def save(self, filename):
        """保存模型状态"""
        model_data = {
            'player_id': self.player_id,
            'pieces': [(p.body.position.x, p.body.position.y, p.chess_type.value) for p in self.pieces]
        }
        
        try:
            with open(f"{filename}.model", "wb") as f:
                pickle.dump(model_data, f)
            print(f"模型已保存到 {filename}.model 文件，包含 {len(self.pieces)} 个棋子")
            return True
        except Exception as e:
            print(f"保存模型失败: {e}")
            return False
            
    @classmethod
    def load(cls, filename, space):
        """加载模型状态"""
        try:
            if not os.path.exists(f"{filename}.model"):
                print(f"无法找到模型文件: {filename}.model")
                return None
                
            with open(f"{filename}.model", "rb") as f:
                model_data = pickle.load(f)
                
            model = ChessModel(model_data['player_id'])
            
            if 'pieces' in model_data and len(model_data['pieces']) > 0:
                for x, y, chess_type_value in model_data['pieces']:
                    try:
                        chess_type = ChessPieceType(chess_type_value)
                        piece = ChessPiece(x, y, chess_type, space)
                        model.add_piece(piece)
                    except Exception as e:
                        print(f"加载棋子失败: {e}")
                
                print(f"从 {filename}.model 成功加载了 {len(model.pieces)} 个棋子")
                return model
            else:
                print(f"模型文件 {filename}.model 没有包含棋子数据")
                return None
        except Exception as e:
            print(f"加载模型失败: {e}")
            return None 