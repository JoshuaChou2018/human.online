-- 添加 max_steps 列到 simulations 表
ALTER TABLE simulations ADD COLUMN IF NOT EXISTS max_steps INTEGER DEFAULT 10;

-- 更新现有记录
UPDATE simulations SET max_steps = 10 WHERE max_steps IS NULL;
