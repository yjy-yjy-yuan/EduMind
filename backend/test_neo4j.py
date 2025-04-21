"""测试Neo4j数据库连接"""
import logging
from neo4j import GraphDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Neo4j连接配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "cjx20040328"

def test_connection():
    """测试Neo4j数据库连接"""
    try:
        # 创建Neo4j驱动
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        # 测试连接
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS count")
            count = result.single()["count"]
            logger.info(f"数据库中共有 {count} 个节点")
            
            # 创建测试节点
            session.run(
                """
                MERGE (t:Test {name: "测试节点"})
                RETURN t
                """
            )
            
            logger.info("成功创建测试节点")
        
        # 关闭连接
        driver.close()
        logger.info("Neo4j连接测试成功")
        return True
    except Exception as e:
        logger.error(f"Neo4j连接测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
