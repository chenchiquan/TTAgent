-- ============================================================
-- TTAgent 初始测试数据
-- 内容：SCAR突击步枪 + 7.62×51弹药 + 5个配件 + 兼容关系 + 价格
-- 数值体系：据枪=ergonomics，操控速度(默认)=ads_speed+ads_move_speed，后坐力(默认)=垂直+水平
-- bonus 存原始加成值（正负与游戏面板一致），最终效果由应用层按数值方向计算
-- 说明：部分数值/价格为测试占位值，后期按实际数据调整
-- ============================================================

SET NAMES utf8mb4;
USE ttagent;

-- ===== 1. 枪械 SCAR =====
INSERT INTO guns (code, name, type, caliber, flesh_damage, armor_damage, fire_rate, effective_range, muzzle_velocity, ergonomics, vertical_recoil, horizontal_recoil, hipfire_accuracy, ads_speed, ads_move_speed, reload_time, magazine_size, weight, base_slots, remark)
VALUES (
  'scar-h', 'SCAR突击步枪', '步枪', '7.62×51',
  40, 42, 600, 80, 800, 60, 52, 35, 77, 300, 50, 3000, 20, 3.500,
  '[{"slot":"muzzle","count":1},{"slot":"foregrip","count":1},{"slot":"rear_grip","count":1},{"slot":"magazine","count":1},{"slot":"stock","count":1},{"slot":"optic","count":1},{"slot":"laser","count":2}]',
  '测试数据：SCAR突击步枪，7.62×51口径，基础槽位含2个镭射'
);

-- ===== 2. 弹药 7.62×51（大口径，伤害由枪械决定，弹药只有等级）=====
INSERT INTO ammo (code, name, caliber, caliber_class, penetration)
VALUES ('ammo_762x51', '7.62×51弹药', '7.62×51', '大口径', 3);

-- ===== 3. 配件 5 个 =====
-- 普通枪托：+2后坐力（无特殊说明→垂直+水平各+2）
INSERT INTO attachments (code, name, category, slot_type, vertical_recoil_bonus, horizontal_recoil_bonus)
VALUES ('stock_normal', '普通枪托', '枪托', 'stock', 2, 2);

-- UR战术枪托：+8后座(垂直+水平各+8) +8据枪(人机工效+8) -8操控速度(开镜速度-8 + 开镜移速-8)
INSERT INTO attachments (code, name, category, slot_type, vertical_recoil_bonus, horizontal_recoil_bonus, ergonomics_bonus, ads_speed_bonus, ads_move_speed_bonus)
VALUES ('stock_ur_tactical', 'UR战术枪托', '枪托', 'stock', 8, 8, 8, -8, -8);

-- 垂直握把：+2后坐力（垂直+水平各+2）
INSERT INTO attachments (code, name, category, slot_type, vertical_recoil_bonus, horizontal_recoil_bonus)
VALUES ('grip_vertical', '垂直握把', '握把', 'foregrip', 2, 2);

-- 钢制炸膛枪口：+6后座(垂直+水平各+6) -2据枪(人机工效-2)
INSERT INTO attachments (code, name, category, slot_type, vertical_recoil_bonus, horizontal_recoil_bonus, ergonomics_bonus)
VALUES ('muzzle_steel_compensator', '钢制炸膛枪口', '枪口', 'muzzle', 6, 6, -2);

-- 战术后握把：+2后坐力控制（垂直+水平各+2）
INSERT INTO attachments (code, name, category, slot_type, vertical_recoil_bonus, horizontal_recoil_bonus)
VALUES ('grip_tactical_rear', '战术后握把', '握把', 'rear_grip', 2, 2);

-- ===== 4. 枪-配件兼容关系（SCAR 支持 5 配件）=====
INSERT INTO gun_attachments (gun_id, attachment_id, slot) VALUES
((SELECT id FROM guns WHERE code='scar-h' AND version='v1'), (SELECT id FROM attachments WHERE code='stock_normal' AND version='v1'), 'stock'),
((SELECT id FROM guns WHERE code='scar-h' AND version='v1'), (SELECT id FROM attachments WHERE code='stock_ur_tactical' AND version='v1'), 'stock'),
((SELECT id FROM guns WHERE code='scar-h' AND version='v1'), (SELECT id FROM attachments WHERE code='grip_vertical' AND version='v1'), 'foregrip'),
((SELECT id FROM guns WHERE code='scar-h' AND version='v1'), (SELECT id FROM attachments WHERE code='muzzle_steel_compensator' AND version='v1'), 'muzzle'),
((SELECT id FROM guns WHERE code='scar-h' AND version='v1'), (SELECT id FROM attachments WHERE code='grip_tactical_rear' AND version='v1'), 'rear_grip');

-- ===== 5. 价格（枪/弹药/配件各自挂价）=====
INSERT INTO prices (item_type, item_id, price) VALUES
('gun',        (SELECT id FROM guns        WHERE code='scar-h'                  AND version='v1'), 112500),
('ammo',       (SELECT id FROM ammo        WHERE code='ammo_762x51'             AND version='v1'), 500),
('attachment', (SELECT id FROM attachments WHERE code='stock_normal'            AND version='v1'), 3000),
('attachment', (SELECT id FROM attachments WHERE code='stock_ur_tactical'       AND version='v1'), 50000),
('attachment', (SELECT id FROM attachments WHERE code='grip_vertical'           AND version='v1'), 5000),
('attachment', (SELECT id FROM attachments WHERE code='muzzle_steel_compensator' AND version='v1'), 8000),
('attachment', (SELECT id FROM attachments WHERE code='grip_tactical_rear'      AND version='v1'), 4000);
