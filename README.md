# MiBoyDaily
利用小米人在传感器实现每日自动化

## 需要

1. 小米人在传感器
2. 小爱音箱 Pro 用来作为蓝牙 mesh
3, 你想用的任何小米能连接蓝牙的设备

## 安装

1. install pdm
2. pdm install
3. export GitHub Token -> 参考[巧妙利用 iOS 的快捷指令配合 GitHub Actions 实现自动化](https://github.com/yihong0618/gitblog/issues/198)来配置你的 Actions
4. 参考 [Miservice](https://github.com/yihong0618/MiService) 拿到人在传感器和小爱 Pro 的 did
5. 更改代码的 schedule 自行添加 task
6. pdm run miboy_daily.py


