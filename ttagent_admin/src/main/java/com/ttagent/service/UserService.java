package com.ttagent.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ttagent.entity.User;
import com.ttagent.mapper.UserMapper;
import org.springframework.stereotype.Service;

/**
 * 用户 Service（继承 ServiceImpl 自动拥有 CRUD）
 */
@Service
public class UserService extends ServiceImpl<UserMapper, User> {
}
