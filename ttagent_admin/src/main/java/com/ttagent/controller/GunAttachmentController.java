package com.ttagent.controller;

import com.ttagent.entity.GunAttachment;
import com.ttagent.service.GunAttachmentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 枪-配件兼容关系管理接口
 */
@RestController
@RequestMapping("/api/gun-attachments")
public class GunAttachmentController {

    @Autowired
    private GunAttachmentService gunAttachmentService;

    @GetMapping
    public List<GunAttachment> list() {
        return gunAttachmentService.list();
    }

    @GetMapping("/{id}")
    public GunAttachment get(@PathVariable Long id) {
        return gunAttachmentService.getById(id);
    }

    @PostMapping
    public boolean create(@RequestBody GunAttachment gunAttachment) {
        return gunAttachmentService.save(gunAttachment);
    }

    @PutMapping
    public boolean update(@RequestBody GunAttachment gunAttachment) {
        return gunAttachmentService.updateById(gunAttachment);
    }

    @DeleteMapping("/{id}")
    public boolean delete(@PathVariable Long id) {
        return gunAttachmentService.removeById(id);
    }
}
