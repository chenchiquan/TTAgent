package com.ttagent.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ttagent.entity.Gun;
import com.ttagent.mapper.GunMapper;
import org.springframework.stereotype.Service;

/**
 * 枪械 Service（继承 ServiceImpl 自动拥有 CRUD 业务方法）
 */
@Service
public class GunService extends ServiceImpl<GunMapper, Gun> {
}
