# question_generator.py
# 实现了一个问题生成器，用于根据视频内容生成学习问题。

from typing import List, Dict

class QuestionGenerator:
    # 初始化问题生成器
    def __init__(self):
        self.question_types = [
            "概念理解",
            "关键点提取",
            "应用实践",
            "知识扩展",
            "思维启发"
        ]
    
    # 根据视频内容生成学习问题
    def generate_questions(self, transcript: str) -> List[Dict]:
        # 这里应实现实际的LLM调用逻辑
        # 示例实现
        questions = []
        for i, qtype in enumerate(self.question_types, 1):
            questions.append(self._generate_question(qtype, i))
        return questions
    
    # 生成单个问题
    def _generate_question(self, question_type: str, qid: int) -> Dict:
        # 实际实现需要基于视频内容调用LLM
        questions = {
            "概念理解": "视频中介绍的核心概念是什么？",
            "关键点提取": "视频的主要观点有哪些？",
            "应用实践": "如何将视频中的知识应用到实际中？",
            "知识扩展": "与视频内容相关的延伸话题有哪些？",
            "思维启发": "视频内容给你带来了哪些思考？"
        }
        return {
            "id": qid,
            "type": question_type,
            "question": questions.get(question_type, "默认问题")
        }
    
    # 生成测试题:可以实现生成选择题、判断题等具体题型
    def generate_quiz(self, transcript: str) -> List[Dict]:
        pass