package com.ttagent;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * TTAgent 管理后端启动类
 * @MapperScan 显式扫描 Mapper 接口包，确保 MyBatis-Plus 注入
 */
@SpringBootApplication
@MapperScan("com.ttagent.mapper")
public class TtagentAdminApplication {

    public static void main(String[] args) {
        SpringApplication.run(TtagentAdminApplication.class, args);
    }
}
