package com.ttagent.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

/**
 * 枪-配件兼容关系实体（对应 gun_attachments 表）
 * 表达"某把枪能装某个配件到某个槽"
 * 该表无 is_deleted 字段，物理删除
 */
@Data
@TableName("gun_attachments")
public class GunAttachment {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long gunId;
    private Long attachmentId;
    private String slot;
    private Integer isActive;
}
