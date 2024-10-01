import pymysql

# 连接数据库
connection = pymysql.connect(
    host='localhost',  # 数据库服务器地址，通常为 localhost
    user='rozhao',  # 数据库用户名
    password='z_13777869196',  # 数据库密码
    database='quant',  # 要连接的数据库名称
    port=3306  # 数据库端口号，默认为 3306
)

# 使用 cursor() 方法创建一个游标对象
cursor = connection.cursor()

# 执行 SQL 查询语句
query = "SELECT * FROM test_table"
cursor.execute(query)

# 获取查询结果
results = cursor.fetchall()

# 打印结果
for row in results:
    print(row)

# 关闭游标和连接
cursor.close()
connection.close()