package com.ttagent.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ttagent.entity.GunAttachment;
import com.ttagent.mapper.GunAttachmentMapper;
import org.springframework.stereotype.Service;

/**
 * 枪-配件兼容关系 Service
 */
@Service
public class GunAttachmentService extends ServiceImpl<GunAttachmentMapper, GunAttachment> {
}
