-- 为 avatars 表添加 private_profile 列
ALTER TABLE avatars ADD COLUMN IF NOT EXISTS private_profile JSON DEFAULT '{}';

-- 更新现有数据，设置默认值
UPDATE avatars SET private_profile = '{}' WHERE private_profile IS NULL;
