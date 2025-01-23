# note_system.py
# 实现了一个现代化的笔记系统，用于记录视频学习笔记

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Set
import json
import os
import emoji
from enum import Enum

class NoteImportance(Enum):
    LOW = "💡"      # 普通笔记
    MEDIUM = "⭐"   # 重要笔记
    HIGH = "🌟"     # 非常重要
    CRITICAL = "🔥"  # 关键笔记

class NoteMood(Enum):
    HAPPY = "😊"     # 理解很好
    NEUTRAL = "😐"   # 一般理解
    CONFUSED = "😕"  # 有点困惑
    DIFFICULT = "😫" # 很难理解

class NoteTemplate(Enum):
    CONCEPT = "概念模板"
    QUESTION = "问题模板"
    SUMMARY = "总结模板"
    REVIEW = "复习模板"

class Note:
    def __init__(
        self,
        text: str,
        timestamp: float,
        timestamp_str: Optional[str] = None,
        importance: NoteImportance = NoteImportance.LOW,
        mood: NoteMood = NoteMood.NEUTRAL,
        tags: Set[str] = None,
        template_type: Optional[NoteTemplate] = None,
        related_notes: List[int] = None
    ):
        self.id = datetime.now().timestamp()
        self.text = text.strip()
        self.timestamp = timestamp
        self.timestamp_str = timestamp_str or str(timedelta(seconds=int(timestamp)))
        self.importance = importance
        self.mood = mood
        self.tags = tags or set()
        self.template_type = template_type
        self.related_notes = related_notes or []
        self.created_at = datetime.now()
        self.last_reviewed = None
        self.review_count = 0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text,
            "timestamp": self.timestamp,
            "timestamp_str": self.timestamp_str,
            "importance": self.importance.name,
            "mood": self.mood.name,
            "tags": list(self.tags),
            "template_type": self.template_type.name if self.template_type else None,
            "related_notes": self.related_notes,
            "created_at": self.created_at.isoformat(),
            "last_reviewed": self.last_reviewed.isoformat() if self.last_reviewed else None,
            "review_count": self.review_count
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Note':
        note = cls(
            text=data["text"],
            timestamp=data["timestamp"],
            timestamp_str=data["timestamp_str"],
            importance=NoteImportance[data["importance"]],
            mood=NoteMood[data["mood"]],
            tags=set(data["tags"]),
            template_type=NoteTemplate[data["template_type"]] if data["template_type"] else None,
            related_notes=data["related_notes"]
        )
        note.id = data["id"]
        note.created_at = datetime.fromisoformat(data["created_at"])
        note.last_reviewed = datetime.fromisoformat(data["last_reviewed"]) if data["last_reviewed"] else None
        note.review_count = data["review_count"]
        return note

