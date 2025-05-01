import pandas as pd
from backend.extensions import neo4j


def export_tasks_to_csv(output_file):
    """
    将知识图谱中的Task节点信息导出到CSV文件，排除required_resources属性

    参数:
        output_file: 输出CSV文件路径
    """
    try:
        # 1. 查询所有Task节点
        query = """
        MATCH (t:Task)
        RETURN t
        """
        results = neo4j.graph.run(query).data()

        if not results:
            print("没有找到Task节点")
            return

        # 2. 提取节点属性并过滤掉required_resources
        tasks_data = []
        for record in results:
            task = record['t']
            # 获取所有属性并转换为字典
            task_dict = dict(task)
            # 移除不需要的属性
            task_dict.pop('required_resources', None)
            tasks_data.append(task_dict)

        # 3. 创建DataFrame并保存为CSV
        df = pd.DataFrame(tasks_data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"成功导出{len(df)}条任务数据到 {output_file}")

    except Exception as e:
        print(f"导出任务数据失败: {str(e)}")
        raise


# 使用示例
export_tasks_to_csv("E:/py_prjs/flask3/frontend/src/assets/tasks_export.csv")