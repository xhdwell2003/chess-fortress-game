import pygame
import sys

def test_fonts():
    pygame.init()
    
    # 创建窗口
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("中文字体测试")
    
    # 获取系统中所有可用字体
    all_fonts = pygame.font.get_fonts()
    print(f"系统中有 {len(all_fonts)} 个可用字体")
    
    # 测试这些字体
    test_text = "测试中文字体 - 棋子堡垒对战游戏"
    font_size = 24
    y_position = 20
    
    # 背景颜色
    screen.fill((255, 255, 255))
    
    # 测试一些常见的中文字体名称
    chinese_font_names = ["Microsoft YaHei", "SimHei", "STHeiti", "Heiti SC", "PingFang SC", 
                         "STFangsong", "STKAITI", "Microsoft JhengHei", "Arial Unicode MS",
                         "simsun", "nsimsun", "fangsong", "kaiti"]
    
    available_fonts = []
    
    for font_name in chinese_font_names:
        try:
            font = pygame.font.SysFont(font_name, font_size)
            text = font.render(f"{font_name}: {test_text}", True, (0, 0, 0))
            screen.blit(text, (20, y_position))
            y_position += 30
            available_fonts.append(font_name)
            print(f"成功加载字体: {font_name}")
        except:
            print(f"无法加载字体: {font_name}")
    
    # 使用默认字体尝试渲染中文
    default_font = pygame.font.get_default_font()
    print(f"默认字体: {default_font}")
    default_font_obj = pygame.font.Font(default_font, font_size)
    default_text = default_font_obj.render(f"默认字体: {test_text}", True, (0, 0, 0))
    screen.blit(default_text, (20, y_position))
    
    # 使用系统字体列表中的前几个字体
    y_position += 60
    for i, font_name in enumerate(all_fonts[:10]):
        try:
            font = pygame.font.SysFont(font_name, font_size)
            text = font.render(f"{font_name}: {test_text}", True, (0, 0, 0))
            screen.blit(text, (20, y_position))
            y_position += 30
            print(f"系统字体 {i+1}: {font_name}")
        except:
            print(f"无法加载系统字体 {i+1}: {font_name}")
    
    pygame.display.flip()
    
    # 将可用的中文字体打印出来，方便用户查看
    print("\n可用的中文字体:")
    for font in available_fonts:
        print(font)
    
    # 等待用户关闭窗口
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    test_fonts() 