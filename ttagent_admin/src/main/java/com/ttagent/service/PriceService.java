package com.ttagent.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ttagent.entity.Price;
import com.ttagent.mapper.PriceMapper;
import org.springframework.stereotype.Service;

/**
 * 价格 Service
 */
@Service
public class PriceService extends ServiceImpl<PriceMapper, Price> {
}
