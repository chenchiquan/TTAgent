package com.ttagent.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ttagent.entity.Ammo;
import com.ttagent.mapper.AmmoMapper;
import org.springframework.stereotype.Service;

/**
 * 弹药 Service
 */
@Service
public class AmmoService extends ServiceImpl<AmmoMapper, Ammo> {
}
