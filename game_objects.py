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
    def __init__(self, x, y, space, chess_type, radius=20, mass=20.0, player_id=1):
        self.chess_type = chess_type
        self.player_id = player_id  # 记录棋子属于哪个玩家
        self.position = (x, y)  # 保存初始位置
        self.radius = radius    # 保存半径，用于重建形状
        self.size = radius*2    # 保存尺寸，用于重建形状
        
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
                (-radius*1.2, radius),  # 左下角更宽
                (radius*1.2, radius),   # 右下角更宽
                (0, -radius)            # 顶点不变
            ]
            moment = pymunk.moment_for_poly(mass, triangle_vertices, (0, 0))
            self.body = pymunk.Body(mass, moment)
            self.body.position = (x, y)
            self.shape = pymunk.Poly(self.body, triangle_vertices)
            self.shape_type = "triangle"
        
        # 设置物理属性
        self.shape.elasticity = 0.2  # 进一步降低弹性，减少弹跳
        self.shape.friction = 0.7  # 进一步降低摩擦力，使棋子能够更容易滑动
        
        # 为围棋棋子增加特殊处理，防止穿过地面
        if chess_type == ChessPieceType.GO_CHESS:
            self.shape.friction = 0.9  # 增加围棋的摩擦力
            self.shape.elasticity = 0.1  # 降低围棋的弹性
            # 增加碰撞过滤组，确保围棋与地面正确碰撞
            self.shape.collision_type = 3  # 围棋专用碰撞类型
        
        # 为其他棋子（非围棋）设置玩家相关的碰撞类型
        else:
            # 根据玩家ID设置碰撞类型
            if player_id == 1:
                self.shape.collision_type = 1  # 玩家1的棋子
            else:
                self.shape.collision_type = 2  # 玩家2的棋子
        # 确保棋子是动态的，能够受重力影响
        self.body.body_type = pymunk.Body.DYNAMIC
        
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
                    # 围棋（三角形）- 使用更宽的底部
                    points = [
                        (x, y - radius),
                        (x - radius*1.2, y + radius),
                        (x + radius*1.2, y + radius)
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
                    # 围棋（三角形）- 使用更宽的底部
                    points = [
                        (x, y - self.radius),
                        (x - self.radius*1.2, y + self.radius),
                        (x + self.radius*1.2, y + self.radius)
                    ]
                    pygame.draw.polygon(screen, (0, 0, 255), points)
        except Exception as e:
            print(f"绘制棋子时出错: {e}")

# 弹射物（铅笔）
class Projectile:
    def __init__(self, x, y, space, radius=5, mass=0.5):
        # 创建一个长方形的物理体，模拟铅笔形状
        self.length = 30  # 铅笔长度
        self.width = 8    # 铅笔宽度
        moment = pymunk.moment_for_box(mass, (self.length, self.width))
        self.body = pymunk.Body(mass, moment)
        self.body.position = x, y
        
        # 初始状态下设置为动态，允许自由落体
        self.body.body_type = pymunk.Body.DYNAMIC
        
        # 创建铅笔形状（长方形）
        self.shape = pymunk.Poly.create_box(self.body, (self.length, self.width))
        self.shape.elasticity = 0.5  # 降低弹性，防止过度弹跳
        self.shape.friction = 0.8    # 增加摩擦力，使其更稳定
        
        # 设置碰撞类型，用于与地面的碰撞处理
        self.shape.collision_type = 4  # 弹射物碰撞类型
        self.projectile_collision_type = 4  # 保存碰撞类型为属性，方便游戏管理器使用
        
        # 设置碰撞过滤器，确保与地面和棋子正确碰撞
        self.shape.filter = pymunk.ShapeFilter(
            categories=0x8,  # 弹射物类别
            mask=0x4 | 0x1 | 0x2 | 0x3  # 地面、玩家1、玩家2和围棋类别
        )
        
        # 铅笔颜色
        self.pencil_color = (255, 215, 0)  # 金黄色铅笔
        self.tip_color = (50, 50, 50)      # 深灰色笔尖
        
        # 添加到物理空间
        space.add(self.body, self.shape)
    
    def apply_impulse(self, direction, strength):
        """施加冲量以发射弹射物"""
        try:
            # 确保弹射物是动态的
            if self.body.body_type != pymunk.Body.DYNAMIC:
                self.body.body_type = pymunk.Body.DYNAMIC
            
            # 检查方向向量是否有效
            if math.isnan(direction.x) or math.isnan(direction.y):
                print("警告：发射方向包含NaN值，使用默认方向")
                direction = pymunk.Vec2d(1, 0)  # 默认向右发射
            
            # 确保方向向量不为零
            if direction.length < 0.001:
                print("警告：发射方向向量接近零，使用默认方向")
                direction = pymunk.Vec2d(1, 0)  # 默认向右发射
            else:
                # 标准化方向向量
                direction = direction.normalized()
            
            # 设置铅笔的角度与发射方向一致
            angle = math.atan2(direction.y, direction.x)
            self.body.angle = angle
            
            # 使用world_point而不是local_point来施加冲量，确保方向正确
            self.body.apply_impulse_at_world_point(direction * strength, self.body.position)
            print(f"成功发射弹射物，方向: ({direction.x:.2f}, {direction.y:.2f})，强度: {strength}")
        except Exception as e:
            print(f"施加冲量时出错: {e}")
        
    def apply_impulse_old(self, direction, strength):
        """旧的施加冲量方法（保留用于参考）"""
        try:
            # 确保弹射物是动态的
            if self.body.body_type != pymunk.Body.DYNAMIC:
                self.body.body_type = pymunk.Body.DYNAMIC
            
            # 检查方向向量是否有效
            if math.isnan(direction.x) or math.isnan(direction.y):
                print("警告：发射方向包含NaN值，使用默认方向")
                direction = pymunk.Vec2d(1, 0)  # 默认向右发射
            else:
                # 标准化方向向量
                direction = direction.normalized()
            
            # 设置铅笔的角度，使笔尖朝向发射方向
            angle = math.atan2(direction.y, direction.x)
            self.body.angle = angle
            # 确保强度有效
            if math.isnan(strength) or strength <= 0:
                print("警告：发射强度无效，使用默认强度")
                strength = 500  # 默认强度
            
            # 施加冲量
            self.body.apply_impulse_at_local_point(direction * strength)
            print(f"成功发射弹射物，方向: ({direction.x:.2f}, {direction.y:.2f})，强度: {strength}")
        except Exception as e:
            print(f"施加冲量时出错: {e}")
        
    def draw(self, screen, draw_options=None):
        """绘制铅笔形状的弹射物"""
        try:
            if hasattr(self, 'body') and hasattr(self.body, 'position'):
                # 检查位置是否有效
                if math.isnan(self.body.position.x) or math.isnan(self.body.position.y):
                    print("警告：检测到无效的弹射物位置")
                    return
                    
                # 获取铅笔的位置和角度
                x, y = int(self.body.position.x), int(self.body.position.y)
                angle = self.body.angle
                
                # 计算铅笔的四个角点
                half_length = self.length / 2
                half_width = self.width / 2
                
                # 铅笔主体的四个角点（顺时针）
                points = [
                    (-half_length, -half_width),
                    (half_length, -half_width),
                    (half_length, half_width),
                    (-half_length, half_width)
                ]
                
                # 旋转并平移点
                rotated_points = []
                for px, py in points:
                    # 旋转
                    rx = px * math.cos(angle) - py * math.sin(angle)
                    ry = px * math.sin(angle) + py * math.cos(angle)
                    # 平移
                    rotated_points.append((x + rx, y + ry))
                
                # 绘制铅笔主体
                pygame.draw.polygon(screen, self.pencil_color, rotated_points)
                
                # 绘制笔尖（三角形）
                tip_length = half_length * 0.3
                tip_points = [
                    (half_length, 0),
                    (half_length + tip_length, -half_width * 0.5),
                    (half_length + tip_length, half_width * 0.5)
                ]
                
                # 旋转并平移笔尖点
                rotated_tip_points = []
                for px, py in tip_points:
                    # 旋转
                    rx = px * math.cos(angle) - py * math.sin(angle)
                    ry = px * math.sin(angle) + py * math.cos(angle)
                    # 平移
                    rotated_tip_points.append((x + rx, y + ry))
                
                # 绘制笔尖
                pygame.draw.polygon(screen, self.tip_color, rotated_tip_points)
        except Exception as e:
            print(f"绘制弹射物时出错: {e}")

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
            
            # 确保棋子知道它属于哪个玩家
            piece.player_id = self.player_id
            
            # 确保碰撞类型正确
            if hasattr(piece, 'shape') and piece.chess_type != ChessPieceType.GO_CHESS:
                # 根据玩家ID设置对应的碰撞类型(保留围棋的特殊类型)
                if self.player_id == 1:
                    piece.shape.collision_type = 1  # 玩家1的棋子
                else:
                    piece.shape.collision_type = 2  # 玩家2的棋子
                    
                # 打印详细信息以便调试
                if piece.chess_type == ChessPieceType.GO_CHESS:
                    print(f"围棋碰撞类型保持为: {piece.shape.collision_type}")
                print(f"设置棋子碰撞类型为: {piece.shape.collision_type}, 玩家ID: {self.player_id}")
            print(f"棋子已添加到玩家{self.player_id}模型，当前数量: {len(self.pieces)}")
        else:
            print(f"棋子已经存在于玩家{self.player_id}模型中，当前数量: {len(self.pieces)}")
        
    def is_destroyed(self):
        """检查模型是否被完全摧毁（所有棋子都散落在地面以上一定高度）"""
        if not self.pieces:  # 如果没有棋子，认为模型已摧毁
            return True
    
        return self.get_destruction_percentage() > 0.7
            
    def get_destruction_percentage(self):
        """计算模型被摧毁的百分比"""
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
                
        # 返回散落的棋子比例
        return fallen_count / initial_total if initial_total > 0 else 1.0
    
    def is_chinese_chess_isolated(self, space):
        """检查象棋是否与本方其他棋子都不接触
        
        Args:
            space: pymunk物理空间，用于检测碰撞
            
        Returns:
            bool: 如果象棋与其他本方棋子都不接触，返回True；否则返回False
        """
        # 首先找到象棋棋子
        chinese_chess = None
        other_pieces = []
        
        # 计算初始完好的棋子数量
        ground_y = 500  # 假设500是地面位置
        initial_total = len(self.pieces)
        fallen_count = 0
        
        for piece in self.pieces:
            # 检查棋子是否已掉落或靠近地面
            if hasattr(piece, 'chess_type'):
                if piece.chess_type == ChessPieceType.CHINESE_CHESS:
                    chinese_chess = piece
                else:
                    other_pieces.append(piece)
            else:
                print(f"警告：棋子没有chess_type属性")
        
        # 如果没有找到象棋，则认为没有象棋或者象棋已经掉落（按照规则应该已经输了）
        if not chinese_chess or not hasattr(chinese_chess, 'shape'):
            print(f"玩家{self.player_id}的象棋不存在或无效")
            return True
            
        # 如果没有其他棋子，象棋肯定是孤立的
        if not other_pieces:
            print(f"玩家{self.player_id}没有非象棋棋子，象棋被认为是孤立的")
            return True
            
        # 检查象棋是否与其他本方棋子接触
        for other in other_pieces:
            if hasattr(other, 'shape') and hasattr(other.body, 'position'):
                # 使用pymunk的碰撞检测功能来判断两个棋子是否接触
                if space.shape_query(chinese_chess.shape):
                    query_result = space.shape_query(chinese_chess.shape)
                    for contact in query_result:
                        if contact.shape == other.shape:
                            print(f"玩家{self.player_id}的象棋与其他棋子接触")
                            return False  # 有接触，不孤立
        
        print(f"玩家{self.player_id}的象棋孤立")
        return True  # 没有接触，孤立

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
            
            # 打印加载的模型信息
            print(f"从{filename}.model加载模型，玩家ID: {model.player_id}")
            
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
                        
                        # 明确使用模型的player_id创建棋子
                        player_id = model.player_id
                        piece = ChessPiece(x, y, space, chess_type, player_id=player_id)
                        
                        # 直接设置正确的碰撞类型
                        if chess_type == ChessPieceType.GO_CHESS:
                            piece.shape.collision_type = 3  # 围棋特殊类型
                        else:
                            piece.shape.collision_type = player_id  # 根据玩家ID设置
                        
                        # 打印调试信息
                        print(f"加载棋子: 类型={chess_type.name}, 玩家ID={player_id}, 碰撞类型={piece.shape.collision_type}")
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