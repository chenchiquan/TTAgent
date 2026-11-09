package com.ttagent.config;

import com.ttagent.interceptor.JwtInterceptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 注册 JWT 拦截器。
 * 阶段1仅拦截 /api/chat（对话需要 userId 给记忆体系用）；
 * /api/auth/** 放行（登录注册本身不需要 token）；
 * admin/数据接口暂不拦截（admin 后台尚未有登录入口，避免 401 坏掉），后续统一加登录时再扩大范围。
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Autowired
    private JwtInterceptor jwtInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(jwtInterceptor)
                .addPathPatterns("/api/chat")
                .excludePathPatterns("/api/auth/**");
    }
}
