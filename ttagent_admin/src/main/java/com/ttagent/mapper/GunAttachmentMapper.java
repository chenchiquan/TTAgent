package com.ttagent.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ttagent.entity.GunAttachment;
import org.apache.ibatis.annotations.Mapper;

/**
 * 枪-配件兼容关系 Mapper（继承 BaseMapper 自动拥有 CRUD）
 */
@Mapper
public interface GunAttachmentMapper extends BaseMapper<GunAttachment> {
}
