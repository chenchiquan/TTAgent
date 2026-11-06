package com.ttagent.controller;

import com.ttagent.entity.Gun;
import com.ttagent.service.GunService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 枪械管理接口
 * GET    /api/guns        列表
 * GET    /api/guns/{id}   详情
 * POST   /api/guns        新增
 * PUT    /api/guns        修改
 * DELETE /api/guns/{id}   删除（软删除 is_deleted=1）
 */
@RestController
@RequestMapping("/api/guns")
public class GunController {

    @Autowired
    private GunService gunService;

    @GetMapping
    public List<Gun> list() {
        return gunService.list();
    }

    @GetMapping("/{id}")
    public Gun get(@PathVariable Long id) {
        return gunService.getById(id);
    }

    @PostMapping
    public boolean create(@RequestBody Gun gun) {
        return gunService.save(gun);
    }

    @PutMapping
    public boolean update(@RequestBody Gun gun) {
        return gunService.updateById(gun);
    }

    @DeleteMapping("/{id}")
    public boolean delete(@PathVariable Long id) {
        return gunService.removeById(id);
    }
}
