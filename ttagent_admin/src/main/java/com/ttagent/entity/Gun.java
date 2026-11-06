package com.ttagent.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.math.BigDecimal;

/**
 * 枪械实体（对应 guns 表）
 */
@Data
@TableName("guns")
public class Gun {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String code;
    private String name;
    private String type;
    private String caliber;

    // ===== 基础数值 =====
    private Integer fleshDamage;
    private Integer armorDamage;
    private Integer fireRate;
    private Integer effectiveRange;
    private Integer muzzleVelocity;
    private Integer ergonomics;
    private Integer verticalRecoil;
    private Integer horizontalRecoil;
    private Integer hipfireAccuracy;
    private Integer adsSpeed;
    private Integer adsMoveSpeed;
    private Integer reloadTime;
    private Integer magazineSize;
    private BigDecimal weight;

    // ===== 槽位与说明 =====
    private String baseSlots;   // JSON 字符串
    private String remark;

    // ===== 版本与状态 =====
    private String version;
    private Integer isActive;

    @TableLogic
    private Integer isDeleted;  // 软删除自动处理
}
