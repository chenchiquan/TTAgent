package com.ttagent.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.math.BigDecimal;

/**
 * 统一价格实体（对应 prices 表）
 * 所有物品价格挂这里，按 item_type + item_id 区分
 * 该表无 is_deleted 字段，物理删除（价格通常 update 覆盖）
 */
@Data
@TableName("prices")
public class Price {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String itemType;   // gun/attachment/ammo/armor 等
    private Long itemId;
    private BigDecimal price;
}
