import re

# 读取文件
with open('/app/services/content/app/services/recommendation.py', 'r') as f:
    content = f.read()

# 替换所有的状态过滤条件
content = re.sub(
    r'Video\.status == "online"',
    'Video.status.in_(["online", "published"])',
    content
)

# 写回文件
with open('/app/services/content/app/services/recommendation.py', 'w') as f:
    f.write(content)

print('文件修改完成')