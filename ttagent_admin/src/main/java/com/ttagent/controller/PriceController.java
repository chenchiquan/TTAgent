package com.ttagent.controller;

import com.ttagent.entity.Price;
import com.ttagent.service.PriceService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 价格管理接口
 */
@RestController
@RequestMapping("/api/prices")
public class PriceController {

    @Autowired
    private PriceService priceService;

    @GetMapping
    public List<Price> list() {
        return priceService.list();
    }

    @GetMapping("/{id}")
    public Price get(@PathVariable Long id) {
        return priceService.getById(id);
    }

    @PostMapping
    public boolean create(@RequestBody Price price) {
        return priceService.save(price);
    }

    @PutMapping
    public boolean update(@RequestBody Price price) {
        return priceService.updateById(price);
    }

    @DeleteMapping("/{id}")
    public boolean delete(@PathVariable Long id) {
        return priceService.removeById(id);
    }
}
