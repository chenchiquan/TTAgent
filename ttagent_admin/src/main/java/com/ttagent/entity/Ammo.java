package com.ttagent.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

/**
 * 弹药实体（对应 ammo 表）
 * 弹药无独立伤害（由枪械决定），只有口径、口径分类、穿透等级
 */
@Data
@TableName("ammo")
public class Ammo {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String code;
    private String name;
    private String caliber;
    private String caliberClass;
    private Integer penetration;

    private String version;
    private Integer isActive;

    @TableLogic
    private Integer isDeleted;
}
