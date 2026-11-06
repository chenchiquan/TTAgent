package com.ttagent.controller;

import com.ttagent.entity.Ammo;
import com.ttagent.service.AmmoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 弹药管理接口
 */
@RestController
@RequestMapping("/api/ammo")
public class AmmoController {

    @Autowired
    private AmmoService ammoService;

    @GetMapping
    public List<Ammo> list() {
        return ammoService.list();
    }

    @GetMapping("/{id}")
    public Ammo get(@PathVariable Long id) {
        return ammoService.getById(id);
    }

    @PostMapping
    public boolean create(@RequestBody Ammo ammo) {
        return ammoService.save(ammo);
    }

    @PutMapping
    public boolean update(@RequestBody Ammo ammo) {
        return ammoService.updateById(ammo);
    }

    @DeleteMapping("/{id}")
    public boolean delete(@PathVariable Long id) {
        return ammoService.removeById(id);
    }
}
