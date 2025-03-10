import pygame
import sys
from game_states import GameManager, GameState

def main():
    # 初始化pygame
    pygame.init()
    
    # 设置游戏窗口
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("棋子堡垒对战游戏")
    
    # 创建游戏管理器
    game_manager = GameManager(screen_width, screen_height)
    
    # 设置游戏时钟
    clock = pygame.time.Clock()
    
    # 记录前一个游戏状态以检测状态变化
    previous_state = game_manager.current_state
    print(f"游戏启动，初始状态: {previous_state}")
    
    # 游戏主循环
    while True:
        # 检测状态变化
        if game_manager.current_state != previous_state:
            print(f"游戏状态从 {previous_state} 变为 {game_manager.current_state}")
            previous_state = game_manager.current_state
            
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            game_manager.handle_event(event)
            
        # 更新游戏状态
        game_manager.update(1/60.0)  # 60 FPS
        
        # 绘制游戏
        game_manager.draw(screen)
        
        # 更新屏幕
        pygame.display.flip()
        
        # 控制帧率
        clock.tick(60)

if __name__ == "__main__":
    main() 