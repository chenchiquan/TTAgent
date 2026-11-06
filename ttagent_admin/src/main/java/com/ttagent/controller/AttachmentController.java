package com.ttagent.controller;

import com.ttagent.entity.Attachment;
import com.ttagent.service.AttachmentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 配件管理接口
 */
@RestController
@RequestMapping("/api/attachments")
public class AttachmentController {

    @Autowired
    private AttachmentService attachmentService;

    @GetMapping
    public List<Attachment> list() {
        return attachmentService.list();
    }

    @GetMapping("/{id}")
    public Attachment get(@PathVariable Long id) {
        return attachmentService.getById(id);
    }

    @PostMapping
    public boolean create(@RequestBody Attachment attachment) {
        return attachmentService.save(attachment);
    }

    @PutMapping
    public boolean update(@RequestBody Attachment attachment) {
        return attachmentService.updateById(attachment);
    }

    @DeleteMapping("/{id}")
    public boolean delete(@PathVariable Long id) {
        return attachmentService.removeById(id);
    }
}
