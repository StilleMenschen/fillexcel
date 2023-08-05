# fillexcel

## 介绍

填充二维数组数据到 Excel 中，可以自定义每个单元格列的填充规则，支持的规则如下

- 固定字符串
- 指定范围的随机数
- 日期时间组成的字符串（带有序号）
- 表达式计算
- 拼接多个列的为一个字符串
- 指定的字符串数组
- 指定的对象字典数组

### 表达式计算

可以计算多个数值单元格的数据，如

```
{A} * {B} + {C} - 5
```

### 拼接多个列的为一个字符串

指定一个连接的字符，如以字符“-”按指定的顺序拼接“A,E,C,E”四个单元格的值

### 指定的字符串数组

按顺序循环填入简单的字符串数组，如一组动物名称：蛇、蝎、虎、豹、鹿

### 指定的对象字典数组

按顺序循环填入自定义字典象数组，如一组星球观测数据：

{"mass": 158.54, "radius": 45, "temperature": "135°C"}、
{"mass": 851.21, "radius": 78, "temperature": "-227°C"}、
{"mass": 581, "radius": 42.254, "temperature": "318°C"}

另外，自定义字段属性对象数组还需要配置绑定，如参考上面的定义，
将 mass 绑定到单元格列 A，将 radius 绑定到单元格列 B

## 主要组件

1. Django
2. Celery
3. xlwings

## 外部服务

1. PostgresSQL
2. RabbitMQ
3. Redis
4. Minio
5. Nginx

## 部署安装

> 运行本项目需要一台额外的 Windows/MacOS 机器，且机器必须已安装 Microsoft Office Excel

### 首先拉取代码

```bash
git clone https://github.com/StilleMenschen/fillexcel.git
cd fillexcel
```

### 启动所有容器

```bash
docker compose up -d --build
```

### 配置 Minio 的访问密钥

1. 访问服务器的端口9001，如`http://192.168.1.1:9001`，分别输入账号 admin 和密码 password
2. 访问左侧菜单 Access Keys，点击按钮 Create access key
3. 将展示的 Access Key 和 secret Key 复制到 fillexcel/configure.ini 中对应 [minio] 下的 access 和 secret
4. 点击 Create，完成

### 前端文件

由于是前后端分离的，前端代码参考对应的仓库 [fillexcel-front](https://github.com/StilleMenschen/fillexcel-front)

前端打包后的文件放置在 web 路径下

### 数据库

首次使用需要初始化数据库，先在 PostgresSQL 中创建一个名为 fillexcel 的数据库，然后在项目根目录下执行合并

```bash
python manage.py migrate
```

> 如果需要初始数据，可以执行脚本 fills/sql/fill_function_define.sql

### 在 Windows/MacOS 机器上启动 Celery

1. 在对应机器上安装 Python 3.11
2. 通过 pip 安装依赖

   ```bash
   pip install -U celery xlwings psycopg2 redis certifi urllib3 minio
   ```

3. 拉取代码

   ```bash
   git clone https://github.com/StilleMenschen/fillexcel.git
   cd fillexcel
   ```

4. 项目根目录下，运行任务接收生成请求

   ```bash
   celery -A fills.tasks worker -l INFO -c 2 -P eventlet
   ```
