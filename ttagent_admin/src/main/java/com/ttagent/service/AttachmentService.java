package com.ttagent.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ttagent.entity.Attachment;
import com.ttagent.mapper.AttachmentMapper;
import org.springframework.stereotype.Service;

/**
 * 配件 Service
 */
@Service
public class AttachmentService extends ServiceImpl<AttachmentMapper, Attachment> {
}
