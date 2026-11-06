-- ============================================================
-- TTAgent 数据库 schema
-- 目标：三角洲行动游戏助手的基础数据存储
-- 版本管理：每张业务表带 version + is_active + is_deleted，
--           新版本插新行、旧版 is_active=0，下线物品 is_deleted=1（软删除保留历史）
-- ============================================================

CREATE DATABASE IF NOT EXISTS ttagent
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
USE ttagent;

-- ------------------------------------------------------------
-- 1. guns 枪械表
--    存枪械基础数值与基础槽位；数值为绝对值，好坏由 type 解读
--    （如同样后坐力控制，步枪优于冲锋枪，靠 type 字段判断）
-- ------------------------------------------------------------
CREATE TABLE guns (
  id                BIGINT       NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  code              VARCHAR(64)  NOT NULL COMMENT '业务编码（如官方代号），版本更替时同 code 不同 version，用于对应同一把枪',
  name              VARCHAR(64)  NOT NULL COMMENT '枪械名称',
  type              VARCHAR(32)  NOT NULL COMMENT '枪械类型：步枪/冲锋枪/狙击枪/霰弹枪/轻机枪/手枪，用于解读数值好坏',
  caliber           VARCHAR(32)  DEFAULT NULL COMMENT '口径，用于关联 ammo.caliber',
  -- ===== 基础数值（绝对值） =====
  damage            INT  DEFAULT NULL COMMENT '伤害',
  fire_rate         INT  DEFAULT NULL COMMENT '射速（发/分）',
  effective_range   INT  DEFAULT NULL COMMENT '有效射程（米）',
  muzzle_velocity   INT  DEFAULT NULL COMMENT '初速（米/秒）',
  ergonomics        INT  DEFAULT NULL COMMENT '人机工效',
  vertical_recoil   INT  DEFAULT NULL COMMENT '垂直后坐力',
  horizontal_recoil INT  DEFAULT NULL COMMENT '水平后坐力',
  hipfire_accuracy  INT  DEFAULT NULL COMMENT '腰射精度/腰射值',
  ads_speed         INT  DEFAULT NULL COMMENT '开镜速度（毫秒，越小越快）',
  ads_move_speed    INT  DEFAULT NULL COMMENT '开镜状态下的移动速度',
  reload_time       INT  DEFAULT NULL COMMENT '换弹时间（毫秒）',
  magazine_size     INT  DEFAULT NULL COMMENT '弹匣容量（发）',
  weight            DECIMAL(6,3) DEFAULT NULL COMMENT '重量（千克）',
  -- ===== 槽位（JSON，因枪而异） =====
  base_slots        JSON DEFAULT NULL COMMENT '基础槽位列表，如 [{"slot":"muzzle","count":1},{"slot":"foregrip","count":1}]；count 表示该槽可装几个同类配件，0 表示该枪无此槽',
  -- ===== 版本与状态 =====
  version           VARCHAR(16)  NOT NULL DEFAULT 'v1' COMMENT '数据版本号，游戏版本更新时新建版本',
  is_active         TINYINT      NOT NULL DEFAULT 1 COMMENT '激活状态：1=当前版本有效，0=旧版已弃用但保留可查',
  is_deleted        TINYINT      NOT NULL DEFAULT 0 COMMENT '软删除：1=该物品已下线（短期存在后删除的走这里），0=正常；不物理删除以保留历史',
  created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_guns_code_version (code, version) COMMENT '同一把枪同一版本唯一',
  KEY idx_guns_type (type) COMMENT '按类型查询',
  KEY idx_guns_active (is_active, is_deleted) COMMENT '常用筛选：当前有效且未删除'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='枪械基础数据表';

-- ------------------------------------------------------------
-- 2. ammo 弹药表
--    按口径独立定价，与 guns.caliber 关联
-- ------------------------------------------------------------
CREATE TABLE ammo (
  id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  code          VARCHAR(64)  NOT NULL COMMENT '业务编码',
  name          VARCHAR(64)  NOT NULL COMMENT '弹药名称',
  caliber       VARCHAR(32)  NOT NULL COMMENT '口径，与 guns.caliber 关联',
  damage        INT  DEFAULT NULL COMMENT '伤害',
  penetration   INT  DEFAULT NULL COMMENT '穿透等级',
  version       VARCHAR(16)  NOT NULL DEFAULT 'v1' COMMENT '数据版本号',
  is_active     TINYINT      NOT NULL DEFAULT 1 COMMENT '激活状态：1当前 0旧版',
  is_deleted    TINYINT      NOT NULL DEFAULT 0 COMMENT '软删除：1已下线 0正常',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_ammo_code_version (code, version),
  KEY idx_ammo_caliber (caliber) COMMENT '按口径查询弹药',
  KEY idx_ammo_active (is_active, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='弹药数据表';

-- ------------------------------------------------------------
-- 3. attachments 配件表
--    存配件的数值加成与装上后解锁的额外槽位
--    "能装几个"不在此表，由 guns.base_slots / unlocked_slots 的 count 决定
-- ------------------------------------------------------------
CREATE TABLE attachments (
  id                       BIGINT       NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  code                     VARCHAR(64)  NOT NULL COMMENT '业务编码',
  name                     VARCHAR(64)  NOT NULL COMMENT '配件名称',
  category                 VARCHAR(32)  NOT NULL COMMENT '大类：枪口/瞄具/握把/弹匣/枪托/护木等',
  slot_type                VARCHAR(32)  NOT NULL COMMENT '该配件占用的槽位类型',
  -- ===== 数值加成（装配件就给属性，叠加到枪械基础数值上；负值=降低） =====
  damage_bonus             INT  DEFAULT 0 COMMENT '伤害加成',
  ergonomics_bonus         INT  DEFAULT 0 COMMENT '人机工效加成',
  vertical_recoil_bonus    INT  DEFAULT 0 COMMENT '垂直后坐力加成（负值=降低后坐力）',
  horizontal_recoil_bonus  INT  DEFAULT 0 COMMENT '水平后坐力加成（负值=降低）',
  hipfire_accuracy_bonus   INT  DEFAULT 0 COMMENT '腰射精度加成',
  ads_speed_bonus          INT  DEFAULT 0 COMMENT '开镜速度加成（负值=更快）',
  ads_move_speed_bonus     INT  DEFAULT 0 COMMENT '开镜移速加成',
  fire_rate_bonus          INT  DEFAULT 0 COMMENT '射速加成',
  effective_range_bonus    INT  DEFAULT 0 COMMENT '有效射程加成',
  -- ===== 装上后解锁的额外槽位 =====
  unlocked_slots           JSON DEFAULT NULL COMMENT '装上此配件后新增的槽位，如 [{"slot":"grip_side","count":2}]；count 表示新增几个该类槽',
  -- ===== 版本与状态 =====
  version                  VARCHAR(16)  NOT NULL DEFAULT 'v1' COMMENT '数据版本号',
  is_active                TINYINT      NOT NULL DEFAULT 1 COMMENT '激活状态：1当前 0旧版',
  is_deleted               TINYINT      NOT NULL DEFAULT 0 COMMENT '软删除：1已下线 0正常',
  created_at               DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at               DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_att_code_version (code, version),
  KEY idx_att_category (category) COMMENT '按大类查询配件',
  KEY idx_att_active (is_active, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配件数据表';

-- ------------------------------------------------------------
-- 4. gun_attachments 枪-配件兼容关系表（多对多）
--    表达"某把枪能装某个配件到某个槽"；实际装配方案不在本表，由改枪推荐逻辑生成
-- ------------------------------------------------------------
CREATE TABLE gun_attachments (
  id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  gun_id        BIGINT       NOT NULL COMMENT '枪械 id，关联 guns.id',
  attachment_id BIGINT       NOT NULL COMMENT '配件 id，关联 attachments.id',
  slot          VARCHAR(32)  NOT NULL COMMENT '装到哪个槽位（对应 guns.base_slots 的 slot 名）',
  is_active     TINYINT      NOT NULL DEFAULT 1 COMMENT '兼容关系是否当前有效（随版本可能变化）',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_gun_att_slot (gun_id, attachment_id, slot) COMMENT '同一枪同一配件同一槽唯一',
  KEY idx_ga_gun (gun_id) COMMENT '查某枪能装哪些配件',
  KEY idx_ga_att (attachment_id) COMMENT '查某配件能装哪些枪'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='枪-配件兼容关系表';

-- ------------------------------------------------------------
-- 5. prices 统一价格表
--    所有物品（枪/配件/弹药/后期护甲等）价格统一挂这里
--    当前价模式：每个物品一条，定时任务 UPDATE 覆盖；要历史趋势时再加 recorded_at 改多条
-- ------------------------------------------------------------
CREATE TABLE prices (
  id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  item_type     VARCHAR(16)  NOT NULL COMMENT '物品类型：gun/attachment/ammo/armor 等，方便后期扩展不改表',
  item_id       BIGINT       NOT NULL COMMENT '物品 id，对应各业务表 id',
  price         DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '当前价格，定时任务同步时 UPDATE 覆盖',
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '价格最后更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_price_item (item_type, item_id) COMMENT '每个物品只保留一条当前价'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='统一价格表';