class NoteSystem:
    def __init__(self):
        self.notes: List[Note] = []
        self.templates: Dict[NoteTemplate, str] = {
            NoteTemplate.CONCEPT: "概念名称：\n定义：\n关键点：\n例子：\n",
            NoteTemplate.QUESTION: "问题：\n思考：\n答案：\n相关概念：\n",
            NoteTemplate.SUMMARY: "主要内容：\n重点总结：\n疑问：\n后续学习：\n",
            NoteTemplate.REVIEW: "知识点回顾：\n掌握程度：\n需要加强：\n"
        }
        
    def add_note(
        self,
        text: str,
        timestamp: float,
        timestamp_str: Optional[str] = None,
        importance: NoteImportance = NoteImportance.LOW,
        mood: NoteMood = NoteMood.NEUTRAL,
        tags: Set[str] = None,
        template_type: Optional[NoteTemplate] = None,
        related_notes: List[int] = None
    ) -> bool:
        """添加新笔记"""
        if not text.strip():
            return False
            
        note = Note(
            text=text,
            timestamp=timestamp,
            timestamp_str=timestamp_str,
            importance=importance,
            mood=mood,
            tags=tags,
            template_type=template_type,
            related_notes=related_notes
        )
        self.notes.append(note)
        self.notes.sort(key=lambda x: x.timestamp)
        return True

    def get_notes(self, 
                 importance: Optional[NoteImportance] = None,
                 mood: Optional[NoteMood] = None,
                 tags: Optional[Set[str]] = None,
                 template_type: Optional[NoteTemplate] = None) -> List[Note]:
        """获取笔记，支持多种过滤条件"""
        filtered_notes = self.notes
        
        if importance:
            filtered_notes = [n for n in filtered_notes if n.importance == importance]
        if mood:
            filtered_notes = [n for n in filtered_notes if n.mood == mood]
        if tags:
            filtered_notes = [n for n in filtered_notes if tags & n.tags]
        if template_type:
            filtered_notes = [n for n in filtered_notes if n.template_type == template_type]
            
        return filtered_notes

    def get_note_by_id(self, note_id: int) -> Optional[Note]:
        """通过ID获取笔记"""
        for note in self.notes:
            if note.id == note_id:
                return note
        return None

    def edit_note(
        self,
        note_id: int,
        new_text: Optional[str] = None,
        new_timestamp: Optional[float] = None,
        new_importance: Optional[NoteImportance] = None,
        new_mood: Optional[NoteMood] = None,
        new_tags: Optional[Set[str]] = None
    ) -> bool:
        """编辑笔记"""
        note = self.get_note_by_id(note_id)
        if not note:
            return False
            
        if new_text is not None:
            note.text = new_text.strip()
        if new_timestamp is not None:
            note.timestamp = new_timestamp
            note.timestamp_str = str(timedelta(seconds=int(new_timestamp)))
        if new_importance is not None:
            note.importance = new_importance
        if new_mood is not None:
            note.mood = new_mood
        if new_tags is not None:
            note.tags = new_tags
            
        return True

    def delete_note(self, note_id: int) -> bool:
        """删除笔记"""
        for i, note in enumerate(self.notes):
            if note.id == note_id:
                self.notes.pop(i)
                # 删除其他笔记中对该笔记的引用
                for other_note in self.notes:
                    if note_id in other_note.related_notes:
                        other_note.related_notes.remove(note_id)
                return True
        return False

    def add_related_notes(self, note_id: int, related_note_ids: List[int]) -> bool:
        """添加相关笔记链接"""
        note = self.get_note_by_id(note_id)
        if not note:
            return False
            
        for related_id in related_note_ids:
            if related_id not in note.related_notes and self.get_note_by_id(related_id):
                note.related_notes.append(related_id)
        return True

    def get_template(self, template_type: NoteTemplate) -> str:
        """获取笔记模板"""
        return self.templates.get(template_type, "")

    def mark_note_reviewed(self, note_id: int) -> bool:
        """标记笔记已复习"""
        note = self.get_note_by_id(note_id)
        if not note:
            return False
            
        note.last_reviewed = datetime.now()
        note.review_count += 1
        return True

    def get_notes_for_review(self, days_threshold: int = 7) -> List[Note]:
        """获取需要复习的笔记"""
        review_threshold = datetime.now() - timedelta(days=days_threshold)
        return [
            note for note in self.notes
            if note.last_reviewed is None or note.last_reviewed < review_threshold
        ]

    def get_learning_progress(self) -> Dict:
        """获取学习进度统计"""
        total_notes = len(self.notes)
        if not total_notes:
            return {
                "total_notes": 0,
                "importance_distribution": {},
                "mood_distribution": {},
                "review_status": {"reviewed": 0, "not_reviewed": 0},
                "tags_distribution": {}
            }

        importance_dist = {imp: 0 for imp in NoteImportance}
        mood_dist = {mood: 0 for mood in NoteMood}
        tags_dist = {}
        reviewed = 0

        for note in self.notes:
            importance_dist[note.importance] += 1
            mood_dist[note.mood] += 1
            if note.last_reviewed:
                reviewed += 1
            for tag in note.tags:
                tags_dist[tag] = tags_dist.get(tag, 0) + 1

        return {
            "total_notes": total_notes,
            "importance_distribution": {k.name: v/total_notes for k, v in importance_dist.items()},
            "mood_distribution": {k.name: v/total_notes for k, v in mood_dist.items()},
            "review_status": {
                "reviewed": reviewed/total_notes,
                "not_reviewed": (total_notes-reviewed)/total_notes
            },
            "tags_distribution": {k: v/total_notes for k, v in tags_dist.items()}
        }

    def save_notes(self, filepath: str) -> bool:
        """保存笔记到文件"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                notes_data = [note.to_dict() for note in self.notes]
                json.dump(notes_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving notes: {e}")
            return False

    def load_notes(self, filepath: str) -> bool:
        """从文件加载笔记"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                notes_data = json.load(f)
                self.notes = [Note.from_dict(data) for data in notes_data]
                self.notes.sort(key=lambda x: x.timestamp)
            return True
        except FileNotFoundError:
            self.notes = []
            return False
        except Exception as e:
            print(f"Error loading notes: {e}")
            return False

    def export_notes(self, filepath: str, format_type: str = 'txt') -> bool:
        """导出笔记"""
        try:
            if format_type == 'txt':
                with open(filepath, 'w', encoding='utf-8') as f:
                    for note in self.notes:
                        f.write(f"时间: [{note.timestamp_str}]\n")
                        f.write(f"重要性: {note.importance.value}\n")
                        f.write(f"心情: {note.mood.value}\n")
                        if note.tags:
                            f.write(f"标签: {', '.join(note.tags)}\n")
                        if note.template_type:
                            f.write(f"模板类型: {note.template_type.value}\n")
                        f.write(f"内容:\n{note.text}\n")
                        if note.related_notes:
                            related_texts = []
                            for rel_id in note.related_notes:
                                rel_note = self.get_note_by_id(rel_id)
                                if rel_note:
                                    related_texts.append(f"[{rel_note.timestamp_str}] {rel_note.text[:30]}...")
                            f.write(f"相关笔记:\n" + "\n".join(related_texts) + "\n")
                        f.write("\n" + "="*50 + "\n\n")
            elif format_type == 'json':
                return self.save_notes(filepath)
            return True
        except Exception as e:
            print(f"Error exporting notes: {e}")
            return False