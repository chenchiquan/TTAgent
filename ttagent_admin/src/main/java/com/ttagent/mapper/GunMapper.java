package com.ttagent.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ttagent.entity.Gun;
import org.apache.ibatis.annotations.Mapper;

/**
 * 枪械 Mapper（继承 BaseMapper 自动拥有 CRUD，零 SQL）
 */
@Mapper
public interface GunMapper extends BaseMapper<Gun> {
}
