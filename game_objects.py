import pygame
import pymunk
import pymunk.pygame_util
from enum import Enum
import pickle
import os
import math

# 定义棋子类型
class ChessPieceType(Enum):
    MILITARY_CHESS = 1  # 军棋
    CHINESE_CHESS = 2   # 中国象棋
    GO_CHESS = 3        # 围棋

# 棋子基类
class ChessPiece:
    def __init__(self, x, y, space, chess_type, radius=20, mass=10.0):
        self.chess_type = chess_type
        
        # 根据棋子类型创建不同形状和计算正确的惯性矩
        if chess_type == ChessPieceType.MILITARY_CHESS:
            # 军棋（长方形）
            width, height = radius*2.5, radius*1.5
            # 为长方形计算正确的惯性矩
            moment = pymunk.moment_for_box(mass, (width, height))
            self.body = pymunk.Body(mass, moment)
            self.body.position = (x, y)
            self.shape = pymunk.Poly.create_box(self.body, (width, height))
            self.shape_type = "rectangle"
        elif chess_type == ChessPieceType.CHINESE_CHESS:
            # 象棋（方形）
            size = radius*2
            # 为方形计算正确的惯性矩
            moment = pymunk.moment_for_box(mass, (size, size))
            self.body = pymunk.Body(mass, moment)
            self.body.position = (x, y)
            self.shape = pymunk.Poly.create_box(self.body, (size, size))
            self.shape_type = "box"
        elif chess_type == ChessPieceType.GO_CHESS:
            # 围棋（三角形）
            # 为三角形计算惯性矩
            triangle_vertices = [
                (-radius, radius), 
                (radius, radius), 
                (0, -radius)
            ]
            moment = pymunk.moment_for_poly(mass, triangle_vertices, (0, 0))
            self.body = pymunk.Body(mass, moment)
            self.body.position = (x, y)
            self.shape = pymunk.Poly(self.body, triangle_vertices)
            self.shape_type = "triangle"
        
        # 设置物理属性
        self.shape.elasticity = 0.5
        self.shape.friction = 0.9
        self.radius = radius
        
        # 添加到物理空间
        space.add(self.body, self.shape)
    
    @staticmethod
    def draw_at_body_position(screen, piece, chess_type):
        """静态方法，在指定位置绘制棋子"""
        try:
            if piece and hasattr(piece, 'body'):
                # 检查位置是否有效（防止NaN值）
                if (math.isnan(piece.body.position.x) or math.isnan(piece.body.position.y)):
                    print(f"警告：检测到无效的棋子位置: {piece.body.position}")
                    return
                    
                x, y = int(piece.body.position.x), int(piece.body.position.y)
                radius = getattr(piece, 'radius', 20)
                
                if chess_type == ChessPieceType.MILITARY_CHESS:
                    # 军棋（长方形）
                    pygame.draw.rect(screen, (255, 0, 0), 
                                   (x - radius*1.25, y - radius*0.75, radius*2.5, radius*1.5))
                elif chess_type == ChessPieceType.CHINESE_CHESS:
                    # 象棋（方形）
                    pygame.draw.rect(screen, (0, 255, 0), 
                                   (x - radius, y - radius, radius*2, radius*2))
                elif chess_type == ChessPieceType.GO_CHESS:
                    # 围棋（三角形）
                    points = [
                        (x, y - radius),
                        (x - radius, y + radius),
                        (x + radius, y + radius)
                    ]
                    pygame.draw.polygon(screen, (0, 0, 255), points)
        except Exception as e:
            print(f"静态绘制棋子时出错: {e}")
    
    def draw(self, screen):
        """绘制棋子到屏幕上"""
        try:
            if hasattr(self, 'body') and hasattr(self.body, 'position'):
                # 检查位置是否有效（防止NaN值）
                if (math.isnan(self.body.position.x) or math.isnan(self.body.position.y)):
                    print(f"警告：检测到无效的棋子位置: {self.body.position}")
                    return
                
                x, y = int(self.body.position.x), int(self.body.position.y)
                
                if self.chess_type == ChessPieceType.MILITARY_CHESS:
                    # 军棋（长方形）
                    pygame.draw.rect(screen, (255, 0, 0), 
                                   (x - self.radius*1.25, y - self.radius*0.75, 
                                    self.radius*2.5, self.radius*1.5))
                elif self.chess_type == ChessPieceType.CHINESE_CHESS:
                    # 象棋（方形）
                    pygame.draw.rect(screen, (0, 255, 0), 
                                   (x - self.radius, y - self.radius, 
                                    self.radius*2, self.radius*2))
                elif self.chess_type == ChessPieceType.GO_CHESS:
                    # 围棋（三角形）
                    points = [
                        (x, y - self.radius),
                        (x - self.radius, y + self.radius),
                        (x + self.radius, y + self.radius)
                    ]
                    pygame.draw.polygon(screen, (0, 0, 255), points)
        except Exception as e:
            print(f"绘制棋子时出错: {e}")

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
        print(f"创建玩家{player_id}模型")
        
    def add_piece(self, piece):
        """添加一个棋子到模型中"""
        if piece not in self.pieces:
            self.pieces.append(piece)
            print(f"棋子已添加到玩家{self.player_id}模型，当前数量: {len(self.pieces)}")
        else:
            print(f"棋子已经存在于玩家{self.player_id}模型中，当前数量: {len(self.pieces)}")
        
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
            if hasattr(piece, 'body') and hasattr(piece.body, 'position'):
                if piece.body.position.y > ground_y - 50:
                    fallen_count += 1
            else:
                # 如果棋子没有正确的物理属性，视为已掉落
                fallen_count += 1
                
        # 如果超过70%的棋子已散落，则认为模型已被摧毁
        destruction_percent = fallen_count / initial_total if initial_total > 0 else 1.0
        return destruction_percent > 0.7
        
    def draw(self, screen, draw_options=None):
        """绘制所有棋子"""
        pieces_count = 0
        invalid_pieces = []
        
        for i, piece in enumerate(self.pieces):
            try:
                if hasattr(piece, 'draw'):
                    # 检查棋子位置是否有效
                    if hasattr(piece, 'body') and hasattr(piece.body, 'position'):
                        if (math.isnan(piece.body.position.x) or math.isnan(piece.body.position.y)):
                            print(f"警告：检测到无效的棋子位置，跳过绘制: {piece.body.position}")
                            invalid_pieces.append(i)
                            continue
                    
                    # 根据参数数量调用不同版本的draw方法
                    if draw_options is not None:
                        # 尝试使用两个参数的版本
                        try:
                            piece.draw(screen, draw_options)
                        except TypeError:
                            # 如果失败，尝试使用单参数版本
                            piece.draw(screen)
                    else:
                        piece.draw(screen)
                    
                    pieces_count += 1
            except Exception as e:
                print(f"绘制棋子出错: {e}")
                invalid_pieces.append(i)
        
        # 移除无效的棋子（从后向前移除，避免索引问题）
        for i in sorted(invalid_pieces, reverse=True):
            if i < len(self.pieces):
                print(f"移除无效棋子，索引: {i}")
                try:
                    invalid_piece = self.pieces.pop(i)
                    print(f"已从模型中移除无效棋子")
                except Exception as e:
                    print(f"移除无效棋子时出错: {e}")
        
        if pieces_count < len(self.pieces):
            print(f"警告：只成功绘制了{pieces_count}/{len(self.pieces)}个棋子")
    
    def save(self, filename):
        """保存模型状态"""
        model_data = {
            'player_id': self.player_id,
            'pieces': []
        }
        
        # 保存每个棋子的信息，包括形状类型
        for p in self.pieces:
            piece_data = {
                'position': (p.body.position.x, p.body.position.y),
                'chess_type': p.chess_type.value,
                'angle': p.body.angle  # 保存旋转角度
            }
            model_data['pieces'].append(piece_data)
        
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
                for piece_data in model_data['pieces']:
                    try:
                        # 兼容旧格式
                        if isinstance(piece_data, tuple):
                            x, y, chess_type_value = piece_data
                            angle = 0
                        else:
                            x, y = piece_data['position']
                            chess_type_value = piece_data['chess_type']
                            angle = piece_data.get('angle', 0)
                            
                        chess_type = ChessPieceType(chess_type_value)
                        piece = ChessPiece(x, y, space, chess_type)
                        piece.body.angle = angle  # 设置旋转角度
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