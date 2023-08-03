#!/usr/bin/env bash
# 合并数据库
python manage.py migrate
# 创建数据库合并脚本
python manage.py makemigrations fills
# 查看一个合并脚本实际会执行的 SQL 语句
python manage.py sqlmigrate fills 0001
# 进入 Django 的 REPL
python manage.py shell
# 创建 admin 账户
python manage.py createsuperuser
# 本地启动开发服务
python manage.py runserver 4200
