package com.ttagent.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ttagent.entity.User;
import org.apache.ibatis.annotations.Mapper;

/**
 * 用户 Mapper（继承 BaseMapper 自动拥有 CRUD）
 */
@Mapper
public interface UserMapper extends BaseMapper<User> {
}
