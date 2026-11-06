package com.ttagent.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

/**
 * 配件实体（对应 attachments 表）
 * bonus 存原始加成值（正负与游戏面板一致），最终效果由应用层计算
 */
@Data
@TableName("attachments")
public class Attachment {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String code;
    private String name;
    private String category;
    private String slotType;

    // ===== 数值加成 =====
    private Integer fleshDamageBonus;
    private Integer armorDamageBonus;
    private Integer ergonomicsBonus;
    private Integer verticalRecoilBonus;
    private Integer horizontalRecoilBonus;
    private Integer hipfireAccuracyBonus;
    private Integer adsSpeedBonus;
    private Integer adsMoveSpeedBonus;
    private Integer fireRateBonus;
    private Integer effectiveRangeBonus;

    // ===== 解锁额外槽位 =====
    private String unlockedSlots;   // JSON 字符串

    private String version;
    private Integer isActive;

    @TableLogic
    private Integer isDeleted;
}
