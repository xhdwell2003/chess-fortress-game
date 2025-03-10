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
    def __init__(self, x, y, chess_type, space, radius=20, mass=10.0, auto_add_to_space=True):
        self.chess_type = chess_type
        self.shape_type = None  # 形状类型：'circle', 'rect', 'square'
        self.color = None
        self.space = space  # 保存对物理空间的引用
        self.is_static = False  # 是否为静态棋子
        
        # 设置不同类型棋子的形状、颜色和物理属性
        if chess_type == ChessPieceType.MILITARY_CHESS:
            # 军棋：长方形
            width, height = radius * 2.2, radius * 1.2
            moment = pymunk.moment_for_box(mass, (width, height))
            self.body = pymunk.Body(mass, moment)
            self.body.position = x, y
            self.shape = pymunk.Poly.create_box(self.body, (width, height))
            self.color = (0, 150, 0)  # 绿色
            self.shape.elasticity = 0.3  # 降低弹性
            self.shape.friction = 0.9  # 增加摩擦力
            self.width = width
            self.height = height
            self.shape_type = 'rect'
            
        elif chess_type == ChessPieceType.CHINESE_CHESS:
            # 象棋：正方形
            size = radius * 1.8
            moment = pymunk.moment_for_box(mass, (size, size))
            self.body = pymunk.Body(mass, moment)
            self.body.position = x, y
            self.shape = pymunk.Poly.create_box(self.body, (size, size))
            self.color = (150, 0, 0)  # 红色
            self.shape.elasticity = 0.4
            self.shape.friction = 0.8
            self.size = size
            self.shape_type = 'square'
            
        else:  # GO_CHESS
            # 围棋：圆形
            self.body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
            self.body.position = x, y
            self.shape = pymunk.Circle(self.body, radius)
            self.color = (0, 0, 0) if pygame.time.get_ticks() % 2 == 0 else (255, 255, 255)  # 黑色或白色
            self.shape.elasticity = 0.5
            self.shape.friction = 0.7
            self.radius = radius * 0.8
            self.shape_type = 'circle'
        
        # 设置碰撞类型和组，确保棋子之间可以正常碰撞
        self.shape.collision_type = 1
        
        # 防止棋子飞出屏幕，增加碰撞回调函数
        def limit_velocity(body, gravity, damping, dt):
            max_velocity = 500  # 最大速度限制
            if body.velocity.length > max_velocity:
                scale = max_velocity / body.velocity.length
                body.velocity = body.velocity * scale
                
            # 限制最大角速度
            max_angular_velocity = 5.0  # 最大角速度限制
            if abs(body.angular_velocity) > max_angular_velocity:
                body.angular_velocity = max_angular_velocity * (1 if body.angular_velocity > 0 else -1)
                
            # 正常的速度更新
            pymunk.Body.update_velocity(body, gravity, damping, dt)
            
        # 应用速度限制函数
        self.body.velocity_func = limit_velocity
            
        # 只有在auto_add_to_space为True时才添加到物理空间
        if auto_add_to_space and space is not None:
            try:
                space.add(self.body, self.shape)
                print(f"棋子已自动添加到物理空间，类型: {chess_type.name}")
            except Exception as e:
                print(f"自动添加棋子到物理空间失败: {e}")
        
    def make_static(self):
        """将棋子转为静态，不再受物理影响"""
        if not self.is_static and self.space is not None:
            try:
                # 移除当前body
                self.space.remove(self.body, self.shape)
                
                # 创建一个静态body
                static_body = pymunk.Body(body_type=pymunk.Body.STATIC)
                static_body.position = self.body.position
                static_body.angle = self.body.angle
                
                # 创建对应的shape
                if self.shape_type == 'rect':
                    static_shape = pymunk.Poly.create_box(static_body, (self.width, self.height))
                elif self.shape_type == 'square':
                    static_shape = pymunk.Poly.create_box(static_body, (self.size, self.size))
                else:  # circle
                    static_shape = pymunk.Circle(static_body, self.radius)
                
                # 复制物理属性
                static_shape.elasticity = self.shape.elasticity
                static_shape.friction = self.shape.friction
                static_shape.collision_type = self.shape.collision_type
                
                # 添加到空间
                self.space.add(static_body, static_shape)
                
                # 更新引用
                self.body = static_body
                self.shape = static_shape
                self.is_static = True
                
                print("棋子转为静态成功")
                return True
            except Exception as e:
                print(f"转为静态失败: {e}")
                return False
        return False
    
    def add_to_space(self):
        """显式地将棋子添加到物理空间"""
        if self.space:
            try:
                self.space.add(self.body, self.shape)
                return True
            except Exception as e:
                print(f"添加棋子到空间失败: {e}")
                return False
        return False
    
    def remove_from_space(self):
        """从物理空间中移除棋子"""
        if self.space:
            try:
                self.space.remove(self.body, self.shape)
                return True
            except Exception as e:
                print(f"从空间移除棋子失败: {e}")
                return False
        return False
        
    def draw(self, screen, draw_options):
        # 根据形状类型绘制棋子
        try:
            if self.shape_type == 'circle':
                # 绘制圆形棋子(围棋)
                try:
                    pygame.draw.circle(screen, self.color, 
                                     (int(self.body.position.x), int(self.body.position.y)), 
                                     int(self.radius))
                    
                    # 绘制棋子边缘
                    pygame.draw.circle(screen, (50, 50, 50), 
                                     (int(self.body.position.x), int(self.body.position.y)), 
                                     int(self.radius), 2)
                except (ValueError, TypeError):
                    # 忽略无效的坐标值
                    pass
            
            elif self.shape_type == 'rect':
                # 绘制长方形棋子(军棋)
                try:
                    # 计算四个角的坐标，考虑旋转角度
                    vertices = self.shape.get_vertices()
                    points = []
                    valid_points = True
                    
                    for v in vertices:
                        # 从局部坐标转换为全局坐标
                        point = v.rotated(self.body.angle) + self.body.position
                        if math.isnan(point.x) or math.isnan(point.y):
                            # 跳过无效坐标
                            valid_points = False
                            break
                        points.append((int(point.x), int(point.y)))
                        
                    # 绘制填充多边形和边框
                    if valid_points and len(points) >= 3:
                        pygame.draw.polygon(screen, self.color, points)
                        pygame.draw.polygon(screen, (50, 50, 50), points, 2)
                    else:
                        # 如果点无效，退回到简单的矩形绘制
                        x, y = int(self.body.position.x), int(self.body.position.y)
                        pygame.draw.rect(screen, self.color, (x - int(self.width/2), y - int(self.height/2), 
                                                          int(self.width), int(self.height)))
                except (ValueError, TypeError, AttributeError):
                    # 忽略无效的坐标值
                    try:
                        # 退回到简单矩形
                        x, y = int(self.body.position.x), int(self.body.position.y)
                        pygame.draw.rect(screen, self.color, (x - int(self.width/2), y - int(self.height/2), 
                                                          int(self.width), int(self.height)))
                    except:
                        pass
                
            elif self.shape_type == 'square':
                # 绘制正方形棋子(象棋)
                try:
                    vertices = self.shape.get_vertices()
                    points = []
                    valid_points = True
                    
                    for v in vertices:
                        point = v.rotated(self.body.angle) + self.body.position
                        if math.isnan(point.x) or math.isnan(point.y):
                            # 跳过无效坐标
                            valid_points = False
                            break
                        points.append((int(point.x), int(point.y)))
                        
                    # 绘制填充多边形和边框
                    if valid_points and len(points) >= 3:
                        pygame.draw.polygon(screen, self.color, points)
                        pygame.draw.polygon(screen, (50, 50, 50), points, 2)
                    else:
                        # 如果点无效，退回到简单的矩形绘制
                        x, y = int(self.body.position.x), int(self.body.position.y)
                        pygame.draw.rect(screen, self.color, (x - int(self.size/2), y - int(self.size/2), 
                                                          int(self.size), int(self.size)))
                except (ValueError, TypeError, AttributeError):
                    # 忽略无效的坐标值
                    try:
                        # 退回到简单矩形
                        x, y = int(self.body.position.x), int(self.body.position.y)
                        pygame.draw.rect(screen, self.color, (x - int(self.size/2), y - int(self.size/2), 
                                                          int(self.size), int(self.size)))
                    except:
                        pass
        except Exception as e:
            # 捕获所有可能的绘制错误
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
        
    def draw(self, screen, draw_options):
        """绘制所有棋子"""
        pieces_count = 0
        for piece in self.pieces:
            try:
                if hasattr(piece, 'draw'):
                    piece.draw(screen, draw_options)
                    pieces_count += 1
            except Exception as e:
                print(f"绘制棋子出错: {e}")
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
                        piece = ChessPiece(x, y, chess_type, space)
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