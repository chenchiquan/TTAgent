-- ============================================================
-- 用户表（阶段1：用户登录）
-- 注意：MySQL 容器首次启动时已自动执行过 sql 目录下的脚本，
--       此表不会自动建。请在 Navicat 手动执行，或用 docker exec：
--       docker exec ttagent-mysql mysql -uttagent -pttagent123 ttagent -e "source /docker-entrypoint-initdb.d/user.sql"
--       （容器内 sql 目录已挂载，但仅首次启动执行；手动执行需进容器或在外部跑）
-- ============================================================
USE ttagent;

CREATE TABLE IF NOT EXISTS users (
  id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  username    VARCHAR(64)  NOT NULL COMMENT '用户名',
  password    VARCHAR(100) NOT NULL COMMENT 'BCrypt 加密后的密码',
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
