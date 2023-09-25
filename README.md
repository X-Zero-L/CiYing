# CiYing

## 简介

- 适用于[HoshinoBot](https://github.com/Ice9Coffee/HoshinoBot)的词影游戏插件
- [游戏源网站](https://cy.surprising.studio/)

## 部署

- 在`hoshino/modules`下执行：

    ```shell
    git clone https://github.com/X-Zero-L/CiYing.git
    ```

- 安装依赖

    ```shell
    pip install playwright
    playwright install
    ```

- 在`hoshino/config/__bot__.py`中加入`CiYing`模块

    ```python
    MODULES_ON = {
        ...
        'CiYing',# 词影游戏
        ...
    }
    ```

- 重启bot

## 使用

- `CY|词影 四字成语`:开始游戏
- `CY|词影 reset`:重置游戏
- `CY|词影 show`:查看当前游戏状态

