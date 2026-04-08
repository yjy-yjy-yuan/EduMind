-- 语义搜索全局检索日志表（跨 video_ids 为空时的检索）
-- 执行示例：mysql -u root -p edumind < backend_fastapi/migrations/add_semantic_search_logs.sql

CREATE TABLE IF NOT EXISTS semantic_search_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    query_text VARCHAR(500) NOT NULL,
    is_global TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=跨视频全局检索（请求未带 video_ids）',
    video_ids_searched JSON NULL COMMENT '本次实际参与检索的视频 ID 列表',
    result_count INT NOT NULL DEFAULT 0,
    total_time_ms INT NOT NULL DEFAULT 0,
    limit_used INT NOT NULL,
    threshold_used DECIMAL(4, 3) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_semantic_log_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
