# 棋子堡垒对战游戏

这是一个基于物理引擎的双人对战游戏，玩家可以使用军棋、中国象棋和围棋棋子搭建堡垒模型，然后轮流用"圆珠笔芯"攻击对方模型，直到一方模型完全散架。

## 功能特点

- 使用真实物理引擎模拟棋子的物理属性和碰撞
- 支持使用军棋、中国象棋和围棋棋子搭建模型
- 可以保存和加载已创建的模型
- 双人回合制对战
- 直观的图形界面

## 安装与运行

1. 安装依赖：
```
pip install -r requirements.txt
```

2. 运行游戏：
```
python main.py
```

## 游戏规则

1. 玩家轮流使用棋子搭建自己的堡垒模型
2. 完成搭建后，玩家轮流用圆珠笔芯（游戏中模拟为小球）攻击对方模型
3. 当一方模型完全散架时，另一方获胜 